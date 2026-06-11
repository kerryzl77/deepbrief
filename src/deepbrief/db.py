from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path


class DatabaseError(RuntimeError):
    pass


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def apply_migrations(conn: sqlite3.Connection, migrations_dir: Path) -> list[str]:
    if not migrations_dir.exists():
        raise DatabaseError(f"missing migrations directory: {migrations_dir}")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}
    newly_applied: list[str] = []
    for migration in sorted(migrations_dir.glob("*.sql")):
        version = migration.name
        if version in applied:
            continue
        sql = migration.read_text(encoding="utf-8")
        try:
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise DatabaseError(f"migration failed: {version}: {exc}") from exc
        newly_applied.append(version)
    return newly_applied


def table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def init_database(db_path: Path, migrations_dir: Path) -> sqlite3.Connection:
    conn = connect(db_path)
    apply_migrations(conn, migrations_dir)
    return conn


def ensure_run(conn: sqlite3.Connection, run_date: str | None = None) -> int:
    value = run_date or date.today().isoformat()
    conn.execute(
        "INSERT INTO runs(date, spend_usd, duration_s) VALUES (?, 0, 0) "
        "ON CONFLICT(date) DO NOTHING",
        (value,),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM runs WHERE date = ?", (value,)).fetchone()
    if row is None:
        raise DatabaseError(f"failed to create run row for {value}")
    return int(row["id"])


def log_spend(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    stage: str,
    model: str,
    cost_usd: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    conn.execute(
        "INSERT INTO spend_log(run_id, stage, model, cost_usd, input_tokens, output_tokens) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, stage, model, cost_usd, input_tokens, output_tokens),
    )
    conn.execute("UPDATE runs SET spend_usd = spend_usd + ? WHERE id = ?", (cost_usd, run_id))
    conn.commit()
