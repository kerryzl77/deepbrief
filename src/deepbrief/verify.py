from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from deepbrief.config import Config
from deepbrief.db import ensure_run, init_database
from deepbrief.librarian import upsert_concepts


CODE_CITATION = re.compile(r"(?P<path>[\w./-]+\.[A-Za-z0-9]+):(?P<line>\d+)")


def m4_fixture_gate(config: Config) -> None:
    repo = config.repo_root / "tests" / "fixtures" / "minirepo"
    if not repo.exists():
        raise RuntimeError(f"missing minirepo fixture: {repo}")

    corrupted = """# Fixture Code Dive

## Walkthrough

| step | file:line | symbol | what happens |
|---|---|---|---|
| 1 | `app.py:4` | `PROMPT_TEMPLATE` | Loads the prompt template. |
| 2 | `app.py:999` | `execute_tool` | Corrupted citation deliberately points beyond EOF. |
| 3 | `prompts/agent_prompt.md:1` | `System` | Prompt file is available to the runner. |

## Sources & citations

- `app.py:4` contains `PROMPT_TEMPLATE`.
- `app.py:999` is the planted bad citation.
- `prompts/agent_prompt.md:1` contains the prompt heading.
"""
    initial = verify_markdown_citations(corrupted, repo)
    revised_markdown = strike_invalid_citations(corrupted, initial["path_checks"])
    revised = verify_markdown_citations(revised_markdown, repo, ignore_struck=True)

    conn = init_database(config.state_db, config.migrations_dir)
    run_id = ensure_run(conn, "m4-fixtures")
    concepts = [
        {
            "name": "Prompt template",
            "summary": "A versioned instruction artifact loaded by the fixture runner.",
        },
        {
            "name": "Tool contract",
            "summary": "A narrow function boundary that keeps agent actions explicit.",
        },
        {
            "name": "Agent loop",
            "summary": "A small observe-plan-act cycle used by the fixture implementation.",
        },
    ]
    first = upsert_concepts(conn, run_id, concepts)
    second = upsert_concepts(conn, run_id, concepts)
    total = int(conn.execute("SELECT COUNT(*) AS n FROM concepts").fetchone()["n"])
    conn.close()

    result = {
        "status": "ok",
        "fixture_repo": str(repo),
        "corrupt_citation_caught": not initial["ok"],
        "initial_verification": initial,
        "revision_loop_fired": revised_markdown != corrupted,
        "revised_verification": revised,
        "concept_upserts": {
            "first": first,
            "second": second,
            "idempotent": first["inserted"] >= 0 and second["inserted"] == 0,
            "total_concepts": total,
        },
    }
    if not result["corrupt_citation_caught"] or not revised["ok"] or not result["concept_upserts"]["idempotent"]:
        result["status"] = "failed"
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "ok":
        raise RuntimeError("M4 fixture gate failed")


def verify_markdown_citations(markdown: str, repo: Path, *, ignore_struck: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        if ignore_struck and "~~" in line:
            continue
        for match in CODE_CITATION.finditer(line):
            rel = match.group("path")
            line_no = int(match.group("line"))
            path = repo / rel
            exists = path.exists()
            line_ok = False
            if exists:
                line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
                line_ok = 1 <= line_no <= line_count
            symbol = ""
            symbol_match = re.search(r"`([A-Za-z_][A-Za-z0-9_]{2,})`", line)
            if symbol_match:
                symbol = symbol_match.group(1)
            symbol_ok = True if not symbol else exists and symbol in path.read_text(encoding="utf-8", errors="replace")
            checks.append(
                {
                    "path": rel,
                    "line": line_no,
                    "exists": exists,
                    "line_ok": line_ok,
                    "symbol": symbol,
                    "symbol_ok": symbol_ok,
                }
            )
    return {
        "ok": bool(checks) and all(check["exists"] and check["line_ok"] and check["symbol_ok"] for check in checks),
        "path_checks": checks,
        "checked_count": len(checks),
        "failed_count": len(
            [check for check in checks if not (check["exists"] and check["line_ok"] and check["symbol_ok"])]
        ),
    }


def strike_invalid_citations(markdown: str, checks: list[dict[str, Any]]) -> str:
    bad = {f"{check['path']}:{check['line']}" for check in checks if not (check["exists"] and check["line_ok"])}
    revised_lines: list[str] = []
    for line in markdown.splitlines():
        if any(citation in line for citation in bad):
            revised_lines.append(f"~~{line}~~  <!-- struck by verifier: invalid citation -->")
        else:
            revised_lines.append(line)
    return "\n".join(revised_lines) + "\n"
