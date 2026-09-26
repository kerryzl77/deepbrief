# Daily Applied AI Engineering Must-Read

**July 23, 2026**  
**Estimated reading time: 17 minutes**

Two strict-window runtime changes cleared the bar. No qualifying paper landed
inside the strict 24-hour window, so the paper slot uses the 7-day fallback:
DocOps, published July 22 before the strict cutoff and accepted only after the
author-citation gate and a complete 1,647-line read.

| Rank | Window | Topic | Must-read | Read |
|---:|---|---|---|---:|
| 1 | Last 24h | MCP runtime | [Codex: publish MCP state atomically and reuse unchanged connections](https://github.com/openai/codex/commit/e497325a6a1743cfadeee41a6b5f05ebf7fd0221) | 6 min |
| 2 | Last 24h | Agent control plane | [Claude Agent SDK: a result ends a turn, not necessarily the run](https://github.com/anthropics/claude-agent-sdk-python/commit/e6e07f1c9b0542217e1cf4913e96b161a6bf92b2) | 5 min |
| 3 | 7-day fallback | Document-agent evals | [DocOps: verify native artifact state and preservation](https://arxiv.org/abs/2607.19865) | 6 min |

## 1. Codex: refresh MCP state without changing work already in flight

**Primary sources:** [runtime ownership commit](https://github.com/openai/codex/commit/e497325a6a1743cfadeee41a6b5f05ebf7fd0221) and [connection-reuse commit](https://github.com/openai/codex/commit/e19e65317a333ce725b18ac6f1e3bc904b74d2a1)

### User and operator mental model

An MCP server gives a Codex thread tools or resources. Its effective behavior
depends on more than the server URL: environment variables, authentication,
tool filters, timeouts, plugin provenance, approval policy, and sandbox
permissions all matter.

Suppose you change one of those settings while Codex is working. The new model
is temporal:

1. The current model step keeps the exact tool catalog, connection, and
   approval/sandbox authority it captured. A refresh cannot change the meaning
   of a tool between advertisement, approval, and execution.
2. Codex marks the thread's MCP state dirty, builds a complete replacement, and
   publishes it atomically before the next model step or direct MCP operation.
3. If only view settings changed, such as tool filters, timeouts, metadata, or
   provenance, the new view can reuse the same ready server connection. The
   user avoids an unnecessary restart and `tools/list` round trip.
4. If transport, environment, auth/OAuth, or client capabilities changed,
   Codex reconnects because the old transport no longer represents the same
   authority or execution context.

There is no new user-facing control in these patches. The experience is fewer
refresh stalls and a stronger guarantee that an in-flight step cannot observe
a torn mix of old and new MCP state. The affected state is the thread's
published MCP configuration, live connections, server views, plugin
availability, capability roots, and approval authority, not the user's files.

### Implementation mechanism

A thread now owns one stable `McpRuntime`. It atomically swaps a complete
`PublishedMcpRuntime`, while each sampling step captures an immutable
`McpBinding`. Prepared tool calls retain their captured client and config.
Refreshes are serialized; cancellation restores the dirty bit so the next
operation retries rather than silently accepting stale state.

The follow-up separates a shared `McpServerConnection` from a
publication-specific `McpServerView`. A ready connection is reused only when a
defined connection identity matches. New filters, timeout, metadata, and
elicitation authority are layered over that shared transport; old bindings keep
their old view.

### Engineering takeaways

- Model mutable runtime configuration as versioned publications, then lease one
  immutable version to each step and prepared side effect.
- Classify every setting as connection-defining or view-only, and test that
  matrix. Misclassification is now the main correctness risk.
- Keep server-initiated approval authority current as one atomic tuple, while
  preserving model-authorized call authority from advertisement through
  execution.

### Limitations and skepticism

The patches and tests were inspected but Codex was not built. Reused
connections deliberately do not relist tools, so an out-of-band server catalog
change can remain invisible until a hard refresh or reconnect. A refreshed
publication can also contain non-required servers whose startup later fails;
publication is not globally rolled back. A later same-day follow-up tightened
closed-connection reuse, but it was outside this selected two-patch read.

## 2. Claude Agent SDK: stdin is a live control channel

**Primary source:** [anthropics/claude-agent-sdk-python commit e6e07f1](https://github.com/anthropics/claude-agent-sdk-python/commit/e6e07f1c9b0542217e1cf4913e96b161a6bf92b2)

### User and operator mental model

The Python SDK drives a Claude CLI subprocess. Its stdin is not just where the
initial prompt goes; it remains the return channel for Python hooks and
in-process SDK-MCP tool responses.

In the reproduced failure, a parent turn launched a background subagent and
then emitted a `result`. The SDK interpreted that first result as the end of the
whole run and closed stdin. The background subagent continued: built-in tools
ran without the expected `PreToolUse` callback, while an SDK-MCP tool failed
with `"Stream closed"`. A later result still arrived, proving that the first
frame ended a turn, not the run.

After the patch, finite background agent/workflow tasks keep stdin open across
the intermediate result. Their hook decisions and SDK-MCP responses still
flow. Once the task reaches a terminal lifecycle event, the next result closes
stdin so an ordinary one-shot query can exit.

### Implementation mechanism

`Query` now keeps a per-run set of in-flight task IDs. `task_started` adds
`local_agent` or `local_workflow`; terminal `task_updated` or
`task_notification` removes it. A result closes input only when that set is
empty. Long-lived shells, monitors, teammates, and remote observers are
deliberately excluded because waiting for their terminal event could hang the
query forever. Tests cover intermediate/final results, duplicate lifecycle
events, malformed updates, excluded task types, and a never-ending shell.

### Engineering takeaways

- Specify whether every completion frame closes a step, turn, task, or run.
- Treat EOF as a protocol action. Closing early can remove policy enforcement;
  never closing can deadlock process teardown.
- Monitor expected hook callbacks as a control invariant. A successful built-in
  tool execution does not prove the policy channel was alive.

### Limitations and skepticism

This is explicitly a heuristic mitigation. If a task reaches terminal state
just before the parent result, the ledger is empty and stdin can still close
before the continuation turn. The durable fix is an explicit CLI
`run_complete` signal. The source reports live-CLI reproduction and full test
suites, but this digest did not independently rerun them.

## 3. DocOps: evaluate the native artifact, not the plausible trace

**Primary source:** [arXiv 2607.19865v1](https://arxiv.org/abs/2607.19865)

### Problem statement

Document-agent benchmarks usually score read-only question answering or UI
workflow completion. Neither proves that an edited XLSX, DOCX, PPTX, or PDF
reached the requested native state while preserving formulas, styles, tables,
bookmarks, hierarchy, and unrelated content.

### Proposed method

DocOps defines **210** controlled, synthetic tasks over native documents:
50 atomic edits, 40 short compositions, 60 single-document workflows, and 60
cross-document workflows. Each Harbor task bundles source files, an
instruction, optional skills, and an offline deterministic verifier.

The verifier reopens the submitted artifact with format-native libraries and
checks three contracts: requested structural state, task-specific linguistic
anchors where exact text would be too narrow, and preservation of specified
out-of-scope state. A task passes only if the output exists and every required
predicate succeeds; runtime errors, timeouts, missing files, and verifier
failures all count as failure.

### Key evidence

- Verifier decisions agreed with one expert audit on **122/128** sampled cases
  (95.31%; three false passes and three false fails).
- Controlled mutations were detected in **174/180** cases (96.67%), with native
  structure the weakest mutation category at 33/36.
- The best tested system, GPT-5.5 with Codex and skills, passed **0.671** of the
  210 tasks. GPT-5.5's average fell from **0.725 on L1** to **0.237 on L4**.
- Skills were not uniformly beneficial. Effects changed by model and harness,
  and some configurations regressed.

### Applicability

For a production document or retrieval-to-document agent, define the final
file as the evidence object. Reopen it with an independent parser, assert both
requested edits and preservation invariants, recompute derived values, and
fail the run when required evidence is missing. Evaluate the model, harness,
tools, step budget, and skills as one system.

### Limitations and skepticism

The files are compact synthetic artifacts, not messy enterprise documents.
Each configuration appears to run each task once; there is no run-to-run
reliability estimate. Harness comparisons are confounded by interfaces,
temperatures, budgets, and available model pairings. One auditor performed the
verifier study, and the 128-case pass/fail balance is not reported. DocOps is
also not a retrieval benchmark: it does not measure search recall, ranking, or
attribution.

### Citation gate

**PASS.** Exact coauthor [Xianpei Han](https://openalex.org/A5100620300) matches
the paper's CAS/Institute of Software affiliation and had **4,573 OpenAlex
citations** at collection time, above the hard 1,000-citation threshold.

## What I would read first

Read the Codex patches first. The reusable mental model is not "refresh means
restart"; it is "publish a new version for future work while existing work
finishes under its captured facts and authority."

## What I would prototype or inspect

1. Add a publication ID to one agent runtime's tool catalog, approval context,
   and trace. Test view-only refresh, credential rotation, cancellation, and an
   in-flight approved call against the old publication.
2. Add a background-task protocol test that emits an intermediate result,
   invokes a policy hook and SDK tool, then emits an explicit run-complete
   frame. Alert when a tool executes without its expected hook callback.
3. Build a 20-task native-document regression set. Pair every requested edit
   assertion with at least one preservation assertion and reopen outputs using
   an independent parser.

## Audit

Screened **421 distinct candidates**: **141** raw strict-window records and
**109** genuinely timed strict records after removing blocked placeholders and
standing docs. Registered **46 local artifacts**; selected **3 stories / 6
source artifacts**. All selected sources received full-artifact subagent reads.
**Degraded selected sources: 0.** Paper gate: **PASS** (Xianpei Han, OpenAlex
4,573 citations).

Artifact directory:
`/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-07-23`
