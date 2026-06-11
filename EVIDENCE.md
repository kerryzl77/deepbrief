# DeepBrief Evidence

This file is reserved for milestone gate evidence from `DEEPBRIEF_SPEC.md` §14.

Append command output here as M0–M9b are executed.

## M0 - Scaffold

Documentation consulted before implementing the Claude Agent SDK wrapper and model config:

- https://platform.claude.com/docs/en/agent-sdk/python
- https://code.claude.com/docs/en/agent-sdk/permissions
- https://code.claude.com/docs/en/agent-sdk/hooks
- https://code.claude.com/docs/en/agent-sdk/structured-outputs
- https://code.claude.com/docs/en/agent-sdk/cost-tracking
- https://platform.claude.com/docs/en/about-claude/models/overview
- https://docs.github.com/en/rest/releases/releases
- https://info.arxiv.org/help/api/user-manual.html

Initial gate run after scaffold failed inside the managed filesystem sandbox because `uv` needed
to read its cache under `~/.cache/uv`:

```sh
$ make doctor
error: failed to open file `/Users/liuzikai/.cache/uv/sdists-v9/.git`: Operation not permitted (os error 1)
make: *** [doctor] Error 2
```

The exact gate command was re-run with approved cache access:

```sh
$ make doctor
DeepBrief M0 doctor: ok
repo: /Users/liuzikai/Documents/GitHub/deepbrief
seed files: 14 present
sources: 5 feeds, 5 repos, arxiv configured
migrations applied in temp db: 001_initial.sql
llm: budget wrapper dry-run recorded cost 0.0000
llm: code analyst permission_mode=dontAsk
llm: code analyst mutating/network tools denied
llm: bash PreToolUse allowlist enforced
```

M0 decision notes:

- Scaffolded the repo layout from §13, seed config/source/profile/preference/prompt/template files,
  SQLite migration, CLI command surface, and launchd template.
- Kept `repo_backend` as the single implemented enum value `claude_agent_sdk`; `codex_exec` is not
  implemented.
- `llm.py` exposes `run_text_stage(...)` and `run_repo_stage(...)`, records budget accounting in
  a `BudgetTracker`, handles SDK budget result subtypes, and centralizes code-analyst lockdown
  options plus the read-only Bash `PreToolUse` hook.

## M1 - Scout + Rank (Live)

Implementation notes and iterations:

- Implemented live scout using official RSS/Atom, GitHub REST Releases, and arXiv API calls.
- Implemented deterministic item IDs and SQLite `INSERT OR IGNORE` upserts for idempotency.
- Installed the required Claude Agent SDK dependency:

```sh
$ uv sync
Resolved 34 packages in 932ms
Installed 32 packages in 37ms
 + claude-agent-sdk==0.2.97
```

- Initial rank attempts failed because text-only stages used `disallowed_tools=["*"]`, which also
  blocked the SDK's structured-output mechanism. A minimal smoke query failed with
  `error_max_structured_output_retries`; after changing text stages to `allowed_tools=[]`,
  `permission_mode="dontAsk"`, and no blanket deny list, the same smoke query returned:

```sh
subtype success
is_error False
result Done! ✓
structured {'ok': True}
```

- The broad arXiv query timed out or returned HTTP 429. Replaced it with the verified bounded
  official API query `(cat:cs.CL OR cat:cs.AI) AND all:agent`.
- Blog RSS URLs that returned 404 were substituted to verified official source pages and logged
  in scout output.

Gate command:

```sh
$ make scout
{
  "added_count": 10,
  "duplicate_count": 130,
  "fetched_items": 140,
  "status": "ok",
  "total_items": 140,
  "source_log": [
    {"id": "anthropic_news", "status": "substituted", "used_url": "https://www.anthropic.com/news"},
    {"id": "anthropic_engineering", "status": "substituted", "used_url": "https://www.anthropic.com/engineering"},
    {"id": "openai_news", "status": "verified", "items": 30},
    {"id": "cursor_blog", "status": "substituted", "used_url": "https://cursor.com/blog"},
    {"id": "ramp_engineering", "status": "substituted", "used_url": "https://ramp.com/blog"},
    {"id": "arxiv_agents", "status": "verified", "items": 10},
    {"id": "openai_codex", "status": "verified", "items": 20},
    {"id": "anthropic_claude_code", "status": "verified", "items": 20},
    {"id": "openai_agents_python", "status": "verified", "items": 20},
    {"id": "anthropic_claude_agent_sdk_python", "status": "verified", "items": 20},
    {"id": "e2b", "status": "verified", "items": 20}
  ]
}
```

