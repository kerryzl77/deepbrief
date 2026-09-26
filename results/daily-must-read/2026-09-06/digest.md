# Applied AI Engineering Must-Read Digest — 2026-09-06

**Window:** `2026-09-05T16:04:25Z`–`2026-09-06T16:04:25Z`. No paper appeared in the collected strict window, so item 3 uses the clearly labeled seven-day fallback (`2026-08-30T16:04:25Z` onward). Routine official Codex/Claude release notes were excluded.

## Ranked Top 3

| Rank | Source | Window | Why it earns the slot | Read |
|---:|---|---|---|---:|
| 1 | [SGLang: contain VLM EPD request lifecycle failures](https://github.com/sgl-project/sglang/commit/8ef646a5c65bd2f8922483057dddc02e2b0de18c) | Strict | A deep, test-heavy reconstruction of cancellation as resource ownership across TP work, transfers, request state, and cleanup. | 7 min |
| 2 | [LiteLLM: scope emulated file search to request stores](https://github.com/BerriAI/litellm/commit/942e6cb3cd4c1e3a3cbb4ab1571e122a2230a593) | Strict | One-line production fix with a durable rule: model output may narrow authority, never expand it. | 4 min |
| 3 | [A Blind Trust, the Bloody Thrust](https://arxiv.org/abs/2609.03884) | **7-day fallback** | The strongest paper-native treatment of lifecycle hooks as a supply-chain execution plane, useful despite material reproducibility limits. | 7 min |

## 1. SGLang: Cancellation Is an Ownership Transition

**Primary source:** [commit `8ef646a5`](https://github.com/sgl-project/sglang/commit/8ef646a5c65bd2f8922483057dddc02e2b0de18c)

**User/operator mental model.** In SGLang's disaggregated multimodal path, an encoder can be doing tensor-parallel collective work or transferring an embedding after the HTTP/gRPC caller has timed out. The request owns more than a response future: dispatch order, per-request state, metadata, staged buffers, destination counts, and native transfers have separate lifetimes. A cancelled caller therefore cannot simply free everything.

**Why it matters.** This is the same failure shape seen in agent tool runtimes: the parent coroutine ends while subprocess, IPC, GPU, or zero-copy work still owns state. Correctness requires transferring cleanup responsibility, not assuming cancellation propagated everywhere.

**What changed.** The eight-file patch validates requests before TP dispatch; serializes peer dispatch with rank-zero encode; drains dispatched tasks and native transfers through cancellation; sends abandoned DP requests over a separate release channel; preserves release intent that arrives before request state exists; coordinates preprocessing failures and layout digests across TP ranks before forward; and makes health probes retain the dispatch lock until their encode drains. It adds 45 named tests focused on adverse orderings.

**Key mechanism.** `await_task_completion_on_cancel` shields task-owned work and repeatedly drains it before re-raising cancellation. DP timeout/cancel drops caller bookkeeping but sends release intent outside the bounded encode queue. Request state records deferred release, while Mooncake destination completion is counted by normalized endpoint so retries do not consume multiple receiver slots.

**Engineering takeaways.** Model caller, compute, transfer, metadata, and cleanup lifetimes explicitly. Put cleanup control traffic on a path that cannot queue behind the work it must retire. Validate before entering distributed collectives, and test cancellation at each ownership handoff with controlled scheduling.

**Limitations/skepticism.** The tests were inspected, not run. They use mocks, fake TP groups, and controlled threads; there is no real NCCL/RDMA/IPC recovery result, throughput measurement, or proof of deadlock freedom. Draining can wait indefinitely on hung native work, and release messages remain best effort.

**Estimated read time:** 7 minutes.

## 2. LiteLLM: Model Output Is Not Retrieval Authority

**Primary source:** [commit `942e6cb3`](https://github.com/BerriAI/litellm/commit/942e6cb3cd4c1e3a3cbb4ab1571e122a2230a593)

**User/operator mental model.** The application places vector-store IDs in a `file_search` tool request. The model later emits a tool call that may include its own `vector_store_id`. The request is the authority boundary; the model's value is only a proposed narrowing choice.

**Why it matters.** The previous emulated handler accepted any truthy model-selected ID. LiteLLM's commit explains that the per-key permission check had only seen request IDs, so a later off-list value could select a store outside that checked scope. This is a compact confused-deputy pattern for every agent that turns model text into resource handles.

**What changed.** One production expression now accepts the model-selected ID only when it is a member of the request's store list. A listed ID narrows the search to one store; an unlisted ID falls back to all stores in the request. Two regressions inspect the actual IDs passed to the mocked search API and cover both branches.

**Key mechanism.** Authority is enforced at the point where parsed model output becomes a downstream search argument. The fix preserves capability for valid narrowing without allowing that choice to expand the effective set.

**Engineering takeaways.** Treat model-produced resource IDs, URLs, file paths, tenant IDs, and tool names as untrusted selectors. Test the downstream call argument, not only the final answer. Pair a negative confinement test with a positive capability-preservation test, and make fallback behavior explicit.

**Limitations/skepticism.** The patch assumes the request's effective store list was authorized correctly upstream; that path is outside the diff. The tests were not run and use mocked model/search boundaries. The artifact does not demonstrate a real data leak, credential path, native-provider behavior, or all file-search routes. An off-list value is not rejected or logged; it broadens back to the request list.

**Estimated read time:** 4 minutes.

## 3. Paper: Lifecycle Hooks Bypass the Model Decision Plane

**Primary source:** [arXiv:2609.03884](https://arxiv.org/abs/2609.03884) (**seven-day fallback**)

**Problem statement.** Agent harnesses bind lifecycle events such as session start or post-tool use to host-side commands. A benign plugin can establish trust, then ship an update that changes those bindings under the same identity. Once a matching event occurs, the harness may dispatch the command without the model selecting or interpreting it.

**Method.** HookPry combines three ideas: adversarial manifest optimization for discoverability, temporal decoupling between benign acceptance and hook-bearing update, and a least-common-interface adapter that maps an intended effect to each harness's native lifecycle schema. The evaluation conditions on installation/update delivery and checks synthetic external effects rather than trusting the model's report.

**Key evidence.** The authors report 770 passes, 34 partials, and 196 failures across 1,000 runs covering seven harnesses and 25 harness/backend combinations; no run received the formal `blocked` verdict. On a separate 50-target comparison, native hooks produced 46/50 verified effects versus 28/50 for mechanically translated MCP descriptions. On a fixed 40-malicious/40-benign static corpus, Defender found 0/40, Semgrep 19/40, HookPolicy 20/40, and their union missed 19/40 malicious bundles. These are reported results, not independently reproduced.

**Applicability.** Review plugin identity, changed hook bindings, update authorization, subprocess permissions, and tool-output provenance as one trust chain. Model refusal can affect whether an event happens; it cannot mediate a command the harness dispatches directly after a match. For evals, separate event generation, binding admission, subprocess dispatch, and externally verified effect.

**Limitations/skepticism.** The threat model assumes normal installation and update adoption, uses ephemeral synthetic environments, excludes implementation bugs and sandbox escapes, and does not test dynamic defenses. Product versions and full oracle records are missing; the implementation section is empty. The advertised anonymous repository was unavailable after a clone attempt and one page retry, so this source is marked degraded. The paper's tiny comparison p-value is omitted because its test treats the observed 92% native rate as fixed rather than using the paired outcomes. The ablations are analytical/structural, not matched empirical removals.

**Citation gate.** Passed. Xi Zhang was disambiguated through the paper email, official BUPT profile, DBLP/ORCID `0000-0002-2111-7385`, and matching OpenAlex record. The independent ResearchGate profile reports 1,819 citations, above the 1,000 threshold; see `verification/author-citation-audit.md`.

**Estimated read time:** 7 minutes.

## What I Would Read First

Read the SGLang patch report first. It supplies the most reusable systems model: cancellation ends a waiter, not necessarily the work or the resources that work owns.

## What I Would Prototype or Inspect

Add a fault-injection matrix to one agent runtime: cancel before dispatch, during IPC, during a blocking transfer, after result publication, and during cleanup. Assert resource ownership and late-error provenance at every boundary. Separately, add a negative test that feeds model-generated resource handles outside the request's authorized set, plus a hook-update review that requires fresh approval when executable bindings change.

## Audit

**1,770 candidates screened; 96 manifested local artifacts (91 usable downloads, 5 degraded fetches); 4 selected artifact files for 3 sources; 1 degraded selected source; paper citation gate passed.** Supporting reports and evidence are under `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-06/`.
