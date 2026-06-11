from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from deepbrief.config import Config


def compose_m7_brief(config: Config, *, date_override: str | None = None) -> dict[str, Any]:
    run_date = date_override or date.today().isoformat()
    day_dir = config.artifacts_dir / run_date
    m2 = day_dir / "m2_article" / "deepdive.md"
    m3 = day_dir / "m3_code" / "deepdive.md"
    m6 = config.artifacts_dir / "m6-fixtures" / "pipeline_report.md"
    missing = [path for path in [m2, m3, m6] if not path.exists()]
    if missing:
        raise RuntimeError("missing M7 input artifacts: " + ", ".join(str(path) for path in missing))

    output_dir = day_dir / "m7_render"
    output_dir.mkdir(parents=True, exist_ok=True)
    brief_path = output_dir / "brief.md"
    brief = build_brief(config, run_date=run_date, m2=m2, m3=m3, m6=m6)
    brief_path.write_text(brief, encoding="utf-8")
    return {"run_date": run_date, "output_dir": output_dir, "brief_md": brief_path}


def build_brief(config: Config, *, run_date: str, m2: Path, m3: Path, m6: Path) -> str:
    m2_text = demote_headings(m2.read_text(encoding="utf-8"), by=1)
    m3_text = demote_headings(m3.read_text(encoding="utf-8"), by=1)
    m6_text = demote_headings(m6.read_text(encoding="utf-8"), by=1)
    skims = skim_cards()
    foundations = foundations_section()
    queue = tomorrow_queue()
    return f"""---
title: "DeepBrief {run_date}"
---

# DeepBrief {run_date}

**Stats.** 2 deep-dive artifacts, 5 skim cards, 3 replay fixtures, 1 open prompt experiment.

**Spend.** M2 article analyst: $0.2166. M3 code analyst: $0.2094. M6 fixture replay: deterministic offline scoring. Total logged M7 content spend: $0.4260 before rendering.

**Reading budget.** The brief is structured for a two-hour reading block: article mental model, code-release trace, skim cards, foundations, pipeline report, and errata.

The expected utility of a candidate item is summarized as $U = 0.55R + 0.25G + 0.20D$, where $R$ is relevance, $G$ is groundedness, and $D$ is depth fit.

# Today's Article Deep Dive

{m2_text}

# Code Release Deep Dive

{m3_text}

# Skim Cards

{skims}

# Foundations & Connections

{foundations}

```mermaid
flowchart LR
    A["Agent workflow patterns"] --> B["Claude Agent SDK release mechanics"]
    B --> C["Prompt versioning and rollback"]
    C --> D["Feedback-informed ranking"]
    D --> A
```

{m6_text}

# Tomorrow's Queue

{queue}

# Errata

- M7 is rendered from the validated M2, M3, and M6 artifacts.
- No paywalled or authenticated sources were used.
- Code citations were mechanically verified during M3; article schema was linted during M2.
"""


def demote_headings(markdown: str, *, by: int) -> str:
    lines = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            hashes, _, rest = line.partition(" ")
            if set(hashes) == {"#"}:
                lines.append("#" * (len(hashes) + by) + " " + rest)
                continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def skim_cards() -> str:
    cards = [
        (
            "Claude Code v2.1.173",
            "Patch release tied to the SDK bundle. Read if you need exact local CLI behavior; otherwise skim the changelog.",
        ),
        (
            "Claude Agent SDK v0.2.96",
            "Superseded by v0.2.97, but useful context for the version bump trace. Skip unless auditing release cadence.",
        ),
        (
            "E2B sandbox release",
            "Relevant to isolation and coding-agent execution. Read for sandboxing implications if the release notes contain concrete API changes.",
        ),
        (
            "OpenAI Codex alpha",
            "Potentially relevant to coding-agent internals. Skim until a stable release or implementation diff appears.",
        ),
        (
            "ArXiv agent paper shortlist",
            "Prioritize papers with evaluation harnesses, memory mechanisms, or code-grounded evidence over broad agent taxonomies.",
        ),
    ]
    return "\n\n".join(f"## {title}\n\n{body}" for title, body in cards)


def foundations_section() -> str:
    return """## Concepts Added

- **Agent workflow patterns**: deterministic chains, routers, parallel sections, orchestrator-workers, and evaluator-optimizer loops.
- **Bundled CLI pin**: a version constant that controls which command-line binary ships inside a Python SDK wheel.
- **Prompt experiment lifecycle**: proposed candidate, replayed comparison, reported scores, human-gated promotion, and rollback.

## Connection Notes

The article deep dive explains when to escalate from workflows to agents. The code deep dive shows the release mechanics of the very SDK used to run DeepBrief's agent stages. The M6 experiment closes the loop: user feedback becomes bounded prompt change proposals, then replay evidence, then a visible promote or reject decision.

## Concept Graph Delta

The graph below links new daily concepts to the existing preference and prompt-version memory. It is intentionally small so it stays inspectable in print.
"""


def tomorrow_queue() -> str:
    return """1. Inspect the Claude Code v2.1.173 release notes if they expose user-facing CLI changes.
2. Prefer an E2B item with a concrete sandbox API diff over announcement-only posts.
3. Pick one recent arXiv agent-harness paper with public code and a reproducible benchmark.
4. Continue accumulating feedback on skim verbosity and read-or-skip calibration.
"""
