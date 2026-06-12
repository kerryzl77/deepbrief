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
- Keep local `file:line` evidence in read reports and `verification/evidence-matrix.*`; final PDF prose must use public citation links like `[1](#source-1)` that resolve to a title and raw source URL in `# Citation Appendix`.

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

## Output Contract Precedence

- When the user adapts this skill to a different deliverable (course-note book, report, handbook) and supplies an explicit output structure, the user's structure is the contract. Use the matching renderer profile (`--profile course_book` for per-lecture course books, per `references/brief-contract.md` > Course Book Contract).
- If no renderer profile matches the user's required structure, stop before composition and ask the user how to proceed. Do not reshape the deliverable into the daily/monthly brief schema to satisfy the renderer; a brief-shaped document that drops the user's required sections is a failed run even if the renderer reports `status: ok`.
- Pass coverage expectations to the renderer when the user enumerates them (for example `--expect-lectures 26 --expect-discussions 11`) so missing or merged sections block rendering instead of shipping.

## Hard Composition Guardrails

- Author all final prose and diagrams from the read reports and lane syntheses, in-session or via composer subagents. Never generate deep-dive, skim-card, or section prose from string templates or scripts; scripts may only concatenate already-authored Markdown. The renderer rejects duplicated blocks, repeated sentences, and dive pairs that share sentences.
- Each deep dive's mechanism trace, diagram labels, evidence-map claims, snippet, and experiment must come from that source's own read report. If two dives would share a diagram or paragraph, fix the composition, not the gate.
- On large runs, draft each deep dive to `drafts/deep-dive-<nn>-<item-id>.md` right after lane synthesis, then assemble `brief.md` from the drafts. After context compaction, re-read drafts and syntheses from disk instead of reconstructing from memory.
- Never edit `scripts/render_brief.py`, `assets/brief.typ`, or gate thresholds during a run to make a failing gate pass. If a gate seems wrong for the run shape, stop and ask the user.
- Never pad read reports or audit artifacts to satisfy count gates; the renderer ignores report sections whose heading mentions the renderer.
- Authored prose must exist on disk as Markdown (under `drafts/`, `reviews/`, or `reviews/synthesis/`) before any assembly script runs. Embedding section prose, composer reports, or audit reports as string literals inside a script and executing it violates the no-template rule even when the embedded text was model-written: it destroys the audit trail (the "reports" postdate the script) and bypasses the draft-first compaction safety in this skill. Audit artifacts like `composition-report.md` and `fanout-report.md` must be written directly by the agent that did the work, never emitted by the assembly script.

## Required Reads

Before generating a real brief, read these references:

- `references/codex-native-workflow.md` for the end-to-end procedure.
- `references/source-discovery.md` for source search, downloads, and repo inspection.
- `references/brief-contract.md` for exact PDF structure and quality gates.
- `references/pipeline-map.md` only when comparing against the legacy repository.

Also read the calibrated reader surfaces at the repository root and use them for ranking and composition:

- `profile.md` for the reader's interest areas and penalties.
- `preferences.md` for learned, dated preference bullets; recent entries win on conflict.
- Before final rendering, judge the draft against the rubrics in `calibration/rubrics/` when that directory exists, and fix the weakest-scoring sections first.

These files are inputs only. Do not write to `profile.md` or `preferences.md`; they are maintained by the separate calibration pipeline.

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
11. Write a complete, ready-to-read `brief.md` following `references/brief-contract.md` and the Hard Composition Guardrails above: author each section from its read reports and lane syntheses (drafting deep dives to `drafts/` first on large runs), use source-aware mechanism traces, inline evidence, and real code/config snippets only when they come from inspected artifacts. Never emit final prose from a script template.
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
- Body paragraphs in `brief.md` carry inline public citation links or raw source URLs near the claims they support. Do not expose internal local evidence refs in final prose.
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
- Scripts that generate final `brief.md` prose, deep dives, skim cards, or diagrams from templates.
- Edits to `scripts/render_brief.py`, `assets/brief.typ`, or gate thresholds made during a run to pass a failing gate.

Local Python scripts in this skill are allowed only for deterministic parsing, file assembly, rendering, and verification.
