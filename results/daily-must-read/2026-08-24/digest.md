# Applied AI Engineering Must-Read Digest

**Run:** 2026-08-24  
**Primary window:** 2026-08-23 16:11:55Z to 2026-08-24 16:11:55Z  
**Fallback screened:** 2026-08-17 to 2026-08-23; not used  
**Reader:** senior applied AI engineer building coding agents, sandboxed runtimes, retrieval/document systems, evals, tracing, and production AI

## Ranked Top 3

| Rank | Must read | Area | Why it cleared the bar | Read |
|---:|---|---|---|---:|
| 1 | [The Compaction Cliff in Long-Running AI Agent Memory](https://arxiv.org/abs/2608.22752) | Agent memory and safety | Measures repeated loss of durable rules and proposes typed, deterministic retention operators. | 8 min |
| 2 | [Google ADK: per-invocation token-spend telemetry](https://github.com/google/adk-python/commit/dc00db51bc5dc195a21633b295aa9eac33732ccf) | Tracing and cost observability | Turns multi-call agent loops into one low-dimensional spend distribution without double-counting cumulative stream usage. | 5 min |
| 3 | [Docling: skip native segmented-page decode in full-page OCR](https://github.com/docling-project/docling/commit/963564c328717160ef5376afdca52b40619c707c) | Document AI runtime | Removes an intermediate PDF parse that full-page OCR discards and that can consume multiple GiB on vector-dense pages. | 4 min |

## 1. The Compaction Cliff in Long-Running AI Agent Memory

**Primary:** [arXiv paper](https://arxiv.org/abs/2608.22752)  
**Problem statement:** Agent runtimes usually compact safety rules, procedures, preferences, beliefs, and episodic logs with the same summarizer even though they have different distortion tolerances. In the authors' production-shaped setup, Claude Code `/compact` with Sonnet 4.6 retained 53% of safety rules after one compaction and 10% after five.

**Method:** Knowledge Triage classifies each knowledge item into one of five types, then routes it through deterministic operators. `TypeCompact` pins safety-critical content and budgets the rest by type. `TypeDecompose` copies every in-scope constraint into each partition. `TypeRetrieve` pins in-scope constraints ahead of relevance-ranked items. A verifier detects unsafe compactions and restores rules.

**Key evidence:** Across tested ratios, TypeCompact constraint recall was 1.00, 0.95, and 0.80 at 50%, 25%, and 10% compression, versus 0.53, 0.39, and 0.24 for the strongest listed single-shot LLM compactor. It stabilized at 96% recall through five rounds. On tau-bench retail, mean pass rate was 37.7% versus 28.6% with the full policy and 29.2% with hierarchical truncation. These are paper-reported results, verified against the preserved full PDF and tables, not independently reproduced.

**Applicability:** Treat durable policies and operator constraints as typed state with explicit retention invariants, not prose that merely shares a token budget with conversation history. Add a repeated-compaction eval to the harness: inject rule variants, compact for multiple rounds, and score exact scope, qualifier, and revocation survival. A fail-closed classifier with an audit queue is more defensible than asking a general summarizer to remember what matters.

**Limitations and skepticism:** The guarantee begins only after type and scope classification; false negatives remain the dangerous case. Five-class annotator agreement is only kappa 0.45, declarative-rule recall is below perfect, TypeDecompose overhead reaches 219%, and the retail policies were not token matched. The abstract's `2-4x` claim rounds actual ratios aggressively, and one LLMLingua recall discussion does not reconcile cleanly with Table 6. This is a strong retention architecture, not evidence that the resulting agent is broadly safe.

**Citation gate:** Passed. Coauthor Michael Granitzer is identity-matched through DBLP/ORCID and the University of Passau; public profiles report at least 4,989 citations, above the 1,000 threshold. See `verification/author-citation-audit.md`.

## 2. Google ADK Per-Invocation Token-Spend Telemetry

**Primary:** [Google ADK commit](https://github.com/google/adk-python/commit/dc00db51bc5dc195a21633b295aa9eac33732ccf)  
**User/operator mental model:** One agent invocation may contain several model calls, tool loops, cached prefixes, reasoning tokens, and server-side tool input. Before this patch, operators could count calls and inspect client-level usage, but lacked one distribution point for the complete invocation. The affected artifacts are OpenTelemetry histograms emitted when the invocation span flushes.

**Why it matters:** SLOs and cost controls usually operate at the user request or agent-run boundary, not the individual completion boundary. Whole-invocation distributions expose loop amplification and context growth while retaining separate client metrics for model/provider attribution.

**What changed:** Six experimental histograms now record input, output, total, cache-read input, reasoning output, and tool input tokens. Emission requires the ADK experimental-telemetry opt-in. Each point carries only `gen_ai.agent.name`; subset metrics overlap their parent totals and must not be summed together.

**Key mechanism:** Within a streaming model call, ADK filters to responses carrying usage metadata and takes the newest report because usage chunks are assumed cumulative. It then adds that call once to invocation totals and derives total tokens as input plus output. Goldens show two model calls, 100/25 and 150/50, becoming one invocation observation of 250 input, 75 output, and 325 total.

**Concrete engineering takeaways:** Mirror these dimensions at your own `run_agent` boundary; pair them with inference/tool-call counts; alert on high tail buckets rather than averages; keep agent names bounded; preserve client-level provider/model labels for pricing. Explicitly test cumulative usage chunks, trailing empty chunks, cancellation, nested agents, and mixed providers.

**Limitations and skepticism:** The aggregation assumes cumulative provider stream semantics; delta-reporting providers would be undercounted. The patch has no direct changed tests for multiple usage-bearing chunks, partial-error streams, nested/concurrent contexts, or nonzero tool-input usage through the full path. These are token-volume metrics, not monetary spend, and the names are experimental rather than stable OpenTelemetry semantic conventions.

## 3. Docling Full-Page OCR Skips Native Segmentation

**Primary:** [Docling commit](https://github.com/docling-project/docling/commit/963564c328717160ef5376afdca52b40619c707c)  
**User/operator mental model:** A PDF page can acquire text state from native segmented parsing or from full-page OCR. In full-page mode, OCR becomes authoritative and native text cells are discarded. The patch removes the redundant native decode while preserving enough page geometry and state for OCR and layout stages to proceed.

**Why it matters:** Vector-dense CAD and wiring PDFs can make native segmentation pathological even when OCR will replace the result. The commit reports multiple GiB of decode cost above 100,000 vector segments and successful conversion of a synthetic one-million-segment reproduction after the bypass.

**What changed:** Both standard PDF pipelines derive `skip_cell_extraction` automatically only when `do_ocr` is true and mode is `FULL_PAGE`. If no parsed page exists, the OCR stage constructs an empty page-sized `SegmentedPdfPage` with bottom-left geometry. Layout post-processing skips native text-line write-back instead of asserting. Tests cover policy resolution, preprocessing plumbing, missing parsed-page handling, and the layout guard.

**Key mechanism:** The optimization is semantic rather than heuristic: skip an intermediate representation only when the selected downstream mode deterministically discards it, then create the minimal replacement state required by downstream consumers.

**Concrete engineering takeaways:** Audit document pipelines for expensive parse products that an authoritative OCR or vision mode throws away. Make the bypass mode-derived, preserve explicit coordinate geometry, and test every consumer of the omitted state. Add resource regressions with vector-heavy PDFs to complement functional tests.

**Limitations and skepticism:** The multi-GiB and million-segment statements are commit claims; the patch includes no memory benchmark, dense-vector fixture, or profiler output. Full-page rasterization and OCR still have their own cost. Replacing an assertion with a broad no-op guard can also hide an unexpected missing parse from unrelated failures, so production tracing should record why parsing was skipped.

## What I Would Read First

Read the Compaction Cliff paper first, especially Algorithms 1-3, Table 6, Figure 3, Table 10, and the limitations section. It gives a concrete architecture for separating durable constraints from compressible working state, while also exposing exactly where the guarantee stops.

## What I Would Prototype or Inspect

1. Build a five-round compaction regression for your agent harness with imperative, declarative, conditional, scoped, and revoked rules.
2. Add invocation-level token histograms plus call counts to one production trace path; verify streaming semantics with recorded provider fixtures before trusting totals.
3. Run Docling before/after on one vector-heavy PDF under peak-RSS profiling and confirm OCR/layout equivalence, not just successful completion.

## Audit

**Candidates:** 1,786 distinct, 282 strict-window. **Manifest artifacts:** 70. **Selected source artifacts:** 5 across 3 sources. **Degraded selected sources:** 0. **Paper citation gate:** passed for Michael Granitzer. **Subagents:** 6 discovery readers and 3 source-specific full readers, all completed, 0 retries. **Artifact directory:** `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-24`.