Immediate rerun:

```sh
$ make scout
{
  "added_count": 0,
  "duplicate_count": 140,
  "fetched_items": 140,
  "status": "ok",
  "total_items": 140
}
```

Rank gate:

```sh
$ make rank
{
  "date": "2026-06-11",
  "deep_target": {
    "id": "item_2542941d7b614f34",
    "score": 82.0,
    "score_reasons": "Claude Agent SDK directly core to multi-agent orchestration, Anthropic, and latest version.",
    "source_id": "anthropic_claude_agent_sdk_python",
    "title": "v0.2.97",
    "type": "repo_release",
    "url": "https://github.com/anthropics/claude-agent-sdk-python/releases/tag/v0.2.97"
  },
  "skims": [
    {"id": "item_a6307109efa14ec5", "score": 76.0, "title": "v2.1.173"},
    {"id": "item_009f2c8b296b576a", "score": 76.0, "title": "v0.2.96"},
    {"id": "item_f4a4179ae28324e9", "score": 70.0, "title": "e2b@2.29.1"},
    {"id": "item_6112242667f0a596", "score": 70.0, "title": "@e2b/python-sdk@2.28.1"},
    {"id": "item_524220ced03d2da5", "score": 65.0, "title": "0.140.0-alpha.11"},
    {"id": "item_00f09b7427ed574b", "score": 62.0, "title": "0.140.0-alpha.10"}
  ]
}
```

## M2 - Article Deep Dive

Pinned article URL:

- https://www.anthropic.com/engineering/building-effective-agents

Initial run produced a partial artifact that stopped after the Mental model. The prompt was
tightened to require a compact complete replacement and to reduce source excerpt size so output
budget is reserved for all required sections.

Gate command:

```sh
$ make article URL=https://www.anthropic.com/engineering/building-effective-agents
{
  "deepdive_path": "/Users/liuzikai/DeepBrief/2026-06-11/m2_article/deepdive.md",
  "schema_lint": {
    "citation_count": 4,
    "errors": [],
    "headings_present": true,
    "ok": true,
    "pseudocode_lines": 40
  },
  "schema_lint_path": "/Users/liuzikai/DeepBrief/2026-06-11/m2_article/schema_lint.json",
  "status": "ok",
  "title": "Building effective agents",
  "url": "https://www.anthropic.com/engineering/building-effective-agents",
  "usage": {
    "cost_usd": 0.2165609,
    "input_tokens": 0,
    "output_tokens": 0
  }
}
```

## M3 - Code Deep Dive + Lockdown Proof

Pinned release:

- Repository: `anthropics/claude-agent-sdk-python`
- Range: `v0.2.96` (`afe320b609598ae4f7b7c7824ca0d3a4f4b63b46`) to
  `v0.2.97` (`5e6d6a075f078843cb2a23a1dd8a7e8503961a6f`)
- The diff did not touch prompt files, so the prompt-excerpt requirement is not applicable for
  this release.

Iterations:

- First code analyst output cited bare filenames; verifier failed path checks. Added a
  mechanical citation repair pass that maps bare or package-relative filenames only when they
  uniquely resolve to an existing repo path, then re-ran the gate.
- The planted write instruction did not mutate the checkout. The lockdown proof records an
  explicit `PreToolUse` Bash hook denial for `touch LOCKDOWN_SHOULD_NOT_CHANGE.txt`, and
  `git status --short` was unchanged before/after.

Gate command:

