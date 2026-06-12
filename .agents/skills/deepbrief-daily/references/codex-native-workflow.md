# Codex-Native DeepBrief Workflow

Use this workflow to produce a daily DeepBrief PDF entirely inside one Codex session. The old Python engine is not invoked.

## Inputs

- User profile: applied AI engineer, about two hours of reading time.
- Preferences: prefer code-grounded agent harnesses, sandboxing, prompt/version diffs, memory, evals, implementation mechanics, model-training-to-product implications, and applied document/extraction AI; penalize thin model-release hype.
- Source mix: lab/engineering posts, arXiv papers, repo feature releases, product/company engineering updates, eval benchmarks, model-training/inference notes, and high-signal builder discourse are all first-class.
- Output: one print-quality PDF plus a feedback file.

## Operating Standard

This is a long-running research workflow. Do not stop after a small set of convenient sources. A production DeepBrief must show high recall before narrowing:

- Screen at least 100 distinct candidates.
- Locally save at least 20 raw artifacts.
- Preserve one local artifact for every selected item.
- Deep-read selected items before drafting.
- Record subagent fan-out or equivalent main-agent wave work.
- Tie material claims to local evidence.

If a sandbox, network policy, source outage, auth wall, or Codex app limit prevents a gate, document the exact limit and ask for explicit approval before rendering a degraded PDF.

## Daily Procedure

1. **Prepare artifacts**
   - Create a dated local directory such as `/tmp/deepbrief-codex/YYYY-MM-DD/`, `~/DeepBrief/codex/YYYY-MM-DD/`, or a user-specified output path.
   - Use subdirectories: `sources/`, `sources/raw/`, `sources/papers/`, `repos/`, `images/`, `reviews/`, `verification/`.
   - Write working notes to local files only when useful; do not commit generated artifacts.

2. **Ingest feedback**
   - If yesterday's `feedback.md` exists in the Codex artifact tree, read it.
   - Extract item ratings, global preferences, and A/B decisions.
   - Apply feedback only for today's ranking and pipeline report unless the user asks to persist it.

3. **Scout**
   - Use `references/source-discovery.md`.
   - Gather at least 100 candidate items when possible through web search, official feeds, arXiv, GitHub releases, company blogs, benchmark pages, builder posts, and user-provided sources.
   - Save every candidate as JSONL in `sources/candidates.jsonl`.
   - Download at least 20 raw artifacts before synthesis. Raw artifacts include HTML, Markdown, PDF, extracted full text, release notes, changelog entries, repo diffs, source files, figures, screenshots, or metadata JSON.
   - Save every downloaded artifact as a JSONL record in `sources/manifest.jsonl` with local path, source URL, artifact type, byte count, fetch status, and intended use.
   - Include a source log with verified, substituted, degraded, skipped, and blocked sources.
   - Prefer recent items, but keep one foundational item if it explains today's frontier.

4. **Fan out**
   - When the user prompt or app default prompt explicitly asks for subagents, spawn read-heavy subagents for independent lanes: papers/evals, repos/releases, company/engineering posts, model-training/inference notes, applied document/extraction AI, builder discourse, and verification.
   - If `agents.max_threads` or the app limits concurrency, run agents in waves and record the limit.
   - If subagent tools are unavailable, the main agent must perform equivalent wave-based work and write the same reports.
   - Save `reviews/fanout-report.md` with lane assignments, source counts, raw downloads, top candidates, failed fetches, and unresolved gaps.

5. **Rank**
   - Score each candidate 0-100 from relevance, groundedness, depth fit, novelty, and source quality.
   - Deduct for hype, thin announcements, repeated items, or missing implementation detail.
   - Save ranking evidence for all screened candidates, not only selected items.
   - Select one deep target and 4-6 skim targets.
   - Choose a repo-release deep target when there is enough diff/source code to inspect; choose article/paper when it has enough mechanism.

6. **Deep-read selected sources**
   - For every selected item, preserve a local raw artifact and write `reviews/<item-id>.md`.
   - For papers: save PDF or extracted full text, read end to end, and inventory figures, tables, appendices, limitations, and evaluation claims.
   - For code/repo releases: clone or export only the relevant tag, diff, commit range, or PR set; read relevant files end to end; never execute downloaded code.
   - For company posts and benchmark pages: save raw HTML/text and separate primary-source claims from commentary.
   - For builder discourse or X-derived leads: treat posts as discovery signals only; verify claims against primary links before citing.

7. **Analyze deep target**
   - Use the selected read report plus raw artifacts.
   - For code: inspect the release diff or explicit scope first; expand to repository-level context only when needed to understand entry points, state, prompts, and runtime behavior. Do not execute downloaded code.
   - For article/paper: identify the mechanism, assumptions, visual evidence, and an exercise.
   - Build the deep dive exactly with the schema in `references/brief-contract.md`.

8. **Verify**
   - Write `verification/evidence-matrix.md` or `verification/evidence-matrix.jsonl`.
   - Code: mechanically verify every cited `file:line` and at least 90 percent of symbols with `rg`, `git grep`, `sed -n`, or equivalent read-only commands.
   - Article/paper: verify quoted claims against saved PDF/full text, source pages, or local extracts.
   - A source cannot be labeled `Verified` unless its local artifact exists and the evidence matrix references it.
   - Strike unsupported claims or move them to Errata.

9. **Compose**
   - Write `brief.md` in the fixed order from `references/brief-contract.md`.
   - Include at least one Mermaid diagram and at least one visual asset. Prefer a real source figure or screenshot when available and permitted; if none is available, document that in Errata and use an original Mermaid diagram.
   - Include `Pipeline Report`, `Tomorrow's Queue`, and `Errata`.
   - The Markdown must be final prose, not notes or TODOs.

10. **Feedback file**
   - Write `feedback.md` next to `brief.md` before rendering.
   - Include one block per selected item and a global `## What to change` section.
   - Include an A/B slot only when a real comparison was included in the PDF.

11. **Render and QA**
   - Run `python <skill>/scripts/render_brief.py --input brief.md --out <artifact-dir>`.
   - Fix research-gate, lint, citation, layout, and PDF failures until the renderer reports `status: ok`.
   - If missing tools prevent PDF rendering, deliver the Markdown and the exact missing tool list.
   - Use `--allow-degraded-research` only after explicit user approval.

## Output Contract

Final response to the user should include:

- PDF path.
- Markdown path.
- Feedback path.
- Candidate log path.
- Raw artifact manifest path.
- Fanout report path.
- Evidence matrix path.
- Candidate count, raw artifact count, selected-source artifact count, repo diff/checkouts count, and degraded-source count.
- Selected items.
- Verification summary and residual risks.
