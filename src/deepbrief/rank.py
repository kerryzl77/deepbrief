from __future__ import annotations

import asyncio
import json
import os
from datetime import date
from typing import Any

from deepbrief.config import Config
from deepbrief.db import ensure_run, init_database, log_spend
from deepbrief.llm import BudgetTracker, run_text_stage


def main(config: Config) -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is required for M1 rank because ranking is an LLM stage. "
            "Set it in the environment or an untracked .env file."
        )

    conn = init_database(config.state_db, config.migrations_dir)
    rows = conn.execute(
        """
        SELECT id, source_id, url, title, type, published_at
        FROM items
        WHERE status IN ('new', 'queued') AND score IS NULL
        ORDER BY published_at DESC NULLS LAST, discovered_at DESC
        LIMIT 80
        """
    ).fetchall()
    candidates = diversify_candidates([dict(row) for row in rows], limit=12, per_source=3)
    if not candidates:
        candidates = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, source_id, url, title, type, published_at, score, score_reasons
                FROM items
                WHERE status IN ('new', 'queued')
                ORDER BY score DESC NULLS LAST, published_at DESC NULLS LAST
                LIMIT 12
                """
            )
        ]
    if not candidates:
        raise RuntimeError("no unprocessed items available; run make scout first")

    if rows:
        scores = asyncio.run(score_candidates(config, candidates))
        for scored in scores["items"]:
            conn.execute(
                "UPDATE items SET score = ?, score_reasons = ? WHERE id = ?",
                (float(scored["score"]), str(scored["reason"]), str(scored["id"])),
            )
        run_id = ensure_run(conn, date.today().isoformat())
        usage = scores.get("_usage", {})
        log_spend(
            conn,
            run_id=run_id,
            stage="rank",
            model=config.model_for_tier("fast"),
            cost_usd=float(usage.get("cost_usd", 0.0)),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
        )

    plan = build_plan(conn)
    conn.close()
    print(json.dumps(plan, indent=2, sort_keys=True))
    if not plan["deep_target"] or len(plan["skims"]) < 4:
        raise RuntimeError("rank plan must include a deep target and at least 4 skims")


async def score_candidates(config: Config, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    profile = config.profile_path.read_text(encoding="utf-8")[:2000]
    preferences = config.preferences_path.read_text(encoding="utf-8")[:2000]
    compact_items = [
        {
            "id": item["id"],
            "source": item["source_id"],
            "type": item["type"],
            "title": item["title"],
            "published_at": item["published_at"],
        }
        for item in candidates
    ]
    prompt = json.dumps(
        {
            "profile": profile,
            "preferences": preferences,
            "items": compact_items,
            "instructions": (
                "Score every listed item from 0 to 100 for today's DeepBrief. "
                "Return exactly one object with an items array. Each result id must match an input id. "
                "Reason must be one concise sentence, no markdown."
            ),
        },
        ensure_ascii=True,
    )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "items": {
                "type": "array",
                "minItems": 1,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "score": {"type": "number"},
                        "reason": {"type": "string"},
                    },
                    "required": ["id", "score", "reason"],
                },
            }
        },
        "required": ["items"],
    }
    tracker = BudgetTracker(config.run_budget_usd)
    result = await run_text_stage(
        config,
        stage="rank",
        prompt=prompt,
        system_prompt_path=config.prompts_dir / "rank.md",
        tier="fast",
        output_schema=schema,
        budget=tracker,
    )
    if not result.success:
        raise RuntimeError(f"rank LLM stage failed: subtype={result.subtype} error={result.error}")
    structured = result.structured
    if not isinstance(structured, dict) or not isinstance(structured.get("items"), list):
        try:
            structured = json.loads(result.text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("rank LLM did not return structured score JSON") from exc
    structured["_usage"] = {
        "cost_usd": result.cost_usd,
        "input_tokens": sum(int(v.get("input_tokens", 0)) for v in result.model_usage.values())
        if result.model_usage
        else 0,
        "output_tokens": sum(int(v.get("output_tokens", 0)) for v in result.model_usage.values())
        if result.model_usage
        else 0,
    }
    return structured


def diversify_candidates(
    candidates: list[dict[str, Any]], *, limit: int, per_source: int
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for item in candidates:
        source = str(item["source_id"])
        if counts.get(source, 0) >= per_source:
            continue
        selected.append(item)
        counts[source] = counts.get(source, 0) + 1
        if len(selected) >= limit:
            return selected
    for item in candidates:
        if item in selected:
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def build_plan(conn: Any) -> dict[str, Any]:
    queued = conn.execute(
        """
        SELECT id FROM items
        WHERE status = 'queued'
        ORDER BY score DESC NULLS LAST, published_at DESC NULLS LAST
        LIMIT 7
        """
    ).fetchall()
    if not queued:
        top = conn.execute(
            """
            SELECT id FROM items
            WHERE status = 'new' AND score IS NOT NULL
            ORDER BY score DESC, published_at DESC NULLS LAST
            LIMIT 7
            """
        ).fetchall()
        for row in top:
            conn.execute("UPDATE items SET status = 'queued' WHERE id = ?", (row["id"],))
        conn.commit()

    selected = [
        dict(row)
        for row in conn.execute(
            """
            SELECT id, source_id, url, title, type, published_at, score, score_reasons
            FROM items
            WHERE status = 'queued'
            ORDER BY score DESC NULLS LAST, published_at DESC NULLS LAST
            LIMIT 7
            """
        )
    ]
    deep_target = selected[0] if selected else None
    skims = selected[1:7]
    return {
        "date": date.today().isoformat(),
        "deep_target": deep_target,
        "skims": skims,
    }
    plan = {
        "date": date.today().isoformat(),
        "deep_target": None,
        "skims": [],
        "status": "not_implemented",
        "message": "M1 rank is scaffolded but LLM scoring is not implemented yet.",
    }
    print(json.dumps(plan, indent=2))
