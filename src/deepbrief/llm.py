from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepbrief.config import Config


TEXT_ONLY_STAGES = {"rank", "signal_extract", "tuner", "judge"}
REPO_READ_TOOLS = ["Read", "Grep", "Glob", "Bash"]
MUTATING_OR_NETWORK_TOOLS = [
    "Write",
    "Edit",
    "NotebookEdit",
    "WebFetch",
    "WebSearch",
    "Task",
    "Agent",
    "TodoWrite",
    "BashOutput",
    "KillBash",
    "ExitPlanMode",
    "ListMcpResources",
    "ReadMcpResource",
]
READ_ONLY_BASH_PREFIXES = (
    "git log",
    "git diff",
    "git show",
    "git grep",
    "rg",
    "grep",
    "sed -n",
    "awk",
    "head",
    "tail",
    "find",
    "ls",
    "cat",
    "wc",
    "pwd",
)
SHELL_CONTROL_CHARS = re.compile(r"[;&|`<>$]")
HOOK_AUDIT_EVENTS: list[dict[str, Any]] = []


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class StageResult:
    stage: str
    success: bool
    text: str = ""
    structured: Any = None
    cost_usd: float = 0.0
    model_usage: dict[str, Any] = field(default_factory=dict)
    subtype: str = "success"
    error: str | None = None


@dataclass
class BudgetTracker:
    cap_usd: float
    spent_usd: float = 0.0

    def reserve(self, stage: str, stage_cap: float) -> None:
        if self.spent_usd >= self.cap_usd:
            raise BudgetExceeded(f"run budget exhausted before {stage}: {self.spent_usd:.4f} >= {self.cap_usd:.4f}")
        if stage_cap <= 0:
            raise BudgetExceeded(f"stage budget must be positive for {stage}")

    def record(self, stage: str, cost_usd: float) -> None:
        next_total = self.spent_usd + max(cost_usd, 0.0)
        if next_total > self.cap_usd:
            raise BudgetExceeded(
                f"run budget exceeded after {stage}: {next_total:.4f} > {self.cap_usd:.4f}"
            )
        self.spent_usd = next_total


async def run_text_stage(
    config: Config,
    *,
    stage: str,
    prompt: str,
    system_prompt_path: Path,
    tier: str = "fast",
    output_schema: dict[str, Any] | None = None,
    budget: BudgetTracker | None = None,
    dry_run: bool = False,
) -> StageResult:
    if stage not in TEXT_ONLY_STAGES and stage not in {"skim", "deepdive_article", "librarian"}:
        raise ValueError(f"unexpected text stage: {stage}")
    return await _run_stage(
        config,
        stage=stage,
        prompt=prompt,
        system_prompt_path=system_prompt_path,
        tier=tier,
        cwd=None,
        allowed_tools=[],
        disallowed_tools=[],
        output_schema=output_schema,
        budget=budget,
        dry_run=dry_run,
    )


async def run_repo_stage(
    config: Config,
    *,
    stage: str,
    prompt: str,
    system_prompt_path: Path,
    cwd: Path,
    tier: str = "deep",
    output_schema: dict[str, Any] | None = None,
    budget: BudgetTracker | None = None,
    dry_run: bool = False,
) -> StageResult:
    if stage != "code_analyst":
        raise ValueError("run_repo_stage is reserved for code_analyst")
    return await _run_stage(
        config,
        stage=stage,
        prompt=prompt,
        system_prompt_path=system_prompt_path,
        tier=tier,
        cwd=cwd,
        allowed_tools=REPO_READ_TOOLS,
        disallowed_tools=MUTATING_OR_NETWORK_TOOLS,
        output_schema=output_schema,
        budget=budget,
        dry_run=dry_run,
    )


async def _run_stage(
    config: Config,
    *,
    stage: str,
    prompt: str,
    system_prompt_path: Path,
    tier: str,
    cwd: Path | None,
    allowed_tools: list[str],
    disallowed_tools: list[str],
    output_schema: dict[str, Any] | None,
    budget: BudgetTracker | None,
    dry_run: bool,
) -> StageResult:
    stage_cap = config.stage_budget(stage)
    if budget:
        budget.reserve(stage, stage_cap)
    if dry_run:
        result = StageResult(stage=stage, success=True, text=f"dry-run {stage}", cost_usd=0.0)
        if budget:
            budget.record(stage, result.cost_usd)
        return result

    try:
        from claude_agent_sdk import ResultMessage, query
    except ImportError as exc:
        raise RuntimeError("claude-agent-sdk is not installed; run uv sync before live LLM gates") from exc

    options = build_agent_options(
        config=config,
        stage=stage,
        system_prompt_path=system_prompt_path,
        tier=tier,
        cwd=cwd,
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools,
        output_schema=output_schema,
        stage_cap=stage_cap,
    )
    final: ResultMessage | None = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            final = message
    if final is None:
        raise RuntimeError(f"{stage} returned no ResultMessage")

    cost = float(final.total_cost_usd or 0.0)
    if budget:
        budget.record(stage, cost)

    if final.subtype == "error_max_budget_usd":
        return StageResult(
            stage=stage,
            success=False,
            cost_usd=cost,
            model_usage=final.model_usage or {},
            subtype=final.subtype,
            error="stage budget exhausted",
        )
    return StageResult(
        stage=stage,
        success=not final.is_error and final.subtype == "success",
        text=final.result or "",
        structured=final.structured_output,
        cost_usd=cost,
        model_usage=final.model_usage or {},
        subtype=final.subtype,
        error=(final.result if final.is_error else None),
    )


