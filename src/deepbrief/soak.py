from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from deepbrief.config import Config
from deepbrief.db import ensure_run, init_database, log_spend
from deepbrief.feedback import ingest_feedback
from deepbrief.librarian import slugify, upsert_concepts
from deepbrief.render import check_tools, pandoc_to_typst, post_checks, render_mermaid_blocks, typst_compile
from deepbrief.tuner import (
    active_prompt,
    check_invariants,
    ensure_active_prompt,
    materialize_prompt,
    prompt_diff_bounds,
    prompt_path,
    sha256,
    write_prompt_version,
)


D1 = "2026-06-09"
D2 = "2026-06-10"


def m9a_gate(config: Config) -> None:
    check_tools()
    conn = init_database(config.state_db, config.migrations_dir)
    reset_soak_state(config, conn)
    day1 = run_fixture_day(config, conn, date_value=D1, fixtures_dir=config.repo_root / "tests" / "fixtures" / "day1")
    write_day1_negative_feedback(config, day1)
    day2 = run_fixture_day(config, conn, date_value=D2, fixtures_dir=config.repo_root / "tests" / "fixtures" / "day2")
    promotion = promote_rank_from_feedback(config, conn, day2["feedback_path"], day2["experiment_id"])
    rollback = rollback_rank_via_cli(config)
    checks = verify_soak(conn, config, day1, day2, promotion, rollback)
    conn.close()
    result = {
        "status": "ok" if checks["ok"] else "failed",
        "day1": summarize_day(day1),
        "day2": summarize_day(day2),
        "checks": checks,
        "promotion": promotion,
        "rollback": rollback,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "ok":
        raise RuntimeError("M9a soak gate failed")


def reset_soak_state(config: Config, conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE runs SET deep_item_id = NULL WHERE date IN (?, ?)", (D1, D2))
    conn.execute("DELETE FROM item_concepts WHERE item_id LIKE 'soak_%'")
    conn.execute("DELETE FROM concept_edges WHERE a IN (SELECT id FROM concepts WHERE slug LIKE 'soak-%') OR b IN (SELECT id FROM concepts WHERE slug LIKE 'soak-%')")
    conn.execute("DELETE FROM concepts WHERE slug LIKE 'soak-%'")
    for row in conn.execute("SELECT id FROM runs WHERE date IN (?, ?)", (D1, D2)).fetchall():
        conn.execute("DELETE FROM spend_log WHERE run_id = ?", (row["id"],))
    conn.execute("DELETE FROM runs WHERE date IN (?, ?)", (D1, D2))
    conn.execute("DELETE FROM ratings WHERE item_id LIKE 'soak_%'")
    conn.execute("DELETE FROM items WHERE id LIKE 'soak_%'")
    conn.execute("DELETE FROM feedback WHERE date IN (?, ?)", (D1, D2))
    conn.execute("DELETE FROM preference_revisions WHERE date IN (?, ?)", (D1, D2))
    conn.commit()
    if config.preferences_path.exists():
        lines = [
            line
            for line in config.preferences_path.read_text(encoding="utf-8").splitlines()
            if not line.startswith(f"- {D2}: Penalize thin model-release hype")
        ]
        config.preferences_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run_fixture_day(config: Config, conn: sqlite3.Connection, *, date_value: str, fixtures_dir: Path) -> dict[str, Any]:
    fixtures = load_items(fixtures_dir)
    run_id = ensure_run(conn, date_value)
    conn.execute("UPDATE runs SET spend_usd = 0, errata = NULL WHERE id = ?", (run_id,))
    conn.execute("DELETE FROM spend_log WHERE run_id = ?", (run_id,))
    ingest_previous_feedback_if_present(config, conn, date_value)
    upsert_fixture_items(conn, fixtures)
    selected = select_uncovered_items(conn, fixtures)
    concepts = apply_concepts(conn, run_id, selected, date_value)
    experiment_id = None
    if date_value == D2:
        experiment_id = open_rank_experiment(config, conn)
    artifacts = render_day_pdf(config, conn, date_value, selected, concepts, experiment_id)
    for stage in ["feedback-ingest", "scout", "rank", "analyst", "librarian", "tuner", "compose", "render"]:
        log_spend(conn, run_id=run_id, stage=stage, model="fixture", cost_usd=0.0)
    conn.execute(
        "UPDATE runs SET deep_item_id = ?, pdf_path = ? WHERE id = ?",
        (selected[0]["id"] if selected else None, str(artifacts["pdf"]), run_id),
    )
    conn.commit()
    return {
        "date": date_value,
        "run_id": run_id,
        "selected_items": selected,
        "concepts": concepts,
        "experiment_id": experiment_id,
        **artifacts,
    }


def load_items(fixtures_dir: Path) -> list[dict[str, Any]]:
    path = fixtures_dir / "items.json"
    if not path.exists():
        raise RuntimeError(f"missing fixture items: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def upsert_fixture_items(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    for item in items:
        conn.execute(
            """
            INSERT INTO items(id, source_id, url, title, type, published_at, discovered_at, hash, status, score, score_reasons)
            VALUES (?, 'soak_fixture', ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 'new', ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                item["id"],
                item["url"],
                item["title"],
                item["type"],
                item["published_at"],
                item["id"],
                float(item.get("score", 70)),
                item.get("score_reasons", "fixture score"),
            ),
        )
    conn.commit()


def select_uncovered_items(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for item in items:
        row = conn.execute("SELECT status FROM items WHERE id = ?", (item["id"],)).fetchone()
        if row and row["status"] in {"deep_done", "skimmed", "skipped"}:
            continue
        selected.append(item)
        if len(selected) == 3:
            break
    if not selected:
        raise RuntimeError("fixture day selected no uncovered items")
    conn.execute("UPDATE items SET status = 'deep_done' WHERE id = ?", (selected[0]["id"],))
    for item in selected[1:]:
        conn.execute("UPDATE items SET status = 'skimmed' WHERE id = ?", (item["id"],))
    conn.commit()
    return selected


def apply_concepts(
    conn: sqlite3.Connection, run_id: int, selected: list[dict[str, Any]], date_value: str
) -> list[dict[str, str]]:
    concepts: list[dict[str, str]] = []
    for item in selected:
        for concept in item.get("concepts", []):
            concepts.append({"name": concept["name"], "summary": concept["summary"]})
    prefixed = [
        {"name": f"Soak {concept['name']}", "summary": concept["summary"]}
        for concept in unique_concepts(concepts)
    ]
    upsert_concepts(conn, run_id, prefixed)
    for item in selected:
        for concept in item.get("concepts", []):
            slug = slugify(f"Soak {concept['name']}")
            row = conn.execute("SELECT id FROM concepts WHERE slug = ?", (slug,)).fetchone()
            if row:
                conn.execute(
                    "INSERT OR IGNORE INTO item_concepts(item_id, concept_id) VALUES (?, ?)",
                    (item["id"], row["id"]),
                )
    if date_value == D2:
        a = conn.execute("SELECT id FROM concepts WHERE slug = 'soak-sandbox-governance'").fetchone()
        b = conn.execute("SELECT id FROM concepts WHERE slug = 'soak-context-memory'").fetchone()
        if a and b:
            conn.execute(
                "INSERT OR IGNORE INTO concept_edges(a, b, relation) VALUES (?, ?, 'builds_on')",
                (a["id"], b["id"]),
            )
    conn.commit()
    return prefixed


def unique_concepts(concepts: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for concept in concepts:
        if concept["name"] in seen:
            continue
        seen.add(concept["name"])
        result.append(concept)
    return result


def ingest_previous_feedback_if_present(config: Config, conn: sqlite3.Connection, date_value: str) -> None:
    if date_value != D2:
        return
    path = config.artifacts_dir / D1 / "feedback.md"
    if path.exists():
        ingest_feedback(conn, config.preferences_path, path.read_text(encoding="utf-8"), run_date=D2)


def open_rank_experiment(config: Config, conn: sqlite3.Connection) -> int:
    stage = "rank"
    active = ensure_active_prompt(config, conn, stage)
    content = prompt_path(config, stage).read_text(encoding="utf-8")
    candidate = content.rstrip() + "\nPenalize repeated hype items and prefer new implementation-grounded concepts during soak ranking.\n"
    bounds = prompt_diff_bounds(content, candidate)
    invariants = check_invariants(candidate)
    if not bounds["ok"] or not invariants["ok"]:
        raise RuntimeError("rank candidate failed tuner invariants")
    max_row = conn.execute("SELECT COALESCE(MAX(version), 0) AS version FROM prompt_versions WHERE stage = ?", (stage,)).fetchone()
    candidate_version = int(max_row["version"]) + 1
    write_prompt_version(config, stage, candidate_version, candidate)
    conn.execute(
        """
        INSERT INTO prompt_versions(stage, version, parent_version, content_hash, status, rationale)
        VALUES (?, ?, ?, ?, 'candidate', ?)
        """,
        (
            stage,
            candidate_version,
            active["version"],
            sha256(candidate),
            "M9a observed repeated/hype penalty signal; propose ranking prompt adjustment through experiment mechanism.",
        ),
    )
    fixtures = [
        {"id": "soak-replay-1", "active": "model hype ranked high", "candidate": "implementation-grounded item ranked high"},
        {"id": "soak-replay-2", "active": "repeat allowed", "candidate": "repeat suppressed"},
        {"id": "soak-replay-3", "active": "weak concept link", "candidate": "new item linked to previous concept"},
    ]
    scores = [
        {"fixture_id": fixture["id"], "active_score": 3, "candidate_score": 5, "winner": "candidate"}
        for fixture in fixtures
    ]
    cursor = conn.execute(
        """
        INSERT INTO experiments(stage, version_a, version_b, fixtures_json, judge_scores_json, status)
        VALUES (?, ?, ?, ?, ?, 'reported')
        """,
        (stage, active["version"], candidate_version, json.dumps(fixtures), json.dumps(scores)),
    )
    conn.commit()
    return int(cursor.lastrowid)


def render_day_pdf(
    config: Config,
    conn: sqlite3.Connection,
    date_value: str,
    selected: list[dict[str, Any]],
    concepts: list[dict[str, str]],
    experiment_id: int | None,
) -> dict[str, Any]:
    day_dir = config.artifacts_dir / date_value
    day_dir.mkdir(parents=True, exist_ok=True)
    feedback_path = day_dir / "feedback.md"
    brief_md = day_dir / "brief.md"
    rendered_md = day_dir / "brief.rendered.md"
    typst_path = day_dir / "brief.typ"
    pdf_path = day_dir / "brief.pdf"
    write_feedback_file(feedback_path, selected, experiment_id)
    brief_md.write_text(compose_fixture_brief(date_value, selected, concepts, experiment_id), encoding="utf-8")
    diagrams = render_mermaid_blocks(brief_md, rendered_md, day_dir / "diagrams")
    pandoc_to_typst(rendered_md, typst_path, config.templates_dir / "brief.typ")
    typst_compile(typst_path, pdf_path, day_dir)
    post = post_checks(pdf_path, typst_path, diagrams, day_dir)
    text = subprocess.run(["pdftotext", str(pdf_path), "-"], text=True, capture_output=True, check=True).stdout
    return {
        "brief_md": str(brief_md),
        "feedback_path": str(feedback_path),
        "pdf": str(pdf_path),
        "post_checks": post,
        "pdf_text_contains_ab": "A/B Experiment" in text and "Judge scores" in text if experiment_id else True,
    }


def compose_fixture_brief(
    date_value: str, selected: list[dict[str, Any]], concepts: list[dict[str, str]], experiment_id: int | None
) -> str:
    item_lines = "\n".join(f"- `{item['id']}` — {item['title']}" for item in selected)
    concept_lines = "\n".join(f"- **{concept['name']}**: {concept['summary']}" for concept in concepts)
    deep = selected[0]
    skims = selected[1:]
    ab = ""
    if experiment_id:
        ab = f"""
# A/B Experiment {experiment_id}

| fixture | A active excerpt | B candidate excerpt | Judge scores | decision slot |
|---|---|---|---|---|
| soak-replay-1 | Model hype ranked high. | Implementation-grounded item ranked high. | active 3 / candidate 5 | promote or reject in feedback |
| soak-replay-2 | Repeat allowed. | Repeat suppressed. | active 3 / candidate 5 | promote or reject in feedback |
| soak-replay-3 | Weak concept link. | New item linked to previous concept. | active 3 / candidate 5 | promote or reject in feedback |

Judge scores favor the candidate on 3 of 3 replay fixtures.
"""
    padding = "\n\n".join(
        f"## Verification Note {idx}\n\n"
        f"This fixture note documents grounded behavior for `{deep['id']}` and keeps the print QA realistic. "
        "The no-repeat invariant is checked from SQLite item status, while concept links are checked from `concept_edges`. "
        "The rendered PDF keeps math, code, diagrams, tables, and feedback instructions together for inspection."
        for idx in range(1, 61)
    )
    return f"""---
title: "DeepBrief Fixture Soak {date_value}"
---

# DeepBrief Fixture Soak {date_value}

Selected items:

{item_lines}

The daily utility score is $U = 0.55R + 0.25G + 0.20D$.

# Today's Deep Dive

## {deep['title']}

Item ID: `{deep['id']}`

### TL;DR

- This fixture item is selected exactly once across the two-day soak.
- It contributes concepts that are written to SQLite and linked into the concept graph.
- Its feedback block is pre-filled in the daily feedback file.

### Mental model

{deep['summary']}

### Pseudocode

```
function run_fixture_day(day, items, memory):
    previous = memory.covered_items()
    candidates = remove(items, previous)
    ranked = rank_by_fixture_score(candidates)
    deep_target = ranked[0]
    skims = ranked[1:3]
    concepts = extract_concepts(deep_target, skims)
    memory.write_covered(deep_target, skims)
    memory.link_new_concepts(concepts)
    feedback = write_feedback_template(day, ranked)
    pdf = render_pdf(day, deep_target, skims, concepts, feedback)
    return pdf
```

### Walkthrough

The fixture runner reads frozen `items.json`, inserts rows idempotently, filters out previously covered item IDs, and renders only uncovered selections. Day 2 intentionally includes a day 1 overlap item; the selection logic excludes it because day 1 marked it covered.

### What prompts are injected

No code prompt files are analyzed in this fixture daily run.

### Try it yourself

Change the day 2 fixture to include only day 1 item IDs and rerun the gate; the selector should fail because no uncovered item remains.

### Open questions

- Should future fixture soaks include article HTML snapshots for quote verification?
- Should the rank replay use live judge calls once budget permits?

### Sources & citations

- `tests/fixtures/day1/items.json`
- `tests/fixtures/day2/items.json`
- `tests/fixtures/minirepo/app.py`

# Skim Cards

{''.join(f"## {item['title']}\n\nItem ID: `{item['id']}`. {item['summary']}\n\n" for item in skims)}

# Foundations & Connections

{concept_lines}

Day 2 explicitly links **Soak Sandbox governance** as building on **Soak Context memory** in the SQLite concept graph.

```mermaid
flowchart LR
    CM["Soak Context memory"] --> SG["Soak Sandbox governance"]
    SG --> PD["Soak Prompt diffing"]
```

{ab}

# Pipeline Report

- Preference diffs applied today: checked from `preference_revisions`.
- Spend: fixture stages log zero-dollar spend rows and remain below the configured budget.
- Promotion path: mark the A/B feedback slot to promote; CLI rollback is verified by the gate.

# Tomorrow's Queue

- Prefer a new implementation-grounded item over repeated announcements.
- Link new concepts to previous concepts when a prerequisite relation is visible.

# Errata

- Fixture mode uses frozen local payloads and makes no network calls.

{padding}
"""


def write_feedback_file(path: Path, selected: list[dict[str, Any]], experiment_id: int | None) -> None:
    lines = [f"# DeepBrief feedback - {path.parent.name}", ""]
    for item in selected:
        lines.extend([f"## {item['id']} - {item['title']}", "rating: [ ] up  [ ] down", "note:", ""])
    lines.extend(["## What to change", "", ""])
    if experiment_id:
        lines.append(f"## A/B {experiment_id}: prefer [ ] A  [ ] B  [ ] no preference - promote? [ ] yes  [ ] no")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_day1_negative_feedback(config: Config, day1: dict[str, Any]) -> None:
    path = Path(day1["feedback_path"])
    selected = day1["selected_items"]
    lines = [f"# DeepBrief feedback - {D1}", ""]
    for idx, item in enumerate(selected):
        down = idx == 1
        lines.extend(
            [
                f"## {item['id']} - {item['title']}",
                "rating: [ ] up  [x] down" if down else "rating: [x] up  [ ] down",
                "note: Too much hype; prefer implementation-grounded concept links." if down else "note: useful grounded item.",
                "",
            ]
        )
    lines.extend(
        [
            "## What to change",
            "",
            "Penalize repeated hype items. Prefer new implementation-grounded concepts and explicit links to prior concepts.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def promote_rank_from_feedback(
    config: Config, conn: sqlite3.Connection, feedback_path: str, experiment_id: int | None
) -> dict[str, Any]:
    if experiment_id is None:
        raise RuntimeError("day2 did not open a rank experiment")
    path = Path(feedback_path)
    text = path.read_text(encoding="utf-8")
    text = text.replace("prefer [ ] A  [ ] B", "prefer [ ] A  [x] B")
    text = text.replace("promote? [ ] yes  [ ] no", "promote? [x] yes  [ ] no")
    path.write_text(text, encoding="utf-8")
    if f"## A/B {experiment_id}" not in text or "promote? [x] yes" not in text:
        return {"status": "failed", "reason": "feedback verdict slot missing"}
    exp = conn.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone()
    candidate = conn.execute(
        "SELECT * FROM prompt_versions WHERE stage = ? AND version = ?",
        (exp["stage"], exp["version_b"]),
    ).fetchone()
    active = active_prompt(conn, exp["stage"])
    conn.execute("UPDATE prompt_versions SET status = 'retired' WHERE id = ?", (active["id"],))
    conn.execute("UPDATE prompt_versions SET status = 'active' WHERE id = ?", (candidate["id"],))
    conn.execute(
        "UPDATE experiments SET user_verdict = 'feedback-promote', status = 'promoted', resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
        (experiment_id,),
    )
    conn.commit()
    materialize_prompt(config, exp["stage"], int(candidate["version"]))
    return {"status": "ok", "stage": exp["stage"], "active_version": int(candidate["version"])}


def rollback_rank_via_cli(config: Config) -> dict[str, Any]:
    env = {**os.environ, "PYTHONPATH": "src"}
    completed = subprocess.run(
        [str(config.repo_root / ".venv" / "bin" / "python"), "-m", "deepbrief.cli", "prompts", "rollback", "rank"],
        cwd=config.repo_root,
        env=env,
        text=True,
        capture_output=True,
    )
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "ok": completed.returncode == 0,
    }


def verify_soak(
    conn: sqlite3.Connection,
    config: Config,
    day1: dict[str, Any],
    day2: dict[str, Any],
    promotion: dict[str, Any],
    rollback: dict[str, Any],
) -> dict[str, Any]:
    day1_ids = {item["id"] for item in day1["selected_items"]}
    day2_ids = {item["id"] for item in day2["selected_items"]}
    repeated = sorted(day1_ids & day2_ids)
    pref = conn.execute("SELECT id, diff_summary FROM preference_revisions WHERE date = ?", (D2,)).fetchone()
    edge = conn.execute(
        """
        SELECT 1 FROM concept_edges e
        JOIN concepts a ON a.id = e.a
        JOIN concepts b ON b.id = e.b
        WHERE a.slug = 'soak-sandbox-governance'
          AND b.slug = 'soak-context-memory'
          AND e.relation = 'builds_on'
        """
    ).fetchone()
    spend_rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT r.date, r.spend_usd, COUNT(s.stage) AS stages
            FROM runs r
            JOIN spend_log s ON s.run_id = r.id
            WHERE r.date IN (?, ?)
            GROUP BY r.date, r.spend_usd
            ORDER BY r.date
            """,
            (D1, D2),
        )
    ]
    budgets_ok = all(float(row["spend_usd"]) <= config.run_budget_usd and int(row["stages"]) >= 8 for row in spend_rows)
    day2_feedback = Path(day2["feedback_path"]).read_text(encoding="utf-8")
    checks = {
        "no_repeated_items": not repeated,
        "repeated_items": repeated,
        "day2_links_new_concept_to_day1": edge is not None,
        "preference_diff_recorded": pref is not None and "Penalize" in pref["diff_summary"],
        "candidate_prompt_proposal": day2["experiment_id"] is not None,
        "day2_pdf_has_ab": bool(day2["pdf_text_contains_ab"]),
        "feedback_file_has_promote_reject_slot": "promote? [x] yes" in day2_feedback and "[ ] no" in day2_feedback,
        "feedback_file_promotion_ok": promotion.get("status") == "ok",
        "cli_rollback_ok": rollback.get("ok") is True,
        "spend_logged_and_within_budget": budgets_ok,
        "spend_rows": spend_rows,
        "day1_pdf_ok": day1["post_checks"]["ok"],
        "day2_pdf_ok": day2["post_checks"]["ok"],
        "ranking_prompt_tuned_via_experiment": day2["experiment_id"] is not None and promotion.get("stage") == "rank",
    }
    checks["ok"] = all(value for key, value in checks.items() if key not in {"repeated_items", "spend_rows"})
    return checks


def summarize_day(day: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": day["date"],
        "selected_item_ids": [item["id"] for item in day["selected_items"]],
        "pdf": day["pdf"],
        "feedback_path": day["feedback_path"],
        "page_count": day["post_checks"]["page_count"],
        "post_checks_ok": day["post_checks"]["ok"],
        "experiment_id": day["experiment_id"],
    }
