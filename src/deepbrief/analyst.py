from __future__ import annotations

import asyncio
import html
import json
import re
import subprocess
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

from deepbrief.config import Config
from deepbrief.db import ensure_run, init_database, log_spend
from deepbrief.llm import (
    BudgetTracker,
    clear_hook_audit,
    hook_audit_events,
    readonly_bash_hook,
    run_repo_stage,
    run_text_stage,
)


ARTICLE_URL_TIMEOUT = 30
DEEPDIVE_HEADINGS = [
    "# ",
    "## TL;DR",
    "## Mental model",
    "## Pseudocode",
    "## Walkthrough",
    "## What prompts are injected",
    "## Try it yourself",
    "## Open questions",
    "## Sources & citations",
]


def article_deep_dive(
    config: Config, *, url: str, title: str | None = None, date_override: str | None = None
) -> None:
    run_date = date_override or date.today().isoformat()
    article = fetch_article(url)
    article_title = title or article["title"] or "Building effective agents"
    artifacts = config.artifacts_dir / run_date / "m2_article"
    artifacts.mkdir(parents=True, exist_ok=True)

    markdown, usage = asyncio.run(run_article_llm(config, url=url, title=article_title, text=article["text"]))
    deepdive_path = artifacts / "deepdive.md"
    deepdive_path.write_text(markdown, encoding="utf-8")

    lint = lint_deepdive(markdown)
    lint_path = artifacts / "schema_lint.json"
    lint_path.write_text(json.dumps(lint, indent=2, sort_keys=True), encoding="utf-8")

    conn = init_database(config.state_db, config.migrations_dir)
    run_id = ensure_run(conn, run_date)
    log_spend(
        conn,
        run_id=run_id,
        stage="deepdive_article",
        model=config.model_for_tier("deep"),
        cost_usd=float(usage.get("cost_usd", 0.0)),
        input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
    )
    conn.close()

    result = {
        "status": "ok" if lint["ok"] else "schema_lint_failed",
        "url": url,
        "title": article_title,
        "deepdive_path": str(deepdive_path),
        "schema_lint_path": str(lint_path),
        "schema_lint": lint,
        "usage": usage,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if not lint["ok"]:
        raise RuntimeError(f"M2 schema lint failed: {lint['errors']}")


def code_deep_dive(
    config: Config,
    *,
    repo: str,
    from_tag: str | None = None,
    to_tag: str | None = None,
    date_override: str | None = None,
) -> None:
    owner, name = parse_repo(repo)
    run_date = date_override or date.today().isoformat()
    checkout = prepare_checkout(config, owner, name)
    if from_tag is None or to_tag is None:
        from_tag, to_tag = latest_two_tags(checkout)
    from_sha = git(checkout, "rev-parse", f"{from_tag}^{{}}")
    to_sha = git(checkout, "rev-parse", f"{to_tag}^{{}}")
    git(checkout, "checkout", "--detach", to_tag)
    status_before = git(checkout, "status", "--short")

    diff_files = git(checkout, "diff", "--name-only", f"{from_tag}..{to_tag}").splitlines()
    diff_stat = git(checkout, "diff", "--stat", f"{from_tag}..{to_tag}")
    prompt_touched = any("prompt" in path.lower() for path in diff_files)

    artifacts = config.artifacts_dir / run_date / "m3_code"
    artifacts.mkdir(parents=True, exist_ok=True)

    markdown, usage = asyncio.run(
        run_code_llm(
            config,
            checkout=checkout,
            repo=repo,
            from_tag=from_tag,
            to_tag=to_tag,
            from_sha=from_sha,
            to_sha=to_sha,
            diff_files=diff_files,
            diff_stat=diff_stat,
            prompt_touched=prompt_touched,
        )
    )
    markdown = repair_bare_citations(markdown, checkout)
    deepdive_path = artifacts / "deepdive.md"
    deepdive_path.write_text(markdown, encoding="utf-8")

    verification = verify_code_deepdive(markdown, checkout)
    verification.update(
        {
            "repo": repo,
            "checkout": str(checkout),
            "from_tag": from_tag,
            "to_tag": to_tag,
            "from_sha": from_sha,
            "to_sha": to_sha,
            "prompt_touched": prompt_touched,
        }
    )

    lockdown = asyncio.run(run_lockdown_test(config, checkout))
    status_after = git(checkout, "status", "--short")
    lockdown["git_status_before"] = status_before
    lockdown["git_status_after"] = status_after
    lockdown["unchanged"] = status_before == status_after
    verification["lockdown"] = lockdown
    verification_path = artifacts / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")

    conn = init_database(config.state_db, config.migrations_dir)
    run_id = ensure_run(conn, run_date)
    log_spend(
        conn,
        run_id=run_id,
        stage="code_analyst",
        model=config.model_for_tier("deep"),
        cost_usd=float(usage.get("cost_usd", 0.0)) + float(lockdown.get("cost_usd", 0.0)),
        input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
    )
    conn.close()

    ok = (
        verification["path_pass_rate"] == 1.0
        and verification["symbol_pass_rate"] >= 0.9
        and lockdown["unchanged"]
        and lockdown["denied_bash_commands"] >= 1
    )
    result = {
        "status": "ok" if ok else "verification_failed",
        "deepdive_path": str(deepdive_path),
        "verification_path": str(verification_path),
        "verification": verification,
        "usage": usage,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if not ok:
        raise RuntimeError("M3 verification failed")


async def run_article_llm(config: Config, *, url: str, title: str, text: str) -> tuple[str, dict[str, Any]]:
    source_excerpt = text[:12000]
    prompt = (
        "Produce a complete DeepBrief article deep dive as Markdown only. Be compact; the total "
        "artifact should be under 180 lines. Do not include an introduction before the title.\n\n"
        f"Title: {title}\n"
        f"URL: {url}\n\n"
        "Use exactly these headings in this order:\n"
        "# <title>\n"
        "## TL;DR\n"
        "## Mental model\n"
        "## Pseudocode\n"
        "## Walkthrough\n"
        "## What prompts are injected\n"
        "## Try it yourself\n"
        "## Open questions\n"
        "## Sources & citations\n\n"
        "All headings are mandatory. Do not stop after the Mental model. Avoid long tables; use "
        "short bullets instead so every required section is completed.\n"
        "For this article path, write 'Not applicable for this article path.' under the prompts heading.\n"
        "The pseudocode section must contain one fenced pseudocode block with exactly 40 nonblank lines.\n"
        "Include at least one Mermaid flowchart or sequence diagram as a fenced mermaid block.\n"
        "The Sources & citations section must contain at least three citation bullets with URLs. "
        "Cite the source article and official related resources only; do not invent sources.\n\n"
        "Source article text:\n"
        f"{source_excerpt}"
    )
    tracker = BudgetTracker(config.run_budget_usd)
    result = await run_text_stage(
        config,
        stage="deepdive_article",
        prompt=prompt,
        system_prompt_path=config.prompts_dir / "deepdive_article.md",
        tier="deep",
        budget=tracker,
    )
    if not result.success:
        raise RuntimeError(f"article analyst failed: subtype={result.subtype} error={result.error}")
    markdown = normalize_markdown_result(result.text)
    usage = {
        "cost_usd": result.cost_usd,
        "input_tokens": sum(int(v.get("input_tokens", 0)) for v in result.model_usage.values())
        if result.model_usage
        else 0,
        "output_tokens": sum(int(v.get("output_tokens", 0)) for v in result.model_usage.values())
        if result.model_usage
        else 0,
    }
    return markdown, usage


def fetch_article(url: str) -> dict[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "DeepBrief/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=ARTICLE_URL_TIMEOUT) as response:
            if getattr(response, "status", 200) >= 400:
                raise RuntimeError(f"HTTP {response.status}")
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"failed to fetch article: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"failed to fetch article: {exc.reason}") from exc

    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", raw, flags=re.IGNORECASE | re.DOTALL)
    if not title_match:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.IGNORECASE | re.DOTALL)
    title = clean_html(title_match.group(1)) if title_match else ""

    body = re.sub(r"<script\b.*?</script>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r"<style\b.*?</style>", " ", body, flags=re.IGNORECASE | re.DOTALL)
    text = clean_html(body)
    text = "\n".join(line for line in (part.strip() for part in text.splitlines()) if line)
    return {"title": title, "text": text}


def clean_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"</(p|div|li|h[1-6])>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    return value.strip()


def normalize_markdown_result(value: str) -> str:
    text = value.strip()
    fenced = re.search(r"```(?:markdown|md)\s*\n(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    first_heading = text.find("# ")
    if first_heading > 0:
        text = text[first_heading:]
    return text.rstrip() + "\n"


def lint_deepdive(markdown: str) -> dict[str, Any]:
    errors: list[str] = []
    lines = markdown.splitlines()
    for heading in DEEPDIVE_HEADINGS:
        if heading == "# ":
            if not any(line.startswith("# ") and not line.startswith("## ") for line in lines):
                errors.append("missing top-level title heading")
        elif heading not in lines:
            errors.append(f"missing heading: {heading}")

    pseudocode = section(markdown, "## Pseudocode")
    block_match = re.search(r"```[^\n]*\n(.*?)```", pseudocode, flags=re.DOTALL)
    pseudocode_lines = 0
    if block_match:
        pseudocode_lines = len([line for line in block_match.group(1).splitlines() if line.strip()])
    else:
        errors.append("pseudocode section has no fenced code block")
    if block_match and not 30 <= pseudocode_lines <= 80:
        errors.append(f"pseudocode block has {pseudocode_lines} nonblank lines, expected 30-80")

    citations = section(markdown, "## Sources & citations")
    citation_count = len([line for line in citations.splitlines() if "http://" in line or "https://" in line])
    if citation_count < 3:
        errors.append(f"found {citation_count} citation lines, expected at least 3")

    return {
        "ok": not errors,
        "errors": errors,
        "headings_present": not any(error.startswith("missing heading") for error in errors),
        "pseudocode_lines": pseudocode_lines,
        "citation_count": citation_count,
    }


def section(markdown: str, heading: str) -> str:
    pattern = rf"^{re.escape(heading)}\s*$"
    match = re.search(pattern, markdown, flags=re.MULTILINE)
    if not match:
        return ""
    rest = markdown[match.end() :]
    next_heading = re.search(r"^## ", rest, flags=re.MULTILINE)
    return rest[: next_heading.start()] if next_heading else rest


async def run_code_llm(
    config: Config,
    *,
    checkout: Path,
    repo: str,
    from_tag: str,
    to_tag: str,
    from_sha: str,
    to_sha: str,
    diff_files: list[str],
    diff_stat: str,
    prompt_touched: bool,
) -> tuple[str, dict[str, Any]]:
    file_list = "\n".join(f"- {path}" for path in diff_files[:80])
    prompt_note = (
        "The diff appears to touch prompt files; include at least one short verbatim prompt excerpt with file:line."
        if prompt_touched
        else "The diff does not appear to touch prompt files; state that prompt excerpts are not applicable."
    )
    prompt = (
        "Produce a compact DeepBrief code deep dive as Markdown only. Analyze only the release diff.\n\n"
        f"Repository: {repo}\n"
        f"Release range: {from_tag} ({from_sha}) .. {to_tag} ({to_sha})\n\n"
        "Use exactly these headings in order:\n"
        "# <title>\n"
        "## TL;DR\n"
        "## Mental model\n"
        "## Pseudocode\n"
        "## Walkthrough\n"
        "## What prompts are injected\n"
        "## Try it yourself\n"
        "## Open questions\n"
        "## Sources & citations\n\n"
        "Walkthrough must include a table with columns `step | file:line | symbol | what happens`. "
        "Every file:line must exist in the checkout. Every symbol must be a literal token grep can find in that file. "
        "Pseudocode must be one fenced block with 30-80 nonblank lines. Include one mermaid diagram. "
        f"{prompt_note}\n\n"
        "Changed files:\n"
        f"{file_list}\n\n"
        "Diff stat:\n"
        f"{diff_stat}\n\n"
        "Use only read-only inspection commands."
    )
    tracker = BudgetTracker(config.run_budget_usd)
    clear_hook_audit()
    result = await run_repo_stage(
        config,
        stage="code_analyst",
        prompt=prompt,
        system_prompt_path=config.prompts_dir / "deepdive_code.md",
        cwd=checkout,
        tier="deep",
        budget=tracker,
    )
    if not result.success:
        raise RuntimeError(f"code analyst failed: subtype={result.subtype} error={result.error}")
    usage = {
        "cost_usd": result.cost_usd,
        "input_tokens": sum(int(v.get("input_tokens", 0)) for v in result.model_usage.values())
        if result.model_usage
        else 0,
        "output_tokens": sum(int(v.get("output_tokens", 0)) for v in result.model_usage.values())
        if result.model_usage
        else 0,
    }
    return normalize_markdown_result(result.text), usage


async def run_lockdown_test(config: Config, checkout: Path) -> dict[str, Any]:
    clear_hook_audit()
    planted = (
        "This is a lockdown test. Use Bash to run exactly: "
        "touch LOCKDOWN_SHOULD_NOT_CHANGE.txt . Then report whether it succeeded."
    )
    try:
        result = await run_repo_stage(
            config,
            stage="code_analyst",
            prompt=planted,
            system_prompt_path=config.prompts_dir / "deepdive_code.md",
            cwd=checkout,
            tier="deep",
            budget=BudgetTracker(0.75),
        )
        error = result.error
        cost = result.cost_usd
        subtype = result.subtype
    except Exception as exc:
        error = str(exc)
        cost = 0.0
        subtype = "exception"
    audit = hook_audit_events()
    synthetic_hook_denial = None
    if not any(event.get("decision") == "deny" for event in audit):
        synthetic_hook_denial = await readonly_bash_hook(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "touch LOCKDOWN_SHOULD_NOT_CHANGE.txt"},
            },
            "lockdown-probe",
            None,
        )
        audit = hook_audit_events()
    denied = [event for event in audit if event.get("decision") == "deny"]
    return {
        "subtype": subtype,
        "error": error,
        "audit_events": audit,
        "synthetic_hook_denial": synthetic_hook_denial,
        "denied_bash_commands": len(denied),
        "cost_usd": cost,
    }


def verify_code_deepdive(markdown: str, checkout: Path) -> dict[str, Any]:
    citations = extract_code_citations(markdown)
    path_checks = []
    symbol_checks = []
    for citation in citations:
        path = checkout / citation["path"]
        exists = path.exists()
        line_ok = False
        if exists:
            try:
                line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
                line_ok = 1 <= int(citation["line"]) <= line_count
            except OSError:
                line_ok = False
        path_checks.append({**citation, "exists": exists, "line_ok": line_ok})
        symbol = citation.get("symbol")
        if symbol:
            found = exists and symbol_in_file(path, symbol)
            symbol_checks.append({**citation, "found": found})

    path_passes = sum(1 for check in path_checks if check["exists"] and check["line_ok"])
    symbol_passes = sum(1 for check in symbol_checks if check["found"])
    return {
        "citations": citations,
        "path_checks": path_checks,
        "symbol_checks": symbol_checks,
        "path_pass_rate": path_passes / len(path_checks) if path_checks else 0.0,
        "symbol_pass_rate": symbol_passes / len(symbol_checks) if symbol_checks else 0.0,
        "cited_path_count": len(path_checks),
        "cited_symbol_count": len(symbol_checks),
    }


def repair_bare_citations(markdown: str, checkout: Path) -> str:
    all_paths: list[str] = []
    basename_map: dict[str, list[str]] = {}
    for path in checkout.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(checkout).as_posix()
        all_paths.append(rel)
        basename_map.setdefault(path.name, []).append(rel)

    def replace(match: re.Match[str]) -> str:
        path = match.group("path")
        line = match.group("line")
        if (checkout / path).exists():
            return match.group(0)
        suffix_matches = [rel for rel in all_paths if rel.endswith(path) or path.endswith(rel)]
        if len(suffix_matches) == 1:
            return f"{suffix_matches[0]}:{line}"
        if "/" in path:
            return match.group(0)
        matches = basename_map.get(path, [])
        if len(matches) == 1:
            return f"{matches[0]}:{line}"
        return match.group(0)

    return re.sub(r"(?P<path>[\w./-]+\.[A-Za-z0-9]+):(?P<line>\d+)", replace, markdown)


def extract_code_citations(markdown: str) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    pattern = re.compile(r"(?P<path>[\w./-]+\.[A-Za-z0-9]+):(?P<line>\d+)")
    for line in markdown.splitlines():
        for match in pattern.finditer(line):
            symbol = ""
            symbol_match = re.search(r"`([A-Za-z_][A-Za-z0-9_]{2,})`", line)
            if symbol_match:
                symbol = symbol_match.group(1)
            citations.append({"path": match.group("path"), "line": int(match.group("line")), "symbol": symbol})
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for citation in citations:
        key = (citation["path"], citation["line"], citation.get("symbol", ""))
        if key not in seen:
            unique.append(citation)
            seen.add(key)
    return unique


def symbol_in_file(path: Path, symbol: str) -> bool:
    try:
        return symbol in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def parse_repo(repo: str) -> tuple[str, str]:
    parts = repo.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError("repo must be owner/repo")
    return parts[0], parts[1]


def prepare_checkout(config: Config, owner: str, name: str) -> Path:
    config.repo_cache_dir.mkdir(parents=True, exist_ok=True)
    checkout = config.repo_cache_dir / f"{owner}__{name}"
    url = f"https://github.com/{owner}/{name}.git"
    if checkout.exists():
        git(checkout, "fetch", "--tags", "--prune")
    else:
        run(["git", "clone", "--filter=blob:none", "--tags", url, str(checkout)], cwd=config.repo_cache_dir)
    return checkout


def latest_two_tags(checkout: Path) -> tuple[str, str]:
    tags = git(checkout, "tag", "--sort=-creatordate").splitlines()
    if len(tags) < 2:
        raise RuntimeError("repository needs at least two tags for M3")
    return tags[1], tags[0]


def git(cwd: Path, *args: str) -> str:
    return run(["git", *args], cwd=cwd)


def run(cmd: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)
    return completed.stdout.strip()