```sh
$ PYTHONPATH=src uv run --no-sync python -m deepbrief.cli analyst code --repo anthropics/claude-agent-sdk-python --from-tag v0.2.96 --to-tag v0.2.97
{
  "deepdive_path": "/Users/liuzikai/DeepBrief/2026-06-11/m3_code/deepdive.md",
  "status": "ok",
  "usage": {
    "cost_usd": 0.20936280000000002,
    "input_tokens": 0,
    "output_tokens": 0
  },
  "verification": {
    "repo": "anthropics/claude-agent-sdk-python",
    "checkout": "/Users/liuzikai/.deepbrief/repos/anthropics__claude-agent-sdk-python",
    "from_tag": "v0.2.96",
    "from_sha": "afe320b609598ae4f7b7c7824ca0d3a4f4b63b46",
    "to_tag": "v0.2.97",
    "to_sha": "5e6d6a075f078843cb2a23a1dd8a7e8503961a6f",
    "prompt_touched": false,
    "cited_path_count": 14,
    "cited_symbol_count": 7,
    "path_pass_rate": 1.0,
    "symbol_pass_rate": 1.0,
    "lockdown": {
      "audit_events": [
        {
          "command": "touch LOCKDOWN_SHOULD_NOT_CHANGE.txt",
          "decision": "deny",
          "tool": "Bash"
        }
      ],
      "denied_bash_commands": 1,
      "git_status_before": "",
      "git_status_after": "",
      "unchanged": true
    }
  },
  "verification_path": "/Users/liuzikai/DeepBrief/2026-06-11/m3_code/verification.json"
}
```

## M4 - Verify + Librarian (Fixtures)

Fixture repository:

- `tests/fixtures/minirepo`
- Tags: `v0.1.0` and `v0.2.0`

Gate command:

```sh
$ make m4
{
  "concept_upserts": {
    "first": {
      "existing": 0,
      "inserted": 3
    },
    "idempotent": true,
    "second": {
      "existing": 3,
      "inserted": 0
    },
    "total_concepts": 3
  },
  "corrupt_citation_caught": true,
  "fixture_repo": "/Users/liuzikai/Documents/GitHub/deepbrief/tests/fixtures/minirepo",
  "initial_verification": {
    "checked_count": 6,
    "failed_count": 2,
    "ok": false
  },
  "revised_verification": {
    "checked_count": 4,
    "failed_count": 0,
    "ok": true
  },
  "revision_loop_fired": true,
  "status": "ok"
}
```

## M5 - Feedback Loop (Fixtures)

Gate command:

```sh
$ make m5
{
  "filled_feedback_path": "/Users/liuzikai/DeepBrief/m5-fixtures/feedback_filled.md",
  "negative_rating_shifted_rank": true,
  "preference_revision_recorded": true,
  "preferences_path": "/Users/liuzikai/Documents/GitHub/deepbrief/preferences.md",
  "run_id": 3,
  "score_before": {
    "fixture_agent_release": 72.0,
    "fixture_model_hype": 72.0
  },
  "score_after": {
    "fixture_agent_release": 77.0,
    "fixture_model_hype": 62.0
  },
  "score_shifts": {
    "fixture_agent_release": 5.0,
    "fixture_model_hype": -10.0
  },
  "signals": {
    "preference_revision_id": 1,
    "preference_bullet": "- 2026-06-11: Penalize thin model-release hype; prefer code-grounded agent harnesses, sandboxing details, and prompt/version diffs.",
    "diff_summary": "--- preferences.md.before\n+++ preferences.md.after\n@@ -1 +1,2 @@\n # Learned preferences (machine-maintained - edit freely)\n+- 2026-06-11: Penalize thin model-release hype; prefer code-grounded agent harnesses, sandboxing details, and prompt/version diffs.",
    "ratings": [
      {"item_id": "fixture_agent_release", "value": "up"},
      {"item_id": "fixture_model_hype", "value": "down"}
    ]
  },
  "status": "ok",
  "template_path": "/Users/liuzikai/DeepBrief/m5-fixtures/feedback_template.md"
}
```

## M6 - Tuner + A/B (Fixtures)

Gate command:

```sh
$ make m6
{
  "active_version": 1,
  "candidate_version": 2,
  "diff_bounds": {
    "base_lines": 7,
    "changed_lines": 1,
    "ok": true,
    "ratio": 0.14285714285714285
  },
  "experiment_id": 1,
  "feedback_path": "/Users/liuzikai/DeepBrief/m6-fixtures/feedback.md",
  "invariants": {
    "ok": true,
    "violations": []
  },
  "judge_scores": [
    {"fixture_id": "replay-1", "winner": "candidate"},
    {"fixture_id": "replay-2", "winner": "candidate"},
    {"fixture_id": "replay-3", "winner": "candidate"}
  ],
  "pipeline_report_path": "/Users/liuzikai/DeepBrief/m6-fixtures/pipeline_report.md",
  "stage": "skim",
  "status": "ok"
}
```

Promotion command:

