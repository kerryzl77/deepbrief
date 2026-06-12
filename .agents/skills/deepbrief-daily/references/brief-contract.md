# Brief Contract

Use this file when writing `brief.md`.

The sections below define the daily contract. For monthly/high-recall runs, follow `## Monthly Brief Contract` at the end of this file; it overrides the daily structure wherever the two differ. The renderer auto-detects the profile from the top-level headings.

## Required Order

1. Cover and stats.
2. Table of contents (handled by the Typst template, but the Markdown must have clear headings).
3. Today's Deep Dive.
4. Skim Cards.
5. Foundations & Connections.
6. Concept Graph Delta.
7. Pipeline Report.
8. Tomorrow's Queue.
9. Errata.
10. Citation Appendix.

## Cover Requirements

Include:

- Date.
- Selected deep target title and type.
- Number of skim cards.
- Source counts by class.
- Research coverage: screened candidate count, raw artifact count, selected-source artifact count, repo diff/checkouts count, and degraded-source count.
- Estimated reading time.
- Safety note: generated inside Codex session; legacy Anthropic-backed engine not invoked.

Include the utility formula so render QA can find math text:

```tex
$U = 0.55R + 0.25G + 0.20D$
```

## Deep Dive Schema

Use these exact headings under the deep dive:

```md
# <title>
## TL;DR
## Mental model
## Why this matters now
## Mechanism trace
## Evidence map
## Walkthrough
## Implementation notes
## Try it yourself
## Open questions
## Sources & citations
```

Rules:

- `TL;DR`: at most five bullets.
- `Why this matters now`: explain the operational impact in 2-4 paragraphs, with inline citations for material claims.
- `Mechanism trace`: explain the actual system, benchmark, workflow, or paper mechanism as a staged flow. Include one readable diagram or compact table when it clarifies the flow.
- `Evidence map`: include a table that maps key claims to reader-facing citation numbers. Keep local artifact paths and exact evidence references in `verification/evidence-matrix.*`, not in the final PDF prose.
- `Walkthrough`: for code/repo targets, start with worktree shape, then trace entry points, state/data flow, security or approval boundaries, tests, and exact files. For papers/articles, trace local artifact inventory, central claim, method or eval setup, results, limits, and how to adapt it.
- `Implementation notes`: include real code, config, prompt, API payload, or diff snippets only when they come from inspected artifacts. Do not include a long pseudocode block just to satisfy format.
- `Sources & citations`: include the compact citation numbers used by the deep dive. Full title and URL entries belong in the final `Citation Appendix`, and body paragraphs must already carry inline public citation links.
- Include one explanatory diagram and one visual asset. A poor full-page paper screenshot does not qualify unless it is cropped or annotated and explained in the caption.
- Do not use a `## Pseudocode` heading in production briefs. Long pseudocode is allowed only when the source itself is an algorithmic artifact and the block is labeled with a `source=` or `derived_from=` fence attribute.

Inline evidence:

- Put an inline citation after every material claim, metric, release detail, or source-specific interpretation.
- In final `brief.md` prose, use reader-facing Markdown citation links such as `[1](#source-1)` or `[2](#source-2)`. Multiple supporting sources should appear as adjacent links, for example `[1](#source-1) [2](#source-2)`.
- Do not expose internal audit paths such as `verification/excerpts/example.txt:12`, `sources/raw/example.txt:34`, `repos/example.patch:56`, or `reviews/item.md:78` in the reader-facing PDF. Those local refs belong in read reports and `verification/evidence-matrix.*`.
- When a claim depends on exact local line evidence, map that line evidence to a public citation number through the evidence matrix and citation registry before composing final prose.
- Do not move all citations to the end of a section. End citations are a bibliography, not evidence for the prose.

## Citation Appendix

Add a final top-level section:

