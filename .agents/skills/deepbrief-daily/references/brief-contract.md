# Brief Contract

Use this file when writing `brief.md`.

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
- A PDF generated by invoking the legacy Anthropic-backed engine.
- A PDF that is not ready for the user's daily reading session.
