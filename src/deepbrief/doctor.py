from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from deepbrief.config import Config, load_sources
from deepbrief.db import apply_migrations, connect, table_names
from deepbrief.llm import self_test


REQUIRED_TABLES = {
    "items",
    "runs",
    "ratings",
    "feedback",
    "concepts",
    "concept_edges",
    "item_concepts",
    "prompt_versions",
    "experiments",
    "preference_revisions",
    "spend_log",
    "schema_migrations",
}


def run_doctor(config: Config) -> None:
    missing = [path for path in config.require_seed_files() if not path.exists()]
    if missing:
        joined = "\n  ".join(str(path) for path in missing)
        raise RuntimeError(f"missing scaffold files:\n  {joined}")

    sources = load_sources(config.sources_path)
    for key in ("feeds", "repos", "arxiv"):
        if key not in sources:
            raise RuntimeError(f"sources.yaml missing {key}")

    if config.repo_backend.value != "claude_agent_sdk":
        raise RuntimeError("repo_backend must remain claude_agent_sdk")
    if "fast" not in config.models or "deep" not in config.models:
        raise RuntimeError("config.yaml must define fast and deep model tiers")

    with tempfile.TemporaryDirectory(prefix="deepbrief-doctor-") as tmp:
        conn = connect(Path(tmp) / "state.db")
        applied = apply_migrations(conn, config.migrations_dir)
        tables = table_names(conn)
        missing_tables = REQUIRED_TABLES - tables
        if missing_tables:
            raise RuntimeError(f"missing migrated tables: {sorted(missing_tables)}")
        conn.close()

    llm_checks = asyncio.run(self_test(config))

    print("DeepBrief M0 doctor: ok")
    print(f"repo: {config.repo_root}")
    print(f"seed files: {len(config.require_seed_files())} present")
    print(f"sources: {len(sources['feeds'])} feeds, {len(sources['repos'])} repos, arxiv configured")
    print(f"migrations applied in temp db: {', '.join(applied) if applied else 'already current'}")
    for check in llm_checks:
        print(f"llm: {check}")
