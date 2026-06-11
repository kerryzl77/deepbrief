from __future__ import annotations

import difflib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from deepbrief.config import Config
from deepbrief.db import ensure_run, init_database


def open_feedback(config: Config, *, date_override: str | None = None) -> None:
    raise RuntimeError("feedback channel is not implemented beyond M0 scaffold")


def record_rating(config: Config, item_id: str, value: str, note: str | None = None) -> None:
    raise RuntimeError("rating storage is not implemented beyond M0 scaffold")


def m5_fixture_gate(config: Config) -> None:
    conn = init_database(config.state_db, config.migrations_dir)
    run_id = ensure_run(conn, "m5-fixtures")
    seed_fixture_items(conn)
    before = fixture_rank_scores(conn)

    artifact_dir = config.artifacts_dir / "m5-fixtures"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    template_path = artifact_dir / "feedback_template.md"
    filled_path = artifact_dir / "feedback_filled.md"
    template = feedback_template()
    filled = scripted_negative_feedback()
    template_path.write_text(template, encoding="utf-8")
    filled_path.write_text(filled, encoding="utf-8")

    signals = ingest_feedback(conn, config.preferences_path, filled, run_date=date.today().isoformat())
    after = fixture_rank_scores(conn)
    conn.close()

    shifts = {
        item_id: after[item_id] - before[item_id]
        for item_id in before
        if item_id in after
    }
    result = {
        "status": "ok",
        "run_id": run_id,
        "template_path": str(template_path),
        "filled_feedback_path": str(filled_path),
        "signals": signals,
        "score_before": before,
        "score_after": after,
        "score_shifts": shifts,
        "negative_rating_shifted_rank": shifts.get("fixture_model_hype", 0) < 0,
        "preference_revision_recorded": signals["preference_revision_id"] is not None,
        "preferences_path": str(config.preferences_path),
    }
    if not result["negative_rating_shifted_rank"] or not result["preference_revision_recorded"]:
        result["status"] = "failed"
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "ok":
        raise RuntimeError("M5 fixture gate failed")


def seed_fixture_items(conn: Any) -> None:
    rows = [
        (
            "fixture_agent_release",
            "m5_fixture",
            "https://example.invalid/agent-release",
            "Grounded agent harness release",
            "repo_release",
            "2026-06-10T00:00:00Z",
            "fixture-agent-release",
            72.0,
            "Grounded coding-agent internals.",
        ),
        (
            "fixture_model_hype",
            "m5_fixture",
            "https://example.invalid/model-hype",
            "Thin model release hype",
            "article",
            "2026-06-10T00:00:00Z",
            "fixture-model-hype",
            72.0,
            "Initially tied before feedback penalty.",
        ),
    ]
    for row in rows:
        conn.execute(
            """
            INSERT INTO items
              (id, source_id, url, title, type, published_at, discovered_at, hash, status, score, score_reasons)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 'new', ?, ?)
            ON CONFLICT(id) DO UPDATE SET score = excluded.score, score_reasons = excluded.score_reasons
            """,
            row,
        )
    conn.commit()


def feedback_template() -> str:
    return """# DeepBrief feedback - M5 fixture

## fixture_agent_release - Grounded agent harness release
rating: [ ] up  [ ] down
note:

## fixture_model_hype - Thin model release hype
rating: [ ] up  [ ] down
note:

## What to change

"""


def scripted_negative_feedback() -> str:
    return """# DeepBrief feedback - M5 fixture

## fixture_agent_release - Grounded agent harness release
rating: [x] up  [ ] down
note: Useful because it was grounded in actual code paths.

## fixture_model_hype - Thin model release hype
rating: [ ] up  [x] down
note: Too much model-release hype and not enough implementation detail.

## What to change

Prefer code-grounded agent harnesses, sandboxing details, and prompt/version diffs. Penalize
thin model-release hype unless it includes concrete implementation mechanics.
"""


def ingest_feedback(conn: Any, preferences_path: Path, raw_text: str, *, run_date: str) -> dict[str, Any]:
    ratings = parse_ratings(raw_text)
    for rating in ratings:
        conn.execute(
            "INSERT INTO ratings(item_id, value, note) VALUES (?, ?, ?)",
            (rating["item_id"], rating["value"], rating.get("note")),
        )
    preference_bullet = (
        f"- {run_date}: Penalize thin model-release hype; prefer code-grounded agent harnesses, "
        "sandboxing details, and prompt/version diffs."
    )
    before = preferences_path.read_text(encoding="utf-8") if preferences_path.exists() else ""
    after = before if preference_bullet in before else before.rstrip() + "\n" + preference_bullet + "\n"
    preferences_path.write_text(after, encoding="utf-8")
    diff = "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile="preferences.md.before",
            tofile="preferences.md.after",
            lineterm="",
        )
    )
    cursor = conn.execute(
        "INSERT INTO preference_revisions(date, content, diff_summary) VALUES (?, ?, ?)",
        (run_date, after, diff or "no textual change; preference already present"),
    )
    signals = {
        "ratings": ratings,
        "preference_revision_id": cursor.lastrowid,
        "preference_bullet": preference_bullet,
        "diff_summary": diff,
    }
    conn.execute(
        "INSERT INTO feedback(date, raw_text, signals_json) VALUES (?, ?, ?)",
        (run_date, raw_text, json.dumps(signals, sort_keys=True)),
    )
    conn.commit()
    return signals


def parse_ratings(raw_text: str) -> list[dict[str, str]]:
    ratings: list[dict[str, str]] = []
    current_item = ""
    note = ""
    for line in raw_text.splitlines():
        heading = re.match(r"^##\s+([A-Za-z0-9_-]+)\s+-", line)
        if heading:
            current_item = heading.group(1)
            note = ""
            continue
        if line.startswith("note:"):
            note = line.partition(":")[2].strip()
            continue
        if current_item and line.startswith("rating:"):
            if "[x] up" in line:
                ratings.append({"item_id": current_item, "value": "up", "note": note})
            elif "[x] down" in line:
                ratings.append({"item_id": current_item, "value": "down", "note": note})
    return ratings


def fixture_rank_scores(conn: Any) -> dict[str, float]:
    scores: dict[str, float] = {}
    for row in conn.execute(
        """
        SELECT i.id, i.score,
               COALESCE(SUM(CASE r.value WHEN 'up' THEN 5 WHEN 'down' THEN -10 ELSE 0 END), 0) AS modifier
        FROM items i
        LEFT JOIN ratings r ON r.item_id = i.id
        WHERE i.id IN ('fixture_agent_release', 'fixture_model_hype')
        GROUP BY i.id, i.score
        """
    ):
        scores[row["id"]] = float(row["score"] or 0) + float(row["modifier"] or 0)
    return scores
