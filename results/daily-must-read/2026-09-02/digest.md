# Applied AI Engineering Must-Read Digest

**2 September 2026**  
Strict discovery window: `2026-09-01 16:05 UTC` to `2026-09-02 16:05 UTC`. All selections are strict-window; the seven-day fallback was not needed.

## Ranked Top Three

| Rank | Source | Layer | Why it cleared the bar | Read |
| ---: | --- | --- | --- | ---: |
| 1 | [Stagehand: generalized external-agent benchmark harness](https://github.com/browserbase/stagehand/commit/ad33f63f7172a08155ab70f086b28672a956a38e) | Cross-agent eval infrastructure | Replaces copied harness implementations with a registry, shared lifecycle, normalized evidence boundary, and a Python/MCP proof case. | 7 min |
| 2 | [ToolGate](https://arxiv.org/abs/2609.02067) | Benchmark construction paper | Converts generated evaluation items into executable acceptance decisions, then documents where its first protocol fooled itself. | 7 min |
| 3 | [LiteLLM: bounded MCP `tools/list` pagination](https://github.com/BerriAI/litellm/commit/5767a2da0f6d28a07cf431fbd652678b3223867b) | Tool-catalog reliability | Makes discovery multi-page and bounded, while exposing an important missing completeness contract. | 5 min |

## 1. A Common Evidence Boundary For External Agent Harnesses

**Primary link:** [Stagehand commit `ad33f63`](https://github.com/browserbase/stagehand/commit/ad33f63f7172a08155ab70f086b28672a956a38e), with the [Deep Agents adapter](https://github.com/browserbase/stagehand/commit/0a5e7a4f3f8ab7d213c08a51e1bcb88b4c69a377) as its proof case.

**User/operator mental model.** A benchmark runner executes the same browser task through different coding-agent harnesses. Each harness has its own SDK, process model, tool mounting, event stream, stop reasons, and cleanup behavior. Without a stable outer contract, apparent model comparisons also compare bespoke integration code.

**Why it matters.** This refactor makes the harness adapter the explicit compatibility boundary. A new runtime supplies supported tool surfaces, default models, setup, and execution; shared code owns planning, verifier state, result parsing, trajectory grading, metrics, and teardown.

**What changed.** `defineExternalHarness` and a registry replace closed unions and duplicated Codex/Claude Code lifecycle logic. Shared resolvers select tool surfaces and startup profiles. A runner-owned facade bridge exposes the browser tool server through loopback JSON-RPC while retaining evidence such as URL, ARIA state, and screenshots. The companion Deep Agents commit exercises the abstraction with a Python child process, MCP tool mounting, JSONL events, redaction, bounded draining, and `SIGTERM`-to-`SIGKILL` escalation.

**Key mechanism.** The common path is: registry entry -> task plan -> tool adapter -> runtime-specific agent -> normalized trajectory/result -> shared verifier -> deterministic cleanup. Runtime-specific code stays on the process and event-conversion edges.

**Concrete engineering takeaways.** Version the normalized event/result contract; distinguish unavailable telemetry from zero; include concrete tool-server and adapter versions in every run; and test differential capability parity, not just whether each harness starts.

**Limitations/skepticism.** These are implementation and unit-test artifacts, not comparative benchmark results. Normalizing fields cannot guarantee equivalent tool semantics or faithful SDK telemetry. The connected Deep Agents smoke run is author-reported, and the bridge does not establish isolation against a compromised local process or host-network boundary.

**Estimated read time:** 7 minutes.

## 2. ToolGate: Generated Eval Items Are Proposals, Not Data

**Primary link:** [arXiv `2609.02067`](https://arxiv.org/abs/2609.02067)

**Problem statement.** LLMs can cheaply generate scientific benchmark questions, answers, and solution scripts, but generation does not prove that the script reproduces the answer, that the question requires the target software, or that a tool-enabled agent can solve it independently.

**Method.** ToolGate applies three gates: execute the submitted script in the target environment and require exact answer agreement; reject items solved by a no-tool model under three independently shuffled option orders; then require a fresh tool-enabled agent to solve the survivor within a fixed budget. A run database records models, budgets, presentations, and outcomes.

**Key evidence.** In FEniCSx, 500 generation attempts became 478 locally verified candidates, 256 after two randomized lightweight screens, 135 after a GPT-5.5 medium-reasoning screen, 130 tool-agent successes, and 128 unique survivors. More importantly, the original fixed-order screen was biased: the generator put the answer at C 43.9% of the time while the screener selected C in 66% of calls. The corrected shuffle-and-value protocol changed 191 of 260 original “easy” labels.

**Applicability.** Store an acceptance receipt per eval item: environment/tool digest, executable witness, no-tool protocol and outcomes, tool-agent protocol and outcomes, presentation randomization, budgets, and dedupe identity. Order gates from cheap deterministic checks to expensive agent runs.

**Limitations/skepticism.** A later semantic audit found a data-layout defect in 97 of 130 pre-deduplication survivors. The three gates therefore establish operational consistency, not semantic validity. Results are protocol-relative, use one generator family and one scientific domain, and compare a direct no-tool call with a multi-turn scaffolded tool agent. Code and the run database were promised but absent from the inspected artifacts.

**Citation gate.** Passed. Maziar Raissi’s UC Riverside-matched [OpenAlex profile](https://openalex.org/A5012536010) reports 32,128 citations.

**Estimated read time:** 7 minutes.

## 3. MCP Catalog Enumeration Needs A Completeness Contract

**Primary link:** [LiteLLM commit `5767a2d`](https://github.com/BerriAI/litellm/commit/5767a2da0f6d28a07cf431fbd652678b3223867b)

**User/operator mental model.** An MCP gateway must enumerate a server's entire tool catalog before it can expose, filter, or authorize tools. A one-page implementation silently hides later tools; an unbounded implementation can hang on malformed cursor behavior.

**Why it matters.** Tool discovery is part of the agent's effective capability set. Silent truncation and unmarked partial catalogs can change tool selection and approval policy without an obvious runtime failure.

**What changed.** A shared helper now follows `nextCursor` across pages for `MCPClient`, native tool loading, OpenAI-format conversion, and the REST preview path. It imposes a 1,000-page cap and a whole-walk deadline derived from listing and per-server client timeouts. Empty cursors terminate; repeated cursors, the page cap, or deadline expiry return the accumulated prefix.

**Key mechanism.** One cursor walker centralizes termination and timeout semantics, while the preview layer keeps its explicit timeout response and forwards server-specific timeout configuration.

**Concrete engineering takeaways.** Represent catalog enumeration as `{tools, complete, stopReason, pages, finalCursor, revision}` rather than a bare list. Trace repeated cursors and deadlines, deduplicate stable tool identities, and test auth refresh or catalog mutation between pages.

**Limitations/skepticism.** The current return type does not mark a prefix as partial. A normal second-page exception can still discard the first page under the existing non-raising client path. There is no snapshot consistency, deduplication, per-server page-cap override, real-server OAuth test, or pagination metric in the inspected patch.

**Estimated read time:** 5 minutes.

## What I Would Read First

Read ToolGate first if you own evals: the answer-position postmortem and the 97-item semantic failure are more useful than the headline funnel. Read the Stagehand diff first if you are currently adding another agent runtime to a shared benchmark.

## What I Would Prototype Or Inspect

Prototype two typed envelopes: a versioned cross-harness trajectory/result contract, and an MCP catalog result carrying explicit completeness and stop reason. Then add ToolGate-style acceptance receipts to the eval cases used to validate both envelopes.

## Audit

- Candidates screened: **1,534** distinct records (**567** strict-window)
- Successful local artifacts before synthesis: **94**; blocked artifact responses: **1**
- Selected sources: **3**; selected artifacts: **5**
- Degraded selected sources: **0**
- Paper citation gate: **passed**
- Discovery assignments/full-read subagents: **6 / 3**; no selected-source retries required
- Coverage limitation: company/blog/discourse feeds timed out after GitHub and arXiv collection
- Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-02`

Every material claim maps to a local primary artifact in `verification/evidence-matrix.md`. Recommendations are engineering inferences, not source claims.