```md
# Citation Appendix

## Source 1: <title> {#source-1}

- URL: <raw public source URL>
- Type: <paper | repo_commit | technical_doc | discourse_lead | other>
```

Rules:

- Assign one stable citation number per distinct public source URL or canonical source identity. Reuse the same number for multiple line-level evidence refs from the same source.
- Each appendix entry must include the public title and raw public URL, such as an arXiv URL, GitHub commit/PR/repo URL, company blog URL, benchmark page, paper project page, or original discourse URL.
- If a public URL is unavailable for a selected source, put the item in Errata and do not use it for material claims unless the user explicitly approves the degraded citation.
- The appendix is reader-facing. Do not fill it with local artifact paths, read-report paths, or `verification/excerpts/*` refs.

## Skim Cards

Each skim card should be 120-180 words and include:

- What changed.
- Why it matters.
- Read-or-skip verdict.
- Item ID and source URL.
- At least two inline evidence references or source links near the claims they support.

## Foundations & Connections

Include:

- 3-7 concepts.
- One sentence per concept.
- At least one edge from a new concept to a prior/foundational concept.
- One readable concept graph or mechanism diagram. Mermaid is acceptable only when the rendered labels are legible and the caption explains the point of the graph.

## Pipeline Report

Include:

- Research Coverage: candidate count, raw artifact count, selected-source artifact count, source-class breakdown, fan-out lane summary, and threshold pass/fail.
- Source log: verified, substituted, degraded, skipped.
- Ranking rationale table.
- Verification results with links to `sources/candidates.jsonl`, `sources/manifest.jsonl`, `reviews/fanout-report.md`, per-source read reports, and `verification/evidence-matrix.*`.
- Feedback or preference changes applied today.
- A/B comparison only if actually performed.
- Cost note: Codex-session generation; no Anthropic engine call from local scripts.

## Errata

Include even when empty:

```md
# Errata

- None.
```

If any source failed, unsupported claim was struck, image was unavailable, or tool was missing, report it here.

## PDF Quality Gates

The rendered PDF should pass both research gates and render gates.

Research gates:

- `sources/candidates.jsonl` exists and records at least 100 distinct screened candidates.
- Candidate coverage meets the source-discovery lane minimums, or the run explicitly blocks before rendering and reports why a lane could not be covered.
- `sources/manifest.jsonl` exists and records at least 20 locally saved raw artifacts with valid local paths.
- `reviews/fanout-report.md` exists and records subagent or wave-based source work.
- Raw subagent or wave outputs exist under `reviews/fanout/` or `reviews/subagents/`.
- For monthly/high-recall runs where the user requested discovery subagents by source lane, `reviews/fanout-report.md` must list the actual discovery subagent ids, lane quotas, completed counts, saved lane report paths, and any lane shortfalls.
- For runs where the user requested one source-specific subagent per selected artifact, `reviews/subagents/read-*.md` must contain one actual subagent-written report per selected artifact. Script-generated `reviews/read-workers/*.md` files are auxiliary evidence only and do not satisfy this gate without explicit degraded-run approval.
- At least one per-selected-source read report exists for the deep dive and each skim target.
- Selected-source read reports are substantive: deep dive reports include full-document/full-diff structure, evidence references, limitations, and figure/table or file/artifact inventory; skim reports include mechanism, limitations, and exact local evidence.
- `verification/evidence-matrix.md` or `verification/evidence-matrix.jsonl` exists.
- Every selected item has a local source artifact.
- Repo items have local diff, tag, commit, checkout, or source-file evidence; release-note-only repo items are degraded.
- Paper deep dives have saved PDF or full extracted text plus figure/table inventory.
- A source cannot be labeled `Verified` unless the evidence matrix references a local artifact path.

Render gates:

