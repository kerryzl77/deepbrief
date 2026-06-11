from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    pass


class RepoBackend(StrEnum):
    CLAUDE_AGENT_SDK = "claude_agent_sdk"


DEFAULT_CONFIG_PATH = Path("config.yaml")


@dataclass(frozen=True)
class Config:
    repo_root: Path
    state_dir: Path
    artifacts_dir: Path
    repo_cache_dir: Path
    state_db: Path
    sources_path: Path
    profile_path: Path
    preferences_path: Path
    prompts_dir: Path
    migrations_dir: Path
    templates_dir: Path
    launchd_dir: Path
    repo_backend: RepoBackend
    run_budget_usd: float
    tuner_budget_usd: float
    stage_budgets: dict[str, float]
    models: dict[str, str]
    schedule: dict[str, int]
    auto_promote: bool
    ab_live_variant: str

    @classmethod
    def load(cls, path: Path | str = DEFAULT_CONFIG_PATH) -> "Config":
        repo_root = Path.cwd()
        _load_dotenv(repo_root / ".env")
        config_path = repo_root / Path(path)
        if not config_path.exists():
            raise ConfigError(f"missing config file: {config_path}")
        raw = _load_structured_file(config_path)
        if not isinstance(raw, dict):
            raise ConfigError("config root must be an object")

        state_dir = _expand_path(raw.get("state_dir", "~/.deepbrief"))
        artifacts_dir = _expand_path(raw.get("artifacts_dir", "~/DeepBrief"))
        repo_cache_dir = _expand_path(raw.get("repo_cache_dir", str(state_dir / "repos")))
        budget = _require_dict(raw, "budgets")
        models = _require_dict(raw, "models")
        stages = budget.get("stages", {})
        if not isinstance(stages, dict):
            raise ConfigError("budgets.stages must be an object")

        try:
            backend = RepoBackend(str(raw.get("repo_backend", "claude_agent_sdk")))
        except ValueError as exc:
            raise ConfigError("repo_backend must be claude_agent_sdk") from exc

        schedule = raw.get("schedule", {"hour": 6, "minute": 15})
        if not isinstance(schedule, dict):
            raise ConfigError("schedule must be an object")

        return cls(
            repo_root=repo_root,
            state_dir=state_dir,
            artifacts_dir=artifacts_dir,
            repo_cache_dir=repo_cache_dir,
            state_db=state_dir / "state.db",
            sources_path=repo_root / str(raw.get("sources_path", "sources.yaml")),
            profile_path=repo_root / str(raw.get("profile_path", "profile.md")),
            preferences_path=repo_root / str(raw.get("preferences_path", "preferences.md")),
            prompts_dir=repo_root / str(raw.get("prompts_dir", "prompts")),
            migrations_dir=repo_root / str(raw.get("migrations_dir", "migrations")),
            templates_dir=repo_root / str(raw.get("templates_dir", "templates")),
            launchd_dir=repo_root / str(raw.get("launchd_dir", "launchd")),
            repo_backend=backend,
            run_budget_usd=float(budget.get("run_usd", 5.0)),
            tuner_budget_usd=float(budget.get("tuner_usd", 2.5)),
            stage_budgets={str(k): float(v) for k, v in stages.items()},
            models={str(k): str(v) for k, v in models.items()},
            schedule={"hour": int(schedule.get("hour", 6)), "minute": int(schedule.get("minute", 15))},
            auto_promote=bool(raw.get("auto_promote", False)),
            ab_live_variant=str(raw.get("ab_live_variant", "skims_only")),
        )

    def stage_budget(self, stage: str) -> float:
        return self.stage_budgets.get(stage, self.run_budget_usd)

    def model_for_tier(self, tier: str) -> str:
        try:
            return self.models[tier]
        except KeyError as exc:
            raise ConfigError(f"missing model tier in config.yaml: {tier}") from exc

    def require_seed_files(self) -> list[Path]:
        return [
            self.sources_path,
            self.profile_path,
            self.preferences_path,
            self.prompts_dir / "rank.md",
            self.prompts_dir / "deepdive_article.md",
            self.prompts_dir / "deepdive_code.md",
            self.prompts_dir / "skim.md",
            self.prompts_dir / "signal_extract.md",
            self.prompts_dir / "tuner.md",
            self.prompts_dir / "judge.md",
            self.prompts_dir / "librarian.md",
            self.templates_dir / "brief.typ",
            self.templates_dir / "feedback.md.j2",
            self.launchd_dir / "com.USER.deepbrief.plist.j2",
        ]


def load_sources(path: Path) -> dict[str, Any]:
    raw = _load_structured_file(path)
    if not isinstance(raw, dict):
        raise ConfigError("sources root must be an object")
    return raw


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value)))


def _require_dict(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be an object")
    return value


def _load_structured_file(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ConfigError(
                f"{path} is not JSON and PyYAML is not installed; keep M0 seed files as JSON-compatible YAML"
            ) from exc
        try:
            return yaml.safe_load(text)
        except Exception as exc:  # pragma: no cover - depends on optional PyYAML
            raise ConfigError(f"failed to parse {path}: {json_error}") from exc


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
