---
name: deepbrief-daily
description: "Generate a high-recall Codex-native DeepBrief PDF for applied AI/agents work: screen 100+ sources, download 20+ raw artifacts, use explicit subagent fan-out when requested or from the app default prompt, deep-read selected sources, then render and verify without invoking the legacy Anthropic/Claude engine."
---

# DeepBrief Daily

## Model

Run DeepBrief as a second implementation inside Codex. The existing Python repository is a reference and renderer source, not the production execution path.

- Generate the brief content in the current Codex session.
- Search, fetch, inspect, rank, analyze, and verify using Codex tools and local deterministic commands.
- Use bundled scripts only for rendering and mechanical PDF checks.
- Assume the user wants a long-running, high-recall research run when they invoke this skill through the Codex app default prompt.
- Use explicit subagent fan-out when the user asks for subagents, parallel agents, one-agent-per-source work, or uses this skill's default prompt. If subagents are capped, run them in waves and record the limit. If subagent tools are unavailable, stop before synthesis and ask for explicit approval to continue without them.
- Do not run the legacy DeepBrief Python engine unless the user explicitly opts into Anthropic-backed execution.
- Treat `status: ok` from the renderer as necessary but not sufficient. The PDF must be readable, evidence-linked, visually legible, and useful as a daily learning artifact.

## Codex-Native Boundary

For Codex-native DeepBrief runs, the Python repository is a reference implementation and deterministic renderer only. Do not run `deepbrief`, `python -m deepbrief.cli`, Make pipeline targets, launchd install/kickstart, Claude Agent SDK stages, calibration replay, or commands that inspect or source provider secrets unless the user explicitly asks for legacy-engine execution.

Generate research, ranking, analysis, verification, and prose inside the current Codex session. Use local scripts only for deterministic parsing, file assembly, rendering, and verification.

## Hard Subagent Guardrails

These guardrails override any softer wording elsewhere in this skill.

- When the user requests explicit subagents, parallel agents, one-agent-per-source work, or a monthly/high-recall run with source-count gates, do not replace subagents with scripted `read-workers`, deterministic summaries, or main-agent keyword scans.
- Stage 1 discovery for a monthly 1,000-source run must use multiple discovery subagents or waves sized to the requested source balance. Assign each major lane enough subagent work to cover its quota, typically about 200 leads per major lane: papers/evals, repo/source-code, company/lab posts, builder discourse/X/blog/newsletter/podcast, model-training/inference, and applied product/document AI. Deterministic collectors may dedupe, fetch, and manifest leads, but they do not satisfy the requested discovery-subagent work by themselves.
- Stage 2 deep read for a monthly run must spawn one actual source-specific subagent per shortlisted artifact when the user asks for 100 selected artifacts or 100 deep-read workers. Each subagent receives the exact local artifact paths and writes a report under `reviews/subagents/read-<item-id>.md`.
- A scripted report under `reviews/read-workers/` is useful audit material, but it does not count as a source-specific subagent report when the user asked for subagents or one-agent-per-source work.
- If app concurrency is capped, spawn the source-specific subagents in waves until the requested count is met. Record wave size, completed agent ids, timeouts, and failures in `reviews/fanout-report.md`.
- If the requested number of subagents cannot be spawned, stop before synthesis or rendering and ask the user whether to approve a degraded run. Do not silently satisfy the gate with local scripts.

## Required Reads

Before generating a real brief, read these references:

- `references/codex-native-workflow.md` for the end-to-end procedure.
- `references/source-discovery.md` for source search, downloads, and repo inspection.
- `references/brief-contract.md` for exact PDF structure and quality gates.
- `references/pipeline-map.md` only when comparing against the legacy repository.

## Workflow

1. Create a dated artifact directory in a temp or user-requested location.
2. Ingest prior `feedback.md` files from recent Codex artifact trees when present.
3. Run high-recall source discovery across the broad applied-AI source map in `references/source-discovery.md`.
4. Screen at least 100 distinct candidate sources before final ranking. Save them to `sources/candidates.jsonl`.
5. Download at least 20 raw local artifacts before synthesis. Save artifact records to `sources/manifest.jsonl`.
6. Use two-phase subagent fan-out. First run discovery-lane subagents, then run one source-specific deep-read subagent per selected artifact after raw artifacts are saved. Save `reviews/fanout-report.md` plus raw lane reports under `reviews/fanout/` and source-specific reports under `reviews/subagents/`. Do not count scripted `read-workers` as subagents.
7. Rank candidates against the user profile and learned preferences. Save ranking evidence for all screened candidates.
8. Pick one deep dive and 4-6 skim items only after the research gates pass.
9. For each selected item, download or preserve a local raw artifact and write a substantive per-source read report under `reviews/`. The deep-dive report must be materially deeper than skim reports and must show full-document or full-diff inspection, not only keyword hits.
10. Write `verification/evidence-matrix.md` or `verification/evidence-matrix.jsonl` tying claims to local artifacts and exact sections, pages, or lines.
11. Write a complete, ready-to-read `brief.md` following `references/brief-contract.md`. Use source-aware mechanism traces, inline evidence, and real code/config snippets only when they come from inspected artifacts.
12. Run `python scripts/render_brief.py --input <brief.md> --out <artifact-dir>`.
13. Fix research, citation, layout, or quality-gate failures until the PDF is ready to read.