- Nonzero PDF.
- 8-30 pages target for daily runs. For monthly/high-recall runs, user-provided page targets override this daily range; if none is provided, use a longer monthly target only when the evidence depth supports it.
- Fonts embedded.
- Table of contents present.
- At least one readable explanatory diagram and one visual asset embedded. Mermaid diagrams are rendered as images so labels survive PDF generation.
- No generic diagram captions such as `Mermaid diagram 1`.
- Math text present.
- No unsupported code citations.
- Inline citation density passes the renderer gate.
- No forced long pseudocode block for paper/article targets.
- No unannotated, unreadable full-page paper screenshot used as the primary visual.
- No duplicated code blocks or diagrams, no boilerplate sentences repeated more than twice, no deep-dive pairs sharing over ~30% of their sentences, no truncated dive titles (template-redundancy gates).
- Read-report counts ignore sections whose heading mentions the renderer; evidence refs may be `path:line` or `path:start-end` in backticks.
- Feedback file exists next to PDF.

## Not Acceptable

- A PDF that only summarizes the repository or the skill.
- A PDF based on a small convenience set of sources when 100-source screening was possible.
- A PDF with extracted notes only and no raw local artifacts.
- A PDF that claims sources are verified without local artifact evidence.
- A PDF with placeholders, TODOs, or missing source citations.
- A PDF without visual content.
- A PDF that passes mechanical rendering while being too dense, unstyled, or hard to scan.
- A PDF whose main technical explanation is fake code instead of a source-aware mechanism trace.
- A PDF with empty-looking or illegible diagrams.
- A PDF whose deep dives or skim cards were stamped from a shared template: identical diagrams, identical snippets, or boilerplate paragraphs with only citation numbers swapped.
- A PDF generated by invoking the legacy Anthropic-backed engine.
- A PDF that is not ready for the user's daily reading session.

## Monthly Brief Contract

Apply this section for monthly/high-recall runs. Target 20-40 pages. The renderer enforces the heading set, the per-deep-dive schema, and the citation gates, and detects the monthly profile automatically.

### Required Order

1. Front matter (YAML metadata block).
2. Executive Synthesis.
3. Monthly Themes.
4. Deep Dives.
5. Skim Cards.
6. Change Maps.
7. Pipeline Report.
8. Month-Ahead Queue.
9. Errata.
10. Citation Appendix.

Use exactly these top-level headings: `# Executive Synthesis`, `# Monthly Themes`, `# Deep Dives`, `# Skim Cards`, `# Change Maps`, `# Pipeline Report`, `# Month-Ahead Queue`, `# Errata`, `# Citation Appendix`.

### Front Matter

Start `brief.md` with a YAML metadata block; the Typst template renders it as the cover page:

```md
---
title: "DeepBrief Monthly"
subtitle: "<one-line theme of the month>"
date: "<YYYY-MM-DD window start> to <YYYY-MM-DD window end>"
abstract: |
  At a glance: <deep-dive count> deep dives, <skim count> skims,
  <candidate count> candidates screened across 6 lanes, <artifact count>
  raw artifacts. Deep dives: <titles, comma-separated>.
---
```

If the block is missing, the renderer injects a generic title and date, so the cover degrades instead of failing — but write the block.

### Executive Synthesis

Write the month's mental model, not a table of contents: 3-5 load-bearing shifts, one short paragraph each, each linking to the deep dives that ground it and carrying inline citations. A reader who stops here should still leave with the month's shape.

### Deep Dives

- Group deep dives **by theme, not by source lane**, as `##` sections under the single `# Deep Dives` heading. Order themes by importance.
- Every deep dive uses the full subsection schema at `###` level: `### TL;DR`, `### Mental model`, `### Why this matters now`, `### Mechanism trace`, `### Evidence map`, `### Walkthrough`, `### Implementation notes`, `### Try it yourself`, `### Open questions`, `### Sources & citations`. The renderer checks each dive separately and names the dive in its error.
- Follow the three-layer pedagogy in order: mental model first (the 3-5 load-bearing ideas), then the mechanism reduced to its core flow, then the grounded walkthrough with real files/figures, ending in a 30-60 minute exercise.
- Each dive's `### Sources & citations` needs at least 3 citation lines; all daily deep-dive rules (inline evidence, real snippets, no pseudocode dumps) still apply.

