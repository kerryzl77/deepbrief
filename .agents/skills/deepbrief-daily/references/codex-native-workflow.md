# Codex-Native DeepBrief Workflow

Use this workflow to produce a daily DeepBrief PDF entirely inside one Codex session. The old Python engine is not invoked.

## Inputs

- User profile: applied AI engineer, about two hours of reading time.
- Preferences: prefer code-grounded agent harnesses, sandboxing, prompt/version diffs, memory, evals, and implementation mechanics; penalize thin model-release hype.
- Source mix: lab/engineering posts, arXiv papers, and repo feature releases are all first-class.
- Output: one print-quality PDF plus a feedback file.

## Daily Procedure

1. **Prepare artifacts**
   - Create a dated local directory such as `/tmp/deepbrief-codex/YYYY-MM-DD/`, `~/DeepBrief/codex/YYYY-MM-DD/`, or a user-specified output path.
   - Use subdirectories: `sources/`, `repos/`, `images/`, `verification/`.
   - Write working notes to local files only when useful; do not commit generated artifacts.

2. **Ingest feedback**
   - If yesterday's `feedback.md` exists in the Codex artifact tree, read it.
   - Extract item ratings, global preferences, and A/B decisions.
   - Apply feedback only for today's ranking and pipeline report unless the user asks to persist it.

3. **Scout**
   - Use `references/source-discovery.md`.
   - Gather at least 15 candidate items when possible through web search, official feeds, arXiv, GitHub releases, and user-provided sources.
   - Download source snapshots needed for the selected items into the artifact directory.
   - Include a source log with verified, substituted, degraded, and skipped sources.
   - Prefer recent items, but keep one foundational item if it explains today's frontier.

4. **Rank**
   - Score each candidate 0-100 from relevance, groundedness, depth fit, novelty, and source quality.
   - Deduct for hype, thin announcements, repeated items, or missing implementation detail.
   - Select one deep target and 4-6 skim targets.
   - Choose a repo-release deep target when there is enough diff/source code to inspect; choose article/paper when it has enough mechanism.

5. **Analyze deep target**
   - Fetch source text, release notes, paper HTML/PDF text, figures, and/or repo files.
   - For code: inspect only the relevant release diff, not the whole repo.
   - For article/paper: identify the mechanism, assumptions, and an exercise.
   - Build the deep dive exactly with the schema in `references/brief-contract.md`.

6. **Verify**
   - Code: mechanically verify every cited `file:line` and at least 90 percent of symbols with `rg`, `git grep`, `sed -n`, or equivalent read-only commands.
   - Article/paper: verify quoted claims against fetched text or source pages.
   - Strike unsupported claims or move them to Errata.

7. **Compose**
   - Write `brief.md` in the fixed order from `references/brief-contract.md`.
   - Include at least one Mermaid diagram and at least one visual asset. If no source image is available, use a Mermaid SVG diagram as the visual asset and note that it is original.
   - Include `Pipeline Report`, `Tomorrow's Queue`, and `Errata`.
   - The Markdown must be final prose, not notes or TODOs.

8. **Feedback file**
   - Write `feedback.md` next to `brief.md` before rendering.
   - Include one block per selected item and a global `## What to change` section.
   - Include an A/B slot only when a real comparison was included in the PDF.

9. **Render and QA**
   - Run `python <skill>/scripts/render_brief.py --input brief.md --out <artifact-dir>`.
   - Fix failures until the renderer reports `status: ok`.
   - If missing tools prevent PDF rendering, deliver the Markdown and the exact missing tool list.

## Output Contract

Final response to the user should include:

- PDF path.
- Markdown path.
- Feedback path.
- Source count and selected items.
- Verification summary and residual risks.