```sh
$ PYTHONPATH=src uv run --no-sync python -m deepbrief.cli prompts promote skim
{"status": "ok", "action": "promote", "stage": "skim", "active_version": 2}
```

Rollback command:

```sh
$ PYTHONPATH=src uv run --no-sync python -m deepbrief.cli prompts rollback skim
{"status": "ok", "action": "rollback", "stage": "skim", "active_version": 1}
```

Post-rollback prompt version state:

```sh
{'stage': 'skim', 'version': 1, 'parent_version': None, 'status': 'active'}
{'stage': 'skim', 'version': 2, 'parent_version': 1, 'status': 'retired'}
```

## M7 - Compose + Render (Blocked)

M7 requires the fixed renderer stack from §5: Mermaid CLI (`mmdc`) -> `pandoc` -> `typst`, plus
`pdftoppm` for rasterized PDF QA. The local machine does not currently have these binaries on
`PATH`.

Commands run:

```sh
$ which pandoc
pandoc not found

$ which typst
typst not found

$ which mmdc
mmdc not found

$ which pdftoppm
pdftoppm not found
```

Blocked gate: M7. Unlock needed: install/provide `pandoc` >= 3.1, `typst`, Mermaid CLI (`mmdc`),
and `pdftoppm` on `PATH`, or explicitly approve installation of those system tools. No alternate
renderer was used because that would violate the fixed stack decision in §5.

## M7 - Compose + Render (Passed)

Installed the fixed renderer stack with Homebrew after approval:

```sh
$ brew install pandoc typst poppler mermaid-cli
🍺  /opt/homebrew/Cellar/pandoc/3.9.0.2
🍺  /opt/homebrew/Cellar/typst/0.14.2
🍺  /opt/homebrew/Cellar/poppler/26.06.0
🍺  /opt/homebrew/Cellar/mermaid-cli/11.15.0
```

Mermaid CLI also required a Puppeteer browser payload. Installed the exact browser version it
reported into a repo-local ignored cache:

```sh
$ PUPPETEER_CACHE_DIR=/Users/liuzikai/Documents/GitHub/deepbrief/.cache/puppeteer npx puppeteer browsers install chrome-headless-shell@148.0.7778.97
chrome-headless-shell@148.0.7778.97 /Users/liuzikai/Documents/GitHub/deepbrief/.cache/puppeteer/chrome-headless-shell/mac_arm-148.0.7778.97/chrome-headless-shell-mac-arm64/chrome-headless-shell
```

Iterations:

- First M7 run failed because `mmdc` could not find Chrome. Fixed by setting
  `PUPPETEER_CACHE_DIR` for renderer subprocesses.
- Second M7 run failed because Pandoc emitted `#horizontalrule`, which Typst 0.14.2 does not
  define. Fixed by post-processing generated Typst to `#line(length: 100%)`.

Gate command:

```sh
$ make m7
{
  "brief_md": "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/brief.md",
  "diagrams": {
    "count": 3,
    "svg_paths": [
      "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/diagrams/diagram_01.svg",
      "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/diagrams/diagram_02.svg",
      "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/diagrams/diagram_03.svg"
    ]
  },
  "pdf": "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/brief.pdf",
  "post_checks": {
    "code_overflow_check": "typst compile completed without layout errors",
    "fonts_embedded": true,
    "math_text_present": true,
    "ok": true,
    "page_count": 8,
    "page_count_ok": true,
    "pdf_nonzero": true,
    "pdf_size_bytes": 240409,
    "rasterized_all_pages": true,
    "rasterized_pages": 8,
    "svg_count": 3,
    "svg_files_exist": true,
    "toc_link_markers_present": true,
    "toc_outline_present": true,
    "typst_references_all_svgs": true
  },
  "status": "ok",
  "tool_versions": {
    "mmdc": "11.15.0",
    "pandoc": "pandoc 3.9.0.2",
    "pdfinfo": "pdfinfo version 26.06.0",
    "pdftoppm": "pdftoppm version 26.06.0",
    "typst": "typst 0.14.2 (unknown hash)"
  },
  "typst": "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/brief.typ"
}
```

## M8 - Schedule + Notify

Direct run preflight:

```sh
$ PYTHONPATH=src uv run --no-sync python -m deepbrief.cli run
{
  "status": "ok",
  "pdf": "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/brief.pdf",
  "notification": {
    "returncode": 0,
    "stderr": ""
  },
  "opened": {
    "returncode": 0,
    "stderr": ""
  }
}
```