### Skim Cards

Group skims **by lane** under `## <Lane>` headings, each lane opening with a one-line intro of what moved in that lane this month. Start each card with a blockquote verdict line so it renders as an accent panel:

```md
> **Verdict: adopt | watch | skip.** <one-line reason with citation> [n](#source-n)
```

Then the daily skim-card rules apply (what changed, why it matters, item ID, source URL, two inline references).

### Change Maps

Three maps, each a compact table plus interpreting prose: code/repo changes, paper/eval shifts, and company/product moves.

### Distinctness Rules

The renderer blocks template-stamped output:

- An identical code or Mermaid block appearing more than once is a blocking error. Every dive needs its own source-derived snippet and a diagram whose node labels name that source's actual components, not a generic pipeline flow.
- A sentence repeated more than twice, or two deep dives sharing more than ~30% of their sentences, is a blocking error. Write each dive and skim card from its own read report.
- Dive titles must be the full source title or a cleanly shortened form; mid-word truncation (for example `...(#2.`) is a blocking error.

### Table Rules

- At most 8 rows per table; split or prune longer ones.
- Keep the first column narrow (a name or key, not a sentence).
- Explanations go in the surrounding prose, not in cells.

### Citation Appendix

Write each entry as a heading with an explicit attribute so the anchor survives PDF conversion:

```md
### [3] <title> {#source-3}
```

Raw HTML anchors like `<a id="source-3"></a>` are dropped during conversion and the renderer rejects them.

## Course Book Contract

Apply this section when the user asks for a course-note book, lecture-note book, or any run whose deliverable is per-lecture teaching notes rather than a news brief. This contract overrides the daily and monthly structures entirely; do not coerce course content into the brief schemas. The renderer detects the profile from `# How to Use This Book` or `# Verification Appendix`, or pass `--profile course_book`.

### Required Order

1. Front matter (YAML metadata block; renders as the title page).
2. `# How to Use This Book`
3. `# Course Map`
4. `# Prerequisite Crash Course`
5. Unit chapters containing per-lecture and per-discussion sections.
6. `# Cheat Sheets`
7. `# Glossary`
8. `# Exam-Style Review`
9. `# Citation Appendix`
10. `# Verification Appendix`

### Lecture and Discussion Sections

- Every lecture gets its own heading matching `## Lecture <N>: <title>` (level 1-3). The renderer rejects duplicate lecture numbers, and with `--expect-lectures N` it rejects any missing lecture 1..N.
- Every discussion gets its own heading matching `## Discussion <id>`. With `--expect-discussions M` the renderer requires at least M distinct discussion sections.
- Each lecture section must contain, recognizably: learning goals, key terms, a full explanation, worked examples, common mistakes, self-check questions, and source citations. The renderer keyword-checks these per lecture section.
- Write each lecture section from that lecture's own subagent read report. Distinctness rules from the monthly contract still apply: no shared diagrams, no repeated sentences, no template-stamped captions.
- Page bounds are 60-400; a course book is long by design. Never compress lectures into merged "deep dives" to fit a brief page budget.

### Invocation

```bash
python scripts/render_brief.py --input <dir>/brief.md --out <dir> \
  --profile course_book --expect-lectures <N> --expect-discussions <M>
```

Applied-AI candidate-lane minimums and fanout-lane checks are skipped for this profile; label candidates with honest course lanes (lectures, discussions, transcripts, exams, projects) instead of forcing them into news lanes.

### Precedence Rule

When the user's prompt specifies an explicit output structure that conflicts with every renderer profile, stop and ask the user before composing — never silently reshape the deliverable to satisfy the renderer. A renderable wrong document is a failed run.
