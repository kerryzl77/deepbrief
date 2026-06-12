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
- Record actual subagent fan-out when the user asks for subagents, parallel agents, one-agent-per-source work, or monthly/high-recall gates.
- Tie material claims to local evidence internally and to public citation links in the final PDF.
- Produce a designed, readable PDF, not just a mechanically valid PDF.

If a sandbox, network policy, source outage, auth wall, or Codex app limit prevents a gate, document the exact limit and ask for explicit approval before rendering a degraded PDF.

## Monthly And Explicit-Subagent Guardrail

For monthly or other high-recall runs, the user's requested counts override the daily defaults. If the user asks for 1,000 screened sources, 100 raw artifacts, 100 read reports, or one source-specific subagent per source, treat those numbers as hard gates.

When subagents are requested, there are two required stages:

1. Discovery subagents: spawn multiple lane subagents or waves sized to the requested source-balance quotas. For a 1,000-source monthly run, assign roughly 200 leads per major lane across papers/evals, repo/source-code, company/lab posts, builder discourse/X/blog/newsletter/podcast, model-training/inference, and applied product/document AI unless the user gives different lane counts. Save each lane report before ranking.
2. Source-specific read subagents: after selecting the 100+ local artifact-backed sources, spawn one actual subagent for each selected artifact. Give each subagent exact local paths and require full-artifact inspection. Save each report as `reviews/subagents/read-<item-id>.md`.

Deterministic scripts may fetch, dedupe, count, render, and perform mechanical checks. They may also create auxiliary `reviews/read-workers/` files. They do not count as requested subagents. If the app cannot spawn the requested subagents, stop before synthesis and ask the user whether to approve a degraded non-subagent run.

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
   - Keep the lane quotas from `references/source-discovery.md` visible while screening. Do not satisfy the 100-candidate gate mostly by expanding one release feed or one arXiv query.
   - Prefer recent items, but keep one foundational item if it explains today's frontier.

4. **Fan out**
   - When the user prompt or app default prompt explicitly asks for subagents, spawn read-heavy subagents for independent lanes: papers/evals, repos/releases, company/engineering posts, model-training/inference notes, applied document/extraction AI, builder discourse, and verification.
   - If `agents.max_threads` or the app limits concurrency, run agents in waves and record the limit. Continue wave spawning until the requested subagent count is met or a hard app limit blocks progress.
   - If subagent tools are unavailable or a hard app limit prevents the requested count, stop before synthesis and ask the user whether to approve a degraded non-subagent run.
   - Save each required discovery lane's raw return under `reviews/fanout/<lane>.md` or `reviews/subagents/<lane>.md` before summarizing it. Required discovery lane names are `papers`, `repos`, `company_posts`, `model_training`, `applied_product`, and `discourse`.
   - After the shortlist is chosen and raw artifacts are downloaded, spawn one source-specific read/verification subagent per selected artifact when the user requested source-specific subagents or 100+ deep-read workers. Give each subagent exact local paths and ask it to inspect the saved artifact with read-only shell commands such as `rg`, `nl`, `sed`, `pdfinfo`, `pdftotext`, `git show`, and `git grep`.
   - Save selected-source local read outputs as `reviews/subagents/read-<item-id>.md`. Each must list local paths inspected, exact evidence references found, mechanism notes, limitations, and what should appear in the final synthesis.
   - Do not count script-generated `reviews/read-workers/*.md` as source-specific subagent outputs unless the user explicitly approved a degraded non-subagent run after being told the requested subagents could not be spawned.
   - Save `reviews/fanout-report.md` with lane assignments, source counts, raw downloads, top candidates, failed fetches, unresolved gaps, and links to the saved raw lane reports.

5. **Rank**
   - Score each candidate 0-100 from relevance, groundedness, depth fit, novelty, and source quality.
   - Deduct for hype, thin announcements, repeated items, or missing implementation detail.
   - Save ranking evidence for all screened candidates, not only selected items.
   - Select one deep target and 4-6 skim targets.
   - Choose a repo-release deep target when there is enough diff/source code to inspect; choose article/paper when it has enough mechanism.

