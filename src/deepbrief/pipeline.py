from __future__ import annotations

import json

from deepbrief.config import Config


def run_pipeline(config: Config, *, date_override: str | None = None, fixtures: str | None = None) -> None:
    if fixtures:
        from deepbrief.soak import D1, reset_soak_state, run_fixture_day, summarize_day
        from deepbrief.db import init_database
        from pathlib import Path

        if not date_override:
            raise RuntimeError("fixture mode requires --date")
        conn = init_database(config.state_db, config.migrations_dir)
        if date_override == D1:
            reset_soak_state(config, conn)
        day = run_fixture_day(config, conn, date_value=date_override, fixtures_dir=Path(fixtures))
        conn.close()
        print(json.dumps({"status": "ok", "mode": "fixtures", **summarize_day(day)}, indent=2, sort_keys=True))
        return

    from deepbrief.notify import notify_ready, open_pdf
    from deepbrief.render import m7_gate

    result = m7_gate(config, date_override=date_override)
    pdf = result["pdf"]
    notification = notify_ready(pdf)
    opened = open_pdf(pdf)
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": "fixtures" if fixtures else "live-artifact-run",
                "pdf": pdf,
                "notification": notification,
                "opened": opened,
            },
            indent=2,
            sort_keys=True,
        )
    )