Install gate:

```sh
$ make install
{"action": "install", "label": "com.liuzikai.deepbrief", "plist": "/Users/liuzikai/Library/LaunchAgents/com.liuzikai.deepbrief.plist", "status": "ok", "stderr_log": "/Users/liuzikai/.deepbrief/logs/deepbrief.err.log", "stdout_log": "/Users/liuzikai/.deepbrief/logs/deepbrief.out.log"}
```

Kickstart gate:

```sh
$ launchctl kickstart -k gui/$(id -u)/com.liuzikai.deepbrief
# exit code 0
```

Launchd state after completion:

```sh
$ launchctl print gui/$(id -u)/com.liuzikai.deepbrief
state = not running
runs = 1
last exit code = 0
event trigger = StartCalendarInterval Hour 6 Minute 15
```

Launchd stdout log key output:

```sh
$ tail -n 160 /Users/liuzikai/.deepbrief/logs/deepbrief.out.log
{
  "status": "ok",
  "pdf": "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/brief.pdf",
  "post_checks": {
    "ok": true,
    "page_count": 8,
    "rasterized_pages": 8,
    "fonts_embedded": true,
    "toc_outline_present": true,
    "toc_link_markers_present": true
  }
}
{
  "mode": "live-artifact-run",
  "notification": {"returncode": 0, "stderr": ""},
  "opened": {"returncode": 0, "stderr": ""},
  "pdf": "/Users/liuzikai/DeepBrief/2026-06-11/m7_render/brief.pdf",
  "status": "ok"
}
```

Launchd stderr log:

```sh
$ tail -n 80 /Users/liuzikai/.deepbrief/logs/deepbrief.err.log
# empty
```

Uninstall gate:

```sh
$ make uninstall
{"action": "uninstall", "label": "com.liuzikai.deepbrief", "plist_removed": true, "status": "ok"}

$ test ! -f /Users/liuzikai/Library/LaunchAgents/com.liuzikai.deepbrief.plist && echo plist_removed
plist_removed

$ launchctl print gui/$(id -u)/com.liuzikai.deepbrief
Bad request.
Could not find service "com.liuzikai.deepbrief" in domain for user gui: 501
```

## M9a - Simulated Two-Day Soak (Fixtures)

Gate command:

The exact fixture run commands named in §14 also pass:

```sh
$ PYTHONPATH=src uv run --no-sync python -m deepbrief.cli run --date 2026-06-09 --fixtures tests/fixtures/day1
{
  "date": "2026-06-09",
  "experiment_id": null,
  "feedback_path": "/Users/liuzikai/DeepBrief/2026-06-09/feedback.md",
  "mode": "fixtures",
  "page_count": 9,
  "pdf": "/Users/liuzikai/DeepBrief/2026-06-09/brief.pdf",
  "post_checks_ok": true,
  "selected_item_ids": [
    "soak_context_memory",
    "soak_model_hype",
    "soak_eval_harness"
  ],
  "status": "ok"
}

$ PYTHONPATH=src .venv/bin/python - <<'PY'
from deepbrief.config import Config
from deepbrief.soak import write_day1_negative_feedback
c=Config.load()
day1={
    'feedback_path': str(c.artifacts_dir / '2026-06-09' / 'feedback.md'),
    'selected_items': [
        {'id':'soak_context_memory','title':'Context memory for coding agents'},
        {'id':'soak_model_hype','title':'Model announcement without implementation details'},
        {'id':'soak_eval_harness','title':'Small replay harness for agent evals'},
    ],
}
write_day1_negative_feedback(c, day1)
print(day1['feedback_path'])
PY
/Users/liuzikai/DeepBrief/2026-06-09/feedback.md

$ PYTHONPATH=src uv run --no-sync python -m deepbrief.cli run --date 2026-06-10 --fixtures tests/fixtures/day2
{
  "date": "2026-06-10",
  "experiment_id": 5,
  "feedback_path": "/Users/liuzikai/DeepBrief/2026-06-10/feedback.md",
  "mode": "fixtures",
  "page_count": 9,
  "pdf": "/Users/liuzikai/DeepBrief/2026-06-10/brief.pdf",
  "post_checks_ok": true,
  "selected_item_ids": [
    "soak_sandbox_governance",
    "soak_prompt_diffing",
    "soak_agent_trace"
  ],
  "status": "ok"
}
```