## Research Gates

Do not render a production PDF unless these gates pass, or the user explicitly approves a degraded run:

- `sources/candidates.jsonl` contains at least 100 distinct screened candidates.
- `sources/manifest.jsonl` contains at least 20 locally saved raw artifacts with valid local paths and nonzero byte counts.
- Every selected item has a local artifact: HTML/text/PDF/release notes under `sources/`, paper PDF or extracted text under `sources/papers/`, or repo checkout/diff under `repos/`.
- Repo-release items have local tag, commit, diff, or checkout evidence. Release-note-only repo analysis is degraded and cannot be labeled verified.
- Paper deep dives have saved PDF or full extracted text plus a figure/table inventory.
- Code deep dives have checked-out relevant files and verified `file:line` citations.
- `reviews/fanout-report.md` records subagent or wave assignments, limits, failures, and handoff summaries.
- Raw subagent or wave outputs are saved under `reviews/fanout/` or `reviews/subagents/`; do not rely only on final chat text as the audit trail.
- When the user requested one source-specific subagent per selected artifact, `reviews/subagents/read-*.md` contains one actual subagent report for each selected artifact. `reviews/read-workers/*.md` cannot satisfy this gate unless the user explicitly approved a degraded non-subagent run.
- Each selected source has a read report under `reviews/`. If the user requested source-specific subagents and subagents are unavailable, stop before synthesis and ask for explicit degraded-run approval instead of substituting main-agent reports.
- Read reports must be substantive enough to prove inspection. Deep-dive reports should include an artifact inventory, full-document or full-diff map, mechanism summary, figure/table or file inventory, limitations, exact local evidence references, and open questions. Skim reports should include mechanism, why it matters, limitations, and exact local evidence references.
- `verification/evidence-matrix.*` maps each material claim to a local artifact path and exact evidence location.
- A source cannot be labeled `Verified` unless its raw local artifact exists and is referenced in the evidence matrix.
- Body paragraphs in `brief.md` carry inline local evidence references or source links near the claims they support.
- Visuals are readable and purposeful: no empty-looking Mermaid, generic diagram captions, or unannotated full-page paper screenshots as the main visual.

## Rendering

The renderer expects a complete Markdown brief written by Codex:

```bash
python scripts/render_brief.py --input ~/DeepBrief/codex/YYYY-MM-DD/brief.md --out ~/DeepBrief/codex/YYYY-MM-DD
```

If renderer tools are missing, produce `brief.md` and list the exact missing binaries. Do not fall back to the legacy engine.

If the user explicitly approves a degraded research run after seeing missing gates, the renderer may be invoked with `--allow-degraded-research`; otherwise a research-gate failure must block rendering.

## Final Deliverable

Deliver one daily PDF that is ready to read. It must contain actual researched content, visuals, citations, deep dive, skims, foundations, pipeline report, tomorrow queue, and errata. Do not deliver only a plan, stamp, summary, or scaffold unless rendering is blocked by missing local tools or explicitly approved degraded gates.

The final response must include:

- PDF, Markdown, feedback, candidate log, manifest, fanout report, and evidence matrix paths.
- Candidate count, raw artifact count, selected-source artifact count, repo diff/checkouts count, and degraded-source count.
- Selected items and why the deep dive won.
- Verification summary and residual risks.

## Forbidden

Do not execute these by default:

- `deepbrief`, `python -m deepbrief.cli`, `uv run ... deepbrief`, or Make targets that call them.
- Imports from `deepbrief.*`, `deepbrief.llm`, or `claude_agent_sdk`.
- Commands that source `.env` or inspect provider API keys.
- Launchd install/kickstart commands or legacy calibration/tuner replay commands.
- Downloaded repository test/build/install commands.
- Writes inside downloaded source repositories, except creating separate exported diffs or notes in the artifact directory.

Local Python scripts in this skill are allowed only for deterministic parsing, file assembly, rendering, and verification.
