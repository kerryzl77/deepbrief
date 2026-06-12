---
name: deepbrief-daily
description: Generate DeepBrief-quality daily AI/agents learning PDFs inside one Codex session without invoking the repository's Anthropic/Claude Agent SDK engine. Use when the user asks to run a DeepBrief/debrief morning brief, create the daily PDF from Codex, package DeepBrief as a skill, search sources and repos for an AI/agents deep dive, or produce the same structured brief from a fresh Codex session with local rendering and verification only.
---

# DeepBrief Daily

## Model

Run DeepBrief as a second implementation inside Codex. The existing Python repository is a reference, not the execution path.

- Generate the brief content in the current Codex session.
- Search, fetch, inspect, rank, analyze, and verify using Codex tools and local deterministic commands.
- Use bundled scripts only for rendering and mechanical PDF checks.
- Do not run the legacy DeepBrief Python engine unless the user explicitly opts into Anthropic-backed execution.

## Required Reads

Before generating a real brief, read these references:

- `references/codex-native-workflow.md` for the end-to-end procedure.
- `references/source-discovery.md` for source search, downloads, and repo inspection.
- `references/brief-contract.md` for exact PDF structure and quality gates.
- `references/pipeline-map.md` only when comparing against the legacy repository.

## Workflow

1. Create a dated artifact directory in a temp or user-requested location.
2. Perform deep web/repo research in this Codex session.
3. Download relevant source files, article snapshots, figures, papers, release metadata, and repo snippets into the artifact directory.
4. Rank candidates against the user profile and learned preferences in the skill references or repo files.
5. Pick one deep dive and 4-6 skim items.
6. Write a complete, ready-to-read `brief.md` following `references/brief-contract.md`.
7. Run `python scripts/render_brief.py --input <brief.md> --out <artifact-dir>`.
8. Fix any content, citation, layout, or quality-gate failures until the PDF is ready to read.

## Rendering

The renderer expects a complete Markdown brief written by Codex:

```bash
python scripts/render_brief.py --input ~/DeepBrief/codex/YYYY-MM-DD/brief.md --out ~/DeepBrief/codex/YYYY-MM-DD
```

If renderer tools are missing, produce `brief.md` and list the exact missing binaries. Do not fall back to the legacy engine.

## Final Deliverable

Deliver one daily PDF that is ready to read. It must contain the actual researched content, visuals, citations, deep dive, skims, foundations, pipeline report, tomorrow queue, and errata. Do not deliver only a plan, stamp, summary, or scaffold unless rendering is blocked by missing local tools.

## Forbidden

Do not execute these by default:

- `deepbrief`, `python -m deepbrief.cli`, `uv run ... deepbrief`, or Make targets that call them.
- Imports from `deepbrief.*`, `deepbrief.llm`, or `claude_agent_sdk`.
- Commands that source `.env` or inspect provider API keys.
- Downloaded repository test/build/install commands.

Local Python scripts in this skill are allowed only for deterministic parsing, file assembly, rendering, and verification.