Aggregate verification command:

```sh
$ make m9a
{
  "checks": {
    "candidate_prompt_proposal": true,
    "cli_rollback_ok": true,
    "day1_pdf_ok": true,
    "day2_links_new_concept_to_day1": true,
    "day2_pdf_has_ab": true,
    "day2_pdf_ok": true,
    "feedback_file_has_promote_reject_slot": true,
    "feedback_file_promotion_ok": true,
    "no_repeated_items": true,
    "ok": true,
    "preference_diff_recorded": true,
    "ranking_prompt_tuned_via_experiment": true,
    "repeated_items": [],
    "spend_logged_and_within_budget": true,
    "spend_rows": [
      {
        "date": "2026-06-09",
        "spend_usd": 0.0,
        "stages": 8
      },
      {
        "date": "2026-06-10",
        "spend_usd": 0.0,
        "stages": 8
      }
    ]
  },
  "day1": {
    "date": "2026-06-09",
    "experiment_id": null,
    "feedback_path": "/Users/liuzikai/DeepBrief/2026-06-09/feedback.md",
    "page_count": 9,
    "pdf": "/Users/liuzikai/DeepBrief/2026-06-09/brief.pdf",
    "post_checks_ok": true,
    "selected_item_ids": [
      "soak_context_memory",
      "soak_model_hype",
      "soak_eval_harness"
    ]
  },
  "day2": {
    "date": "2026-06-10",
    "experiment_id": 4,
    "feedback_path": "/Users/liuzikai/DeepBrief/2026-06-10/feedback.md",
    "page_count": 9,
    "pdf": "/Users/liuzikai/DeepBrief/2026-06-10/brief.pdf",
    "post_checks_ok": true,
    "selected_item_ids": [
      "soak_sandbox_governance",
      "soak_prompt_diffing",
      "soak_agent_trace"
    ]
  },
  "promotion": {
    "active_version": 4,
    "stage": "rank",
    "status": "ok"
  },
  "rollback": {
    "ok": true,
    "returncode": 0,
    "stderr": "",
    "stdout": "{\"status\": \"ok\", \"action\": \"rollback\", \"stage\": \"rank\", \"active_version\": 1}"
  },
  "status": "ok"
}
```

## M9b - Handoff

Gate command and verification:

```sh
$ test -s SOAK.md && echo SOAK.md exists
SOAK.md exists

$ make install
{"action": "install", "label": "com.liuzikai.deepbrief", "plist": "/Users/liuzikai/Library/LaunchAgents/com.liuzikai.deepbrief.plist", "status": "ok", "stderr_log": "/Users/liuzikai/.deepbrief/logs/deepbrief.err.log", "stdout_log": "/Users/liuzikai/.deepbrief/logs/deepbrief.out.log"}

$ test -f /Users/liuzikai/Library/LaunchAgents/com.liuzikai.deepbrief.plist && echo plist_loaded_file_present
plist_loaded_file_present

$ launchctl print gui/$(id -u)/com.liuzikai.deepbrief
state = not running
runs = 0
event trigger = StartCalendarInterval Hour 6 Minute 15
path = /Users/liuzikai/Library/LaunchAgents/com.liuzikai.deepbrief.plist
program = /Users/liuzikai/Documents/GitHub/deepbrief/.venv/bin/python
arguments = -m deepbrief.cli run
```

`SOAK.md` now contains the user's live two-day checklist: morning expectations, how to file
feedback, how to inspect the Pipeline Report, how to promote/rollback prompt experiments, and
how to check spend/logs. The launchd job is left installed and loaded for the handoff.

## Final Sanity Checks

```sh
$ make doctor
DeepBrief M0 doctor: ok
repo: /Users/liuzikai/Documents/GitHub/deepbrief
seed files: 14 present
sources: 5 feeds, 5 repos, arxiv configured
migrations applied in temp db: 001_initial.sql
llm: budget wrapper dry-run recorded cost 0.0000
llm: code analyst permission_mode=dontAsk
llm: code analyst mutating/network tools denied
llm: bash PreToolUse allowlist enforced

$ make test
....
----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK

$ launchctl print gui/$(id -u)/com.liuzikai.deepbrief
state = not running
runs = 0
event trigger = StartCalendarInterval Hour 6 Minute 15
path = /Users/liuzikai/Library/LaunchAgents/com.liuzikai.deepbrief.plist
```
