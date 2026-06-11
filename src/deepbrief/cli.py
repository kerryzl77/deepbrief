from __future__ import annotations

import argparse
import sys

from deepbrief import __version__
from deepbrief.config import Config, ConfigError
from deepbrief.db import DatabaseError
from deepbrief.doctor import run_doctor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepbrief")
    parser.add_argument("--version", action="version", version=f"deepbrief {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="Validate the local scaffold and runtime prerequisites.")
    sub.add_parser("scout", help="Fetch source metadata and upsert newly discovered items.")
    sub.add_parser("rank", help="Score unprocessed items and emit today's plan JSON.")
    verify = sub.add_parser("verify", help="Run verification gates.")
    verify_sub = verify.add_subparsers(dest="verify_command")
    verify_sub.add_parser("m4-fixtures", help="Run M4 verifier/librarian fixture gate.")

    analyst = sub.add_parser("analyst", help="Run analyst stages.")
    analyst_sub = analyst.add_subparsers(dest="analyst_command")
    article = analyst_sub.add_parser("article", help="Run article/paper deep-dive analyst.")
    article.add_argument("--url", required=True)
    article.add_argument("--title")
    article.add_argument("--date")
    code = analyst_sub.add_parser("code", help="Run code-release deep-dive analyst.")
    code.add_argument("--repo", required=True, help="owner/repo")
    code.add_argument("--from-tag")
    code.add_argument("--to-tag")
    code.add_argument("--date")

    run = sub.add_parser("run", help="Run the daily pipeline.")
    run.add_argument("--date", help="Override run date as YYYY-MM-DD.")
    run.add_argument("--fixtures", help="Use frozen fixtures instead of live network ingestion.")

    feedback = sub.add_parser("feedback", help="Open today's feedback file.")
    feedback.add_argument("--date", help="Date whose feedback file should be opened.")
    feedback.add_argument("feedback_command", nargs="?")

    rate = sub.add_parser("rate", help="Record one item rating.")
    rate.add_argument("item_id")
    rate.add_argument("value", choices=["up", "down"])
    rate.add_argument("note", nargs="?")

    prompts = sub.add_parser("prompts", help="Manage prompt versions.")
    prompt_sub = prompts.add_subparsers(dest="prompt_command")
    promote = prompt_sub.add_parser("promote", help="Promote a candidate prompt.")
    promote.add_argument("stage")
    rollback = prompt_sub.add_parser("rollback", help="Rollback the active prompt to its parent.")
    rollback.add_argument("stage")

    tuner = sub.add_parser("tuner", help="Run tuner gates.")
    tuner_sub = tuner.add_subparsers(dest="tuner_command")
    tuner_sub.add_parser("m6-fixtures", help="Run M6 tuner/A-B fixture gate.")

    render = sub.add_parser("render", help="Compose and render briefs.")
    render_sub = render.add_subparsers(dest="render_command")
    render_m7 = render_sub.add_parser("m7", help="Run M7 compose/render gate.")
    render_m7.add_argument("--date")

    soak = sub.add_parser("soak", help="Run soak gates.")
    soak_sub = soak.add_subparsers(dest="soak_command")
    soak_sub.add_parser("m9a", help="Run simulated two-day fixture soak gate.")

    sub.add_parser("install", help="Install the user launchd job.")
    sub.add_parser("uninstall", help="Unload and remove the user launchd job.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "doctor"

    try:
        config = Config.load()
        if command == "doctor":
            run_doctor(config)
        elif command == "scout":
            from deepbrief.scout import main as scout_main

            scout_main(config)
        elif command == "rank":
            from deepbrief.rank import main as rank_main

            rank_main(config)
        elif command == "verify" and args.verify_command == "m4-fixtures":
            from deepbrief.verify import m4_fixture_gate

            m4_fixture_gate(config)
        elif command == "analyst" and args.analyst_command == "article":
            from deepbrief.analyst import article_deep_dive

            article_deep_dive(config, url=args.url, title=args.title, date_override=args.date)
        elif command == "analyst" and args.analyst_command == "code":
            from deepbrief.analyst import code_deep_dive

            code_deep_dive(
                config,
                repo=args.repo,
                from_tag=args.from_tag,
                to_tag=args.to_tag,
                date_override=args.date,
            )
        elif command == "run":
            from deepbrief.pipeline import run_pipeline

            run_pipeline(config, date_override=args.date, fixtures=args.fixtures)
        elif command == "feedback":
            from deepbrief.feedback import m5_fixture_gate, open_feedback

            if args.feedback_command == "m5-fixtures":
                m5_fixture_gate(config)
            else:
                open_feedback(config, date_override=args.date)
        elif command == "rate":
            from deepbrief.feedback import record_rating

            record_rating(config, args.item_id, args.value, args.note)
        elif command == "prompts" and args.prompt_command == "promote":
            from deepbrief.tuner import promote_prompt

            promote_prompt(config, args.stage)
        elif command == "prompts" and args.prompt_command == "rollback":
            from deepbrief.tuner import rollback_prompt

            rollback_prompt(config, args.stage)
        elif command == "tuner" and args.tuner_command == "m6-fixtures":
            from deepbrief.tuner import m6_fixture_gate

            m6_fixture_gate(config)
        elif command == "render" and args.render_command == "m7":
            from deepbrief.render import m7_gate

            m7_gate(config, date_override=args.date)
        elif command == "soak" and args.soak_command == "m9a":
            from deepbrief.soak import m9a_gate

            m9a_gate(config)
        elif command == "install":
            from deepbrief.notify import install_launchd

            install_launchd(config)
        elif command == "uninstall":
            from deepbrief.notify import uninstall_launchd

            uninstall_launchd(config)
        else:
            parser.error("unknown or incomplete command")
    except (ConfigError, DatabaseError, RuntimeError, ValueError) as exc:
        print(f"deepbrief: error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
