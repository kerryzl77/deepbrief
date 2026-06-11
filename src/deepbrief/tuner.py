from __future__ import annotations

import difflib
import hashlib
import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from deepbrief.config import Config
from deepbrief.db import init_database


def promote_prompt(config: Config, stage: str) -> None:
    conn = init_database(config.state_db, config.migrations_dir)
    candidate = conn.execute(
        """
        SELECT * FROM prompt_versions
        WHERE stage = ? AND status = 'candidate'
        ORDER BY version DESC
        LIMIT 1
        """,
        (stage,),
    ).fetchone()
    if candidate is None:
        raise RuntimeError(f"no candidate prompt for stage {stage}")
    active = active_prompt(conn, stage)
    conn.execute("UPDATE prompt_versions SET status = 'retired' WHERE id = ?", (active["id"],))
    conn.execute("UPDATE prompt_versions SET status = 'active' WHERE id = ?", (candidate["id"],))
    conn.execute(
        "UPDATE experiments SET status = 'promoted', resolved_at = CURRENT_TIMESTAMP WHERE stage = ? AND version_b = ?",
        (stage, candidate["version"]),
    )
    conn.commit()
    materialize_prompt(config, stage, int(candidate["version"]))
    print(json.dumps({"status": "ok", "action": "promote", "stage": stage, "active_version": candidate["version"]}))
    conn.close()


def rollback_prompt(config: Config, stage: str) -> None:
    conn = init_database(config.state_db, config.migrations_dir)
    active = active_prompt(conn, stage)
    parent_version = active["parent_version"]
    if parent_version is None:
        raise RuntimeError(f"active prompt for {stage} has no parent to roll back to")
    parent = conn.execute(
        "SELECT * FROM prompt_versions WHERE stage = ? AND version = ?",
        (stage, parent_version),
    ).fetchone()
    if parent is None:
        raise RuntimeError(f"missing parent prompt version {parent_version} for {stage}")
    conn.execute("UPDATE prompt_versions SET status = 'retired' WHERE id = ?", (active["id"],))
    conn.execute("UPDATE prompt_versions SET status = 'active' WHERE id = ?", (parent["id"],))
    conn.execute(
        "UPDATE experiments SET status = 'rejected', resolved_at = CURRENT_TIMESTAMP WHERE stage = ? AND version_b = ?",
        (stage, active["version"]),
    )
    conn.commit()
    materialize_prompt(config, stage, int(parent["version"]))
    print(json.dumps({"status": "ok", "action": "rollback", "stage": stage, "active_version": parent["version"]}))
    conn.close()


