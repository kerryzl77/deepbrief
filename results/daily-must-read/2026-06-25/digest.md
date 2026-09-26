# Daily Applied AI Engineering Must-Read Digest - 2026-06-25

Reader: senior applied AI engineer building Codex/Claude Code-like agents, sandboxed tool runtimes, retrieval/document agents, evals, tracing, and production AI systems.

Window: primary last-24-hours run ending 2026-06-25 09:00 America/Los_Angeles. Three primary-window sources cleared the bar, so no 7-day fallback item is selected.

## Ranked Top 3

| Rank | Source | Topic | Why it clears the bar | Est. read |
|---:|---|---|---|---:|
| 1 | [E2B infra commit: harvest resume-prefetch trace on pause](https://github.com/e2b-dev/infra/commit/97bd4a55df42d54012732d699065b9e1b672e496) | Sandbox runtime / pause-resume infra | Production sandbox diff with a concrete latency mechanism, isolation model, flags, metrics, and tests. | 7 min |
| 2 | [OpenAI Codex commit: reconcile legacy WorldState sections](https://github.com/openai/codex/commit/ab80d4d484609719621826946cd9e137a3558862) | Agent context state / cold resume | Small but high-signal agent-state migration pattern for model-visible instructions and persisted world state. | 6 min |
| 3 | [MCP Python SDK commit: `InputRequiredResult` opt-in for `call_tool`](https://github.com/modelcontextprotocol/python-sdk/commit/03681ed55e35e1a11addc46fb5559974823c9cbd) | Tool protocol / HITL calls | Protocol-client API change for resumable, human-input-requiring tool calls while preserving default compatibility. | 4 min |

Total estimated reading time: about 17 minutes.

## 1. E2B Pause-Resume Prefetch Harvest

Primary link: [e2b-dev/infra commit `97bd4a55`](https://github.com/e2b-dev/infra/commit/97bd4a55df42d54012732d699065b9e1b672e496)

Background model: E2B is a cloud sandbox runtime for running agent code in isolated environments. Think of a sandbox as a short-lived remote dev/runtime machine: it has a filesystem, running processes, memory state, network policy, mounted volumes, and orchestration metadata. Pause/resume is the feature that lets E2B stop a sandbox and later bring it back instead of rebuilding everything from scratch.

What artifact is involved: this is not a Docker image optimization and not about compiled build artifacts. It is about a full memory pause snapshot: the sandbox's memory/page-cache state is saved into a snapshot artifact, uploaded, and later used to resume the sandbox. On a cold resume, if the memory file is no longer local, the resumed sandbox faults pages from remote storage such as GCS/NFS on the critical path. The optimization adds metadata telling the runtime which memory-backed pages to fetch early.

User/operator mental model: before this PR, plain Pause -> Resume could lose the prefetch metadata that checkpoint/resume already had, so a cold resumed sandbox might spend user-visible startup time demand-faulting its working set. After this PR, E2B can run a hidden throwaway resume immediately after pause, observe which pages the sandbox faults during startup, and save that page list so the next real resume can prefetch those pages. The user should just experience faster cold resume when the mapping is good; operators get default-off flags and metrics to observe harvest quality before making it customer-visible.

Scope of the feature: it applies to memory snapshots, not filesystem-only pauses. Filesystem-only pause snapshots intentionally drop memory and cold-boot from disk, so there is no memory prefetch mapping to harvest. The patch explicitly skips the harvest for filesystem-only pauses.

Why it matters: agent sandboxes live or die by resume latency and correctness. For Codex-like systems, a sandbox resume is often on the interactive path between a user asking for work and the agent regaining its execution environment. This diff shows a concrete runtime technique for using a controlled throwaway resume to generate prefetch metadata for the next real resume, without changing the existing prefetch consumer.

What changed in code: E2B added a pause-side harvest path for memory snapshots. After a pause snapshot is locally cached and upload starts, the orchestrator can resume a throwaway warm copy, collect its page-fault trace, convert that trace into a `MemoryPrefetchMapping`, and attach it to the pause metadata. The source claims cold resume average on a dev cluster moved from about 1535 ms to about 471 ms for significantly cold resumes.

Key mechanism: the throwaway is intentionally treated as a briefly thawed customer workload. It gets deny-all outbound egress, skipped live registration, suppressed normal startup metrics, volume mounts removed from the throwaway init payload, bounded start-slot use, and bounded teardown. Harvest and consume are split behind separate default-off flags, so operators can measure trace size and failure rate before writing mappings that affect customer resumes.

Concrete engineering takeaways:

- If a runtime already has demand-fault tracking and a resume prefetch consumer, a lifecycle replay can become a new producer without touching the consumer.
- Keep speculative replay isolated: no outbound network, no live registration, no user-visible health/KPI pollution.
- Split rollout controls into "harvest and observe" and "persist for customer-visible consume."
- Treat metadata upload ordering as a correctness boundary; do not update local or remote metadata while another upload path may still be reading or writing it.

Limitations / skepticism: the latency number is a commit-message claim, not a saved benchmark report with sample size or workload distribution. The source also says a real volume-mounted end-to-end run was unavailable on the dev cluster, so volume behavior is covered by config/unit tests plus non-volume e2e evidence.

## 2. OpenAI Codex WorldState Reconciliation

Primary link: [openai/codex commit `ab80d4d`](https://github.com/openai/codex/commit/ab80d4d484609719621826946cd9e137a3558862)

Why it matters: this is a production-pattern bug class for long-running coding agents. A retained transcript can still contain model-visible instructions even when the newer persisted state snapshot does not. Treating "no snapshot" as "nothing was visible" can duplicate stale context or fail to invalidate old instructions.

What changed: Codex adds `PreviousSectionState::{Absent, Unknown, Known}` for WorldState sections. `Unknown` means matching legacy context remains in retained model history, but no typed persisted snapshot exists. Sections can now identify their own legacy fragments, while `ContextManager` owns history reconciliation and baseline persistence.

Key mechanism: `render_history_diff` prefers a persisted snapshot when available, otherwise scans retained response messages for section-specific legacy fragments. AGENTS.md then emits one conservative replacement or removal message for unknown prior instructions, persists the new WorldState baseline, and deduplicates later turns.

Concrete engineering takeaways:

- In agent memory migrations, "unknown but probably model-visible" is a separate state from both "known previous snapshot" and "absent."
- Let each state section own recognition of its old serialization format; keep central code responsible for scanning history and persisting the new baseline.
- For instruction-like context, a one-time explicit replacement/removal notice is safer than silently allowing stale text to coexist.
- Cold-resume tests should simulate old rollout formats by removing the new persisted section while retaining old model-visible fragments.

Limitations / skepticism: the patch starts with AGENTS.md, so other WorldState sections still need meaningful legacy matchers. The scan is conservative but bounded to retained message/input-text representations shown in the diff. I did not run the Codex tests locally.

## 3. MCP Python SDK `InputRequiredResult` For `call_tool`

Primary link: [modelcontextprotocol/python-sdk commit `03681ed`](https://github.com/modelcontextprotocol/python-sdk/commit/03681ed55e35e1a11addc46fb5559974823c9cbd)

Why it matters: multi-round tool calls need a protocol shape that can pause for user input, credentials, disambiguation, or approval without forcing every tool to invent ad hoc argument conventions. This SDK change exposes that shape to Python clients.

What changed: for protocol `2026-07-28`, `tools/call` may return `InputRequiredResult`. The Python SDK keeps default `call_tool` behavior compatible: old callers still get `CallToolResult`, and an unexpected `InputRequiredResult` raises `RuntimeError`. Callers that pass `allow_input_required=True` can receive the union result and retry with `input_responses=` and opaque `request_state=`.

Key mechanism: the session layer parses `tools/call` through a union adapter for `CallToolResult | InputRequiredResult`, then guards the new result behind the opt-in flag. Higher-level `Client` and `ClientSessionGroup` add overloads and forward `input_responses`, `request_state`, and `allow_input_required` down to the session.

Concrete engineering takeaways:

- Model interactive tool clarification as an explicit result variant plus opaque continuation state.
- Keep compatibility by requiring an opt-in before widening a common API's return type.
- Round-trip `request_state` exactly; do not inspect or synthesize it in the host unless the protocol requires it.
- Agent hosts still need the policy/UX loop that maps input requests into validated `InputResponses`.

Limitations / skepticism: this is the client primitive, not a full agent loop. The commit tests opt-in return, retry-param threading, no-opt-in raising, and session-group forwarding, but it does not include a full two-turn server integration that returns `InputRequiredResult` and then a final `CallToolResult`.

## What I Would Read First

Read the E2B commit first. It has the highest implementation density and the most transferable runtime pattern: controlled lifecycle replay, isolation, feature-gated rollout, metrics, and failure-path tests.

## What I Would Prototype Or Inspect

Prototype a small "throwaway replay" harness for one of your sandboxed agent runtimes: take a paused workspace/process snapshot, replay startup under denied egress, collect demand-fault or file-open traces, and compare cold-start/resume time with and without prefetch. Separately, inspect whether your agent context store has an explicit `Unknown` state for legacy model-visible context during migrations.

## Audit

Candidates screened: 521. Raw local artifacts preserved: 87. Selected sources: 3. Selected artifact rows: 7. Degraded selected sources: 0. Source-specific subagent reports: 3. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-06-25`.
