# Daily Applied AI Engineering Must-Read

**September 21, 2026** | Exact window ended `16:01:52Z` | Seven-day fallback used for rank 2 only

Two exact-window repository changes and one citation-qualified fallback paper cleared the bar. A technically strong paper, RRSI, was rejected after its primary arXiv timestamp proved to be after the cutoff.

| Rank | Must read | Focus | Why it made the cut |
|---:|---|---|---|
| 1 | [Microsoft Agent Framework: session-scoped file access](https://github.com/microsoft/agent-framework/commit/87d4d0a5cc22581c3920ea4dafb0dd969fb427ae) | Agent state isolation | A concrete, tested namespace boundary for preventing sessions from sharing harness-managed files by accident. |
| 2 | [An Empirical Study of Harness Design for Coding Agents](https://arxiv.org/abs/2609.20804) | Harness ablations | Controlled evidence that compaction, planning, and tool interfaces solve different failure modes rather than providing universal gains. |
| 3 | [Agno: typed page command and search results](https://github.com/agno-agi/agno/commit/af6e1ff734bd255b7f6b71f095c2a0fa52067094) | Retrieval semantics | Makes empty, partial, truncated, invalid, missing, and unavailable outcomes machine-distinguishable. |

## 1. Microsoft Agent Framework: isolate each session's virtual files

**Primary link:** [commit `87d4d0a`](https://github.com/microsoft/agent-framework/commit/87d4d0a5cc22581c3920ea4dafb0dd969fb427ae)  
**Window:** Primary, committed September 21 at 09:49 UTC  
**User/operator mental model:** Multiple sessions may share one `AgentFileStore`, but an opt-in session-scoped provider now gives each one a virtual root under `~access-/<derived key>/`. An explicit application scope can deliberately share a workspace across sessions.

**Why it matters:** File tools are persistent agent state. Without a workspace key, two sessions can read or overwrite the same logical files even if their conversational state is isolated.

**What changed and how:** Setup resolves explicit scope first, then session ID, derives a collision-resistant storage segment, creates the workspace, and fails closed if neither identifier exists. All eight read/write tools prepend that workspace. `ls` and `grep` now normalize their directory arguments before joining, and grep strips the internal prefix from returned paths. The patch adds separation, deliberate sharing, collision, traversal, relative-path, and backward-compatibility tests.

**Engineering takeaways:** Derive workspace identity once from authenticated server state and capture it in every tool closure. Test accidental sharing, intentional sharing, missing identity, identifier collisions, traversal, and result-path ergonomics separately.

**Limitations/skepticism:** The feature is opt-in; legacy behavior remains shared by default. It is logical store-path isolation, not a process, container, credential, ACL, or encryption boundary. Helper implementations and backend-specific symlink/concurrency behavior were outside the patch, and tests were inspected but not run.

**Estimated targeted read time:** 6 minutes.

## 2. Harness design is conditional on the model's failure mode

**Primary link:** [arXiv:2609.20804](https://arxiv.org/abs/2609.20804)  
**Window:** Seven-day fallback, submitted September 17 at 17:58 UTC  
**Problem:** Coding-agent scores conflate model capability with planning, action interfaces, and context management. The paper fixes one ReAct loop and varies those three components across four models, SWE-bench Verified, Terminal-Bench 2.1, and four context budgets.

**Method:** Five context policies range from no management to staged stale-output elision, recoverable storage, and same-model summarization. A persistent `update_plan` protocol is toggled at the 128k/T4 setting. The action-space comparison uses eight structured tools plus bash versus bash-only.

**Key evidence:** On SWE-bench, managed context beats no management by 35.7 points at 32k but only 2.7 at 128k; unmanaged overflow falls from 78.7% to 8.7%, while managed tiers have zero overflow failures. Staged elision-before-summary has the best aggregate token-cost profile. Recall shows no aggregate gain over elision and is never called in 36 of 64 recall-enabled settings. Planning lifts the 30B model from 13.6% to 25.2% on SWE-bench by preventing early abandonment, but mainly shortens and cheapens stronger-model trajectories. Bash-only helps the strongest Nemotron yet hurts Mistral by 23.2 points on SWE-bench, showing the interface effect is workload- and model-specific.

**Applicability:** Measure overflow, no-edit exits, phase-specific turns, recall usage, tool-selection errors, and verification loops before adding machinery. Stage cheap deterministic compaction before model summarization, and expose the smallest action vocabulary the target model can use reliably.

**Limitations/skepticism:** Each task-setting has one trajectory. Planning and action-space ablations occur only at T4/128k. The action-space treatment bundles tool schemas, prompts, file-state tracking, and diagnostics, so it cannot isolate tool count alone. Models and benchmarks are limited and exclude current frontier production coding agents.

**Citation gate:** Passed through Hamed Zamani's institution-matched OpenAlex profile with 4,238 citations.  
**Estimated targeted read time:** 8 minutes.

## 3. Agno turns retrieval status into data instead of prose

**Primary link:** [commit `af6e1ff`](https://github.com/agno-agi/agno/commit/af6e1ff734bd255b7f6b71f095c2a0fa52067094)  
**Window:** Primary, committed September 21 at 10:47 UTC  
**User/operator mental model:** Agno presents published documentation pages as a read-only virtual filesystem with emulated `ls`, `cat`, and `rg`-like commands, plus ranked page search. These are constrained corpus operations, not host-shell execution.

**Why it matters:** A service outage, a valid zero-hit search, and a search stopped by a deadline must not collapse into the same “no information” response.

**What changed and how:** `PageCommandResult` adds structured text, error codes, partiality, truncation, continuation, and stop reason. Execution paths set those fields directly, so error-looking prose inside a document remains successful content. The implementation distinguishes valid empty output, partial grep, invalid grammar, missing pages, unavailable storage, and final JSON clipping. It bounds the complete UTF-8 JSON envelope and removes continuation after clipping so callers cannot skip unseen content. MCP exposes structured success and protocol errors; the existing chat surface remains backward-compatible text/JSON.

**Engineering takeaways:** Model retrieval as an algebra such as `success | empty | partial | error`, with machine-readable reasons and safe continuation. Evaluate downstream behavior separately for zero hits, output caps, deadline stops, missing pages, and service failure.

**Limitations/skepticism:** This does not improve ranking, embeddings, freshness, or recall, and it does not make the model respect status fields. MCP command errors become `ToolError` text rather than returning the full typed error object. Zero-hit ranked search lacks a dedicated new regression test. The reported 267 passing tests were not rerun here.

**Estimated targeted read time:** 6 minutes.

## What I would read first

Read the harness-design paper's Tables 3-5 and limitations first. The durable lesson is not “always use planning” or “bash beats tools”; it is to identify the model's actual failure mode and ablate one harness mechanism at a time.

## What I would prototype or inspect

Build one cross-cutting eval matrix: session A/B file isolation, then retrieval outcomes `empty`, `partial`, `missing`, and `unavailable`, under 32k and 128k context budgets. Grade both task success and provenance: which workspace was accessed, whether partial evidence was disclosed, and whether the agent retried or abstained on tool failure.

## Audit

173 curated candidates after broad screens of 1,685 arXiv records, 100 daily-paper records, 314 repository events, and 42 engineering pages; 158 preserved local artifacts; 8 selected artifacts; 0 degraded selected sources; 1 non-material degraded supporting artifact excluded from evidence. Paper citation gate: **PASS**. Coordinator plus seven workers verified as `gpt-5.6-sol` with `high` reasoning. No source code or tests were executed. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-21`.