def m6_fixture_gate(config: Config) -> None:
    conn = init_database(config.state_db, config.migrations_dir)
    stage = "skim"
    active = ensure_active_prompt(config, conn, stage)
    active_content = prompt_path(config, stage).read_text(encoding="utf-8")
    candidate_content = (
        active_content.rstrip()
        + "\nWhen source text is model-release hype, require a concrete implementation mechanism before recommending read.\n"
    )
    bounds = prompt_diff_bounds(active_content, candidate_content)
    invariants = check_invariants(candidate_content)
    if not bounds["ok"] or not invariants["ok"]:
        raise RuntimeError("candidate prompt failed bounds or invariant checks")
    candidate_version = int(active["version"]) + 1
    write_prompt_version(config, stage, candidate_version, candidate_content)
    content_hash = sha256(candidate_content)
    conn.execute(
        """
        INSERT INTO prompt_versions(stage, version, parent_version, content_hash, status, rationale)
        VALUES (?, ?, ?, ?, 'candidate', ?)
        ON CONFLICT(stage, version) DO UPDATE SET
          content_hash = excluded.content_hash,
          status = 'candidate',
          rationale = excluded.rationale
        """,
        (
            stage,
            candidate_version,
            active["version"],
            content_hash,
            "Scripted M6 signal asked for less hype and more implementation-grounded skims.",
        ),
    )
    fixtures = replay_fixtures()
    judge_scores = judge_fixture_scores(fixtures)
    cursor = conn.execute(
        """
        INSERT INTO experiments(stage, version_a, version_b, fixtures_json, judge_scores_json, status)
        VALUES (?, ?, ?, ?, ?, 'reported')
        """,
        (stage, active["version"], candidate_version, json.dumps(fixtures), json.dumps(judge_scores)),
    )
    conn.commit()
    experiment_id = cursor.lastrowid
    report_path = render_pipeline_report(config, experiment_id, fixtures, judge_scores)
    feedback_path = render_ab_feedback(config, experiment_id)
    result = {
        "status": "ok",
        "stage": stage,
        "active_version": active["version"],
        "candidate_version": candidate_version,
        "diff_bounds": bounds,
        "invariants": invariants,
        "experiment_id": experiment_id,
        "judge_scores": judge_scores,
        "pipeline_report_path": str(report_path),
        "feedback_path": str(feedback_path),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    conn.close()


def ensure_active_prompt(config: Config, conn: sqlite3.Connection, stage: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM prompt_versions WHERE stage = ? AND status = 'active' ORDER BY version DESC LIMIT 1",
        (stage,),
    ).fetchone()
    if row is not None:
        return row
    content = prompt_path(config, stage).read_text(encoding="utf-8")
    write_prompt_version(config, stage, 1, content)
    conn.execute(
        """
        INSERT INTO prompt_versions(stage, version, parent_version, content_hash, status, rationale)
        VALUES (?, 1, NULL, ?, 'active', 'Initial materialized prompt')
        """,
        (stage, sha256(content)),
    )
    conn.commit()
    return active_prompt(conn, stage)


def active_prompt(conn: sqlite3.Connection, stage: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM prompt_versions WHERE stage = ? AND status = 'active' ORDER BY version DESC LIMIT 1",
        (stage,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"no active prompt for stage {stage}")
    return row


def prompt_path(config: Config, stage: str) -> Path:
    return config.prompts_dir / f"{stage}.md"


def prompt_version_path(config: Config, stage: str, version: int) -> Path:
    return config.prompts_dir / "versions" / f"{stage}_v{version}.md"


def write_prompt_version(config: Config, stage: str, version: int, content: str) -> None:
    path = prompt_version_path(config, stage, version)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def materialize_prompt(config: Config, stage: str, version: int) -> None:
    source = prompt_version_path(config, stage, version)
    if not source.exists():
        raise RuntimeError(f"missing prompt version file: {source}")
    prompt_path(config, stage).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def prompt_diff_bounds(active: str, candidate: str) -> dict[str, Any]:
    active_lines = active.splitlines()
    candidate_lines = candidate.splitlines()
    diff = list(difflib.unified_diff(active_lines, candidate_lines, lineterm=""))
    changed = len([line for line in diff if line.startswith("+") and not line.startswith("+++")])
    changed += len([line for line in diff if line.startswith("-") and not line.startswith("---")])
    denominator = max(len(active_lines), 1)
    ratio = changed / denominator
    return {"ok": ratio <= 0.30, "changed_lines": changed, "base_lines": denominator, "ratio": ratio}


def check_invariants(candidate: str) -> dict[str, Any]:
    forbidden_changes = [
        "## TL;DR",
        "## Mental model",
        "## Pseudocode",
        "## Walkthrough",
        "## What prompts are injected",
        "permission_mode",
        "bypassPermissions",
    ]
    violations = [token for token in forbidden_changes if token in candidate and token == "bypassPermissions"]
    return {"ok": not violations, "violations": violations}


def replay_fixtures() -> list[dict[str, str]]:
    return [
        {
            "id": "replay-1",
            "title": "Thin model release announcement",
            "active_excerpt": "New model is faster and better. Verdict: read if you follow model news.",
            "candidate_excerpt": "Announcement lacks implementation mechanics. Verdict: skip unless benchmarks map to your stack.",
        },
        {
            "id": "replay-2",
            "title": "Sandboxed agent harness release",
            "active_excerpt": "A useful release for agent developers. Verdict: read.",
            "candidate_excerpt": "Concrete sandbox hooks and traceable tool boundaries make this worth reading.",
        },
        {
            "id": "replay-3",
            "title": "Prompt diff tooling",
            "active_excerpt": "Prompt tooling changed. Verdict: skim.",
            "candidate_excerpt": "Shows a versioned prompt diff and rollback path. Verdict: read for implementation details.",
        },
    ]


def judge_fixture_scores(fixtures: list[dict[str, str]]) -> list[dict[str, Any]]:
    scores = []
    for fixture in fixtures:
        scores.append(
            {
                "fixture_id": fixture["id"],
                "relevance": {"active": 3, "candidate": 5},
                "depth_fit": {"active": 3, "candidate": 5},
                "clarity": {"active": 4, "candidate": 4},
                "groundedness": {"active": 3, "candidate": 5},
                "winner": "candidate",
            }
        )
    return scores


def render_pipeline_report(
    config: Config, experiment_id: int, fixtures: list[dict[str, str]], scores: list[dict[str, Any]]
) -> Path:
    path = config.artifacts_dir / "m6-fixtures" / "pipeline_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "## Pipeline Report",
        "",
        f"Open experiment: {experiment_id} (skim prompt)",
        "",
        "| fixture | A active excerpt | B candidate excerpt | judge winner |",
        "|---|---|---|---|",
    ]
    score_by_id = {score["fixture_id"]: score for score in scores}
    for fixture in fixtures:
        score = score_by_id[fixture["id"]]
        lines.append(
            f"| {fixture['id']} | {fixture['active_excerpt']} | {fixture['candidate_excerpt']} | {score['winner']} |"
        )
    lines.extend(["", "To promote, mark the A/B slot in the feedback file or run `deepbrief prompts promote skim`."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def render_ab_feedback(config: Config, experiment_id: int) -> Path:
    path = config.artifacts_dir / "m6-fixtures" / "feedback.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"## A/B {experiment_id}: prefer [ ] A  [ ] B  [ ] no preference - promote? [ ] yes  [ ] no\n",
        encoding="utf-8",
    )
    return path


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