6. **Deep-read selected sources**
   - For every selected item, preserve a local raw artifact and write `reviews/<item-id>.md`.
   - For papers: save PDF or extracted full text, read end to end, and inventory figures, tables, appendices, limitations, evaluation claims, author/source quality, and links to code or project pages when available.
   - For code/repo releases: clone or export only the relevant tag, diff, commit range, or PR set; read relevant files end to end; capture entry points, state transitions, tests, prompts, security boundaries, and exact file/line evidence; never execute downloaded code.
   - For company posts and benchmark pages: save raw HTML/text and separate primary-source claims from commentary.
   - For builder discourse or X-derived leads: treat posts as discovery signals only; verify claims against primary links before citing.
   - A read report is not just a citation stub. It should include the local artifact inventory, what was read, mechanism, limitations, evidence references, and what the source changes about the final synthesis.

7. **Analyze deep target**
   - Use the selected read report plus raw artifacts.
   - For code: inspect the release diff or explicit scope first; expand to repository-level context only when needed to understand entry points, state, prompts, and runtime behavior. Do not execute downloaded code.
   - For article/paper: identify the mechanism, assumptions, visual evidence, limits, and an exercise. Do not turn the paper into fake code unless the source itself provides an algorithm worth translating.
   - Build the deep dive exactly with the schema in `references/brief-contract.md`.

8. **Verify**
   - Write `verification/evidence-matrix.md` or `verification/evidence-matrix.jsonl`.
   - Code: mechanically verify every cited `file:line` and at least 90 percent of symbols with `rg`, `git grep`, `sed -n`, or equivalent read-only commands.
   - Article/paper: verify quoted claims against saved PDF/full text, source pages, or local extracts.
   - Verify that each material claim maps to local evidence in the evidence matrix.
   - A source cannot be labeled `Verified` unless its local artifact exists and the evidence matrix references it.
   - Strike unsupported claims or move them to Errata.

9. **Build the citation registry**
   - Resolve every local evidence ref used for material claims through `sources/manifest.jsonl`, `sources/selected-candidates.jsonl`, and `sources/candidates.jsonl`.
   - Assign one stable citation number per distinct public source URL or canonical source identity. Reuse that number for multiple local line refs from the same source.
   - Persist the audit bridge in `verification/evidence-matrix.*`: claim, local artifact path, exact local line/page/section, citation number, public title, and public URL.
   - Do not use `verification/excerpts/*`, `sources/raw/*`, `sources/papers/*`, `repos/*`, or `reviews/*` paths as reader-facing citations in `brief.md`.
   - If a selected source lacks a public URL, either resolve the canonical URL before synthesis or mark the item in Errata as degraded and avoid material claims from it.

10. **Compose**
   - Write `brief.md` in the fixed order from `references/brief-contract.md`.
   - Include at least one explanatory diagram and at least one visual asset. Prefer a real source figure or screenshot when available and permitted; if none is available, document that in Errata and use an original diagram based on verified evidence.
   - Crop or annotate paper screenshots before using them. A full paper page, formula dump, or unreadable screenshot is not a good reader visual.
   - Use inline code formatting for symbols, file paths, config keys, API fields, and model/release identifiers.
   - Keep code blocks short. Long blocks require a real source path in the fence info string, such as ````python source="repos/pkg/file.py"```` or ````text derived_from="sources/papers/example.txt:120"````.
   - Use inline citation links like `[1](#source-1)` next to material claims. Put public title and URL entries in `# Citation Appendix`.
   - Include `Pipeline Report`, `Tomorrow's Queue`, and `Errata`.
   - The Markdown must be final prose, not notes or TODOs.

11. **Feedback file**
   - Write `feedback.md` next to `brief.md` before rendering.
   - Include one block per selected item and a global `## What to change` section.
   - Include an A/B slot only when a real comparison was included in the PDF.

12. **Render and QA**
   - Run `python <skill>/scripts/render_brief.py --input brief.md --out <artifact-dir>`.
   - Fix research-gate, lint, citation, layout, diagram, and PDF failures until the renderer reports `status: ok`.
   - Visually inspect representative rendered pages: cover/stats, deep-dive mechanism, diagram/visual page, skim page, and pipeline page. If any page is dense, illegible, or unstyled, revise content/template rather than accepting mechanical success.
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
