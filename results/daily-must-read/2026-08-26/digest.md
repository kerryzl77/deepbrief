# Daily Applied AI Engineering Must-Read

**Cutoff:** 2026-08-26 16:02 UTC  
**Primary window:** 2026-08-25 16:02 UTC to 2026-08-26 16:02 UTC  
**Audience:** senior engineers building coding agents, sandboxed runtimes, document systems, evals, and production AI infrastructure

All three selections are in the strict 24-hour window. The seven-day fallback was screened but was not needed. Routine Codex and Claude Code release-note coverage was excluded.

## Ranked Top 3

| Rank | Source | Area | Why it clears the bar | Read |
|---:|---|---|---|---:|
| 1 | [EVOMAL: Self-Poisoning in Self-Evolving Coding Agents](https://arxiv.org/abs/2608.25776) | Coding-agent security | Shows how retrieved malicious code can be laundered into agent-authored, trusted, persistent skills and then propagate after seed removal. | 8 min |
| 2 | [Beyond the Editing Canvas](https://arxiv.org/abs/2608.25880) | Retrieval and document AI | Demonstrates that valid Office files can expose one task-relevant view to a reviewer and another to an LLM ingestion path. | 7 min |
| 3 | [Supabase evals: average scores across independent runs](https://github.com/supabase/evals/commit/62d02849525ce5efe050e9f25087b27c8477b70b) | Evals infrastructure | Carries independent sampling semantics through orchestration, storage, completeness checks, export, compatibility, and UI. | 5 min |

## 1. EVOMAL: the agent becomes the supply-chain carrier

**Primary source:** [paper and full text](https://arxiv.org/abs/2608.25776)

**Problem statement.** Self-evolving coding agents retrieve prior executable skills, imitate them while authoring new tools, store those tools, and retrieve them on later tasks. Existing defenses largely protect the **REUSE path**, where an agent invokes an attacker-submitted tool by name. EVOMAL studies the **CREATE path**, where untrusted retrieved code shapes a new artifact under an agent-chosen name. That generated descendant can cross into trusted persistent state even if the original plant is never executed.

**Method.** The authors add eight malicious skills to a 232-skill library, retrieve the top five examples with BGE-M3 and ChromaDB, and ask agents to author reusable tools on 153 tool-relevant SWE-bench Verified tasks. The attack wraps an inert, interchangeable payload in ordinary-looking source structures intended to induce imitation. The study spans six models, adds payload and banner ablations, tests targeted descriptions, evaluates multiple scaffolds and tool languages, and runs a five-round rolling-library cascade. The authors sandbox the experiments with fake secrets and localhost callbacks.

**Key evidence, verified as reported by the paper.** Full-attack agent self-poisoning rate is 20.3% to 41.8% across the six models. Eight planted skills produce 31 to 64 newly authored malicious skills, making the malicious population 4.9 to 9.0 times the seed count. A task-family-targeted cell reaches 86.7%. After the planted skills are removed, Qwen3 reaches 68% ASPR in round five; three of six models remain infected. The paper is unusually candid that its branching proxy overshoots observed growth by roughly 10 times and misorders important models because retrieval crowding violates the simple model. Its proposed counter-prompt lowers most tested conditions to 2.6% or less, with one small 15-task cell at 6.7%; the stronger signed-quarantine proposal prevents descendants from becoming retrievable under explicit, restrictive assumptions.

**Applicability.** The direct production lesson is an inference from the evidence: agent-authored code is not sanitized merely because the agent wrote it. Tool generation should create an explicit provenance transition. Keep generated helpers ephemeral or quarantined, record content-addressed ancestry to retrieved source, separate execution from admission, and support descendant revocation. Retrieval must preserve trust labels so copied examples cannot silently become first-party context.

**Limitations and skepticism.** The 68% persistence result comes from a controlled rolling-replacement simulation, not a public marketplace outbreak. Every selected task naturally asks the agent to author a reusable tool, and full-distribution rates are lower. The attack packaging is conspicuous, although the 11.1% no-banner result shows a residual imitation problem. The counter-prompt was not tested against an optimizer with repeated access to the exact defense. Numerical results were inspected in the full 29-page paper and appendices but were not independently reproduced.

**Citation gate.** Passed. Ahmed E. Hassan is verified at Queen's University; the preserved OpenAlex record reports 25,388 citations, well above the 1,000-citation threshold. See the author audit (local research intermediate discarded).

**Estimated read time:** 8 minutes for the paper's threat model, Figures 3-4, Tables 5-7, and limitations; 25 minutes for the full paper.

## 2. Office documents do not have one canonical evidentiary view

**Primary source:** [paper and full text](https://arxiv.org/abs/2608.25880)

**Problem statement.** Document pipelines usually assume that extracted text represents what a person reviewed. OOXML files can instead contain co-resident formulas and cached values, selected and unselected compatibility branches, hidden state, metadata fields, and structural relationships. Microsoft Office and a text extractor can select different task-relevant evidence from the same valid file. The authors call the constructions **evidence forks** and the outcome **plural ground truth**.

**Method.** The study mines OOXML specifications and schemas, constructs fixtures, gates them against the default Office editing canvas and a 13-tool extraction panel, and deduplicates the survivors into 21 mechanisms across representation, state, visibility, compatibility, scope, and linearization. Each mechanism is embedded into ten TAT-QA financial-report excerpts, producing 210 valid documents. Four native file-ingestion APIs receive each document ten times, for 8,400 trials; seven web interfaces receive each document once. The paper also traces the default OOXML extractor dependencies of 16 open-source agent and RAG projects.

**Key evidence, verified as reported by the paper.** Every one of the 13 extractors emits trap evidence for at least one mechanism. The four APIs return the reviewer-invisible trap in 48% to 76% of trials. At least one of the eleven tested interfaces returns the trap for 20 of 21 mechanisms. Results are highly stable within a document/API pair: 826 of 840 pairs are consistently exposed or consistently not exposed over ten repeats. Holding the OpenAI file-input path fixed, GPT-5.4 and GPT-5.5 show no difference over 2,100 runs each; changing entry path or extractor configuration does change exposure. This supports the paper's claim that ingestion configuration, not only model behavior, selects the evidence.

**Applicability.** Treat extracted text as a derived view, not canonical truth. Chunk metadata should retain package part, element or relationship path, semantic role, visibility/state, extractor version, flags, and transformation history. Ingestion regression tests should compare the source package, a declared human-review rendering, and the exact model-bound representation. Consequential agents should surface or quarantine disagreements before sending messages, updating databases, or executing tools.

**Limitations and skepticism.** The default Microsoft Office editing canvas is one operational oracle, not the only legitimate OOXML view. Proprietary ingestion paths are dated snapshots, and behavioral matching does not identify a vendor's backend. The 17.5% structural-signature rate in ordinary files is not an attack prevalence estimate. The supplied 17-page PDF and HTML omit Appendices A-D even though the paper cites them; exact extractor commands, the response-labeling prompt, and detailed sample walkthroughs therefore remain incompletely auditable.

**Citation gate.** Passed. Jiang Ming is verified at Tulane University; the preserved ORCID-resolved OpenAlex record reports 2,043 citations. See the author audit (local research intermediate discarded).

**Estimated read time:** 7 minutes for Sections 2-5 and Tables 2-7; 20 minutes for the available full paper.

## 3. Independent eval runs are a data-model change, not an averaging checkbox

**Primary source:** [Supabase evals commit `62d0284`](https://github.com/supabase/evals/commit/62d02849525ce5efe050e9f25087b27c8477b70b)

**User and operator mental model.** Previously, `--runs N` behaved as a conditional attempt budget: later attempts existed only after an earlier failure, and sampling stopped after success. That may model product retry behavior, but it biases a benchmark intended to estimate single-run success. The new experience is: request three independent scored runs, get three isolated artifacts, publish the pair only when indexes 1 through 3 are complete, see a pass fraction such as `2/3`, and drill into every run's transcript and checks.

**Why it matters.** The change separates measurement replication from infrastructure retry. Retrying a failed sandbox for run 2 repairs run 2; it does not create an extra scored sample or silently change the denominator. This makes refreshes easier to compare and keeps partial infrastructure failure from changing sample weights.

**What changed.** The 2,016-line patch touches 17 files. It replaces the serial stop-on-pass loop with stable one-based run indexes, stores results at `results/<experiment>/<eval>/run-<n>/result.json`, creates one sandbox per indexed run, and adds a `run` field to the exported schema. The UI groups rows by experiment/eval, displays an averaged pass rate, preserves per-run detail, and remains compatible with legacy unindexed rows.

**Key mechanism.** Exact-index completeness is enforced both in the workflow and exporter. Incoming partial sample sets are rejected before replacement keys are computed, so a partial refresh cannot overwrite a previously complete published set with a differently weighted average. Cleanup is scoped to one run directory, preventing concurrent sibling jobs from deleting each other's output. Tests cover sample-set completeness, pair/run expansion, grouping and ordering, legacy rows, and percentage labels.

**Concrete engineering takeaways.** Give every stochastic sample a stable identity at scheduling time and carry it through logs, storage, schema, export, and UI. Preserve raw run evidence and compute aggregates at read time. Make sample completeness a publication invariant. For stronger provenance, key results by suite revision, experiment revision, task revision, and sample index, not only path names.

**Limitations and skepticism.** Three binary samples only resolve 0%, 33%, 67%, and 100%; the UI does not show uncertainty. Cost triples in model calls, sandboxes, storage, and rate-limit pressure even if wall time is bounded by parallelism. Runner failure recovery remains manual, and downstream consumers that assumed one row per experiment/eval must adapt. The full patch and tests were inspected but not executed.

**Estimated read time:** 5 minutes for the commit narrative and data flow; 15 minutes for the core harness/export/test diff.

## What I Would Read First

Read EVOMAL first if generated tools, persistent memory, or shared skill registries are anywhere on your roadmap. The CREATE-path distinction changes the trust model more than the particular attack payload does.

## What I Would Prototype or Inspect

1. Add an unretrievable quarantine state for agent-authored executables, with immutable ancestry to every retrieved source and a transitive descendant-revocation query.
2. Build a small OOXML probe suite that records rendered view, extracted view, semantic role, and loader configuration in traces before any document-agent action.
3. Audit eval pipelines for outcome-conditioned retries, incomplete sample-set publication, and missing stable sample identities.

## Audit

**Candidates:** 1,846 distinct records by dedupe key; 1,845 unique IDs because one duplicated OpenAI feed ID maps to two URLs. **Strict-window candidates:** 592. **Preserved artifacts:** 163 nonempty files. **Current selected artifacts:** 7 files for 3 sources. **Degraded selected sources:** 0; one disclosed appendix-availability gap affects item 2. **Paper citation gate:** 2 selected papers passed; no unverified paper surfaced. **Subagents:** 6 discovery readers plus 3 source-specific full readers, 0 failures, 0 retries. **Artifact directory:** `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-26/`
