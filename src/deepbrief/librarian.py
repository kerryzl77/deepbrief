from __future__ import annotations

import re
import sqlite3


def upsert_concepts(conn: sqlite3.Connection, run_id: int, concepts: list[dict[str, str]]) -> dict[str, int]:
    inserted = 0
    existing = 0
    for concept in concepts:
        name = concept["name"].strip()
        slug = slugify(name)
        summary = concept["summary"].strip()
        before = conn.execute("SELECT id FROM concepts WHERE slug = ?", (slug,)).fetchone()
        conn.execute(
            """
            INSERT INTO concepts(name, slug, summary, created_run_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
              summary = excluded.summary
            """,
            (name, slug, summary, run_id),
        )
        if before is None:
            inserted += 1
        else:
            existing += 1
    conn.commit()
    return {"inserted": inserted, "existing": existing}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "concept"