def build_agent_options(
    *,
    config: Config,
    stage: str,
    system_prompt_path: Path,
    tier: str,
    cwd: Path | None,
    allowed_tools: list[str],
    disallowed_tools: list[str],
    output_schema: dict[str, Any] | None,
    stage_cap: float,
) -> Any:
    try:
        from claude_agent_sdk import ClaudeAgentOptions, HookMatcher
    except ImportError as exc:
        raise RuntimeError("claude-agent-sdk is not installed; cannot build live agent options") from exc

    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    output_format = {"type": "json_schema", "schema": output_schema} if output_schema else None
    hooks = None
    if stage == "code_analyst":
        hooks = {"PreToolUse": [HookMatcher(matcher="Bash", hooks=[readonly_bash_hook])]}
    return ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools,
        permission_mode="dontAsk",
        cwd=cwd,
        model=config.model_for_tier(tier),
        max_budget_usd=stage_cap,
        output_format=output_format,
        hooks=hooks,
        setting_sources=[],
    )


async def readonly_bash_hook(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    command = str(input_data.get("tool_input", {}).get("command", ""))
    if is_readonly_bash_command(command):
        HOOK_AUDIT_EVENTS.append({"tool": "Bash", "command": command, "decision": "allow"})
        return {
            "hookSpecificOutput": {
                "hookEventName": input_data["hook_event_name"],
                "permissionDecision": "allow",
                "permissionDecisionReason": "read-only repository inspection command",
            }
        }
    HOOK_AUDIT_EVENTS.append({"tool": "Bash", "command": command, "decision": "deny"})
    return {
        "hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "permissionDecision": "deny",
            "permissionDecisionReason": "Bash command is outside DeepBrief's read-only allowlist",
        }
    }


def clear_hook_audit() -> None:
    HOOK_AUDIT_EVENTS.clear()


def hook_audit_events() -> list[dict[str, Any]]:
    return list(HOOK_AUDIT_EVENTS)


def is_readonly_bash_command(command: str) -> bool:
    command = " ".join(command.strip().split())
    if not command:
        return False
    if SHELL_CONTROL_CHARS.search(command):
        return False
    return any(command == prefix or command.startswith(prefix + " ") for prefix in READ_ONLY_BASH_PREFIXES)


def code_lockdown_summary() -> dict[str, Any]:
    return {
        "permission_mode": "dontAsk",
        "allowed_tools": list(REPO_READ_TOOLS),
        "disallowed_tools": list(MUTATING_OR_NETWORK_TOOLS),
        "bash_hook": "PreToolUse",
        "settings_sources": [],
    }


async def self_test(config: Config) -> list[str]:
    tracker = BudgetTracker(cap_usd=0.01)
    await run_text_stage(
        config,
        stage="rank",
        prompt="Return ok.",
        system_prompt_path=config.prompts_dir / "rank.md",
        budget=tracker,
        dry_run=True,
    )
    locked = code_lockdown_summary()
    required_denies = {"Write", "Edit", "NotebookEdit", "WebFetch", "WebSearch", "Task"}
    if locked["permission_mode"] != "dontAsk":
        raise RuntimeError("code analyst permission mode is not dontAsk")
    if not required_denies.issubset(set(locked["disallowed_tools"])):
        raise RuntimeError("code analyst deny list is missing required mutating/network tools")
    if not is_readonly_bash_command("git show HEAD"):
        raise RuntimeError("read-only bash hook rejected git show")
    if is_readonly_bash_command("git status && touch x"):
        raise RuntimeError("read-only bash hook allowed shell control operators")
    return [
        "budget wrapper dry-run recorded cost 0.0000",
        "code analyst permission_mode=dontAsk",
        "code analyst mutating/network tools denied",
        "bash PreToolUse allowlist enforced",
    ]
