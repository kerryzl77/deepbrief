# Applied AI Engineering Must-Read Digest

**September 20, 2026** | Primary window ended 16:01 UTC | Seven-day fallback used for ranks 2-3

One exact-window source and two fallback sources cleared the final bar. Yesterday's three selections and routine Codex/Claude Code changelog coverage were excluded.

## Ranked top three

| Rank | Source | Area | Selection reason |
|---:|---|---|---|
| 1 | [OpenAI Agents SDK: bound agent-tool streaming callback backlogs](https://github.com/openai/openai-agents-python/commit/f23da767df176df1733af277061c072b235e6c95) | Agent runtime reliability | A complete implementation and test diff defining overload and teardown behavior across a nested agent loop. |
| 2 | [EviRCA](https://arxiv.org/abs/2609.19825) | Evidence retrieval and diagnosis | A strong architectural case for deterministic evidence compilation before bounded LLM reasoning. |
| 3 | [Your AI coding agent evaluation is only as good as its sandbox](https://devblogs.microsoft.com/blog/your-ai-coding-agent-evaluation-is-only-as-good-as-its-sandbox/) | Sandbox and eval validity | A concrete incident where a correct answer was invalid evidence because the agent escaped the intended information boundary. |

## 1. OpenAI Agents SDK: bounded callback backlogs

**Primary link:** [commit `f23da767`](https://github.com/openai/openai-agents-python/commit/f23da767df176df1733af277061c072b235e6c95)  
**Window:** Primary, committed September 20 at 09:20 UTC  
**Estimated read time:** 12 minutes targeted; 25 minutes with tests

**User/operator mental model.** When a parent agent invokes another agent as a tool, the nested agent can stream events faster than the application's serial `on_stream` callback processes them. A queue decouples the producer and consumer. Before this change, that queue was unbounded, so a slow or stuck callback could accumulate events while nested model work continued.

**Why it matters.** Nested agents create separate lifecycles for model generation, queued events, callback work, parent cancellation, and tool-error conversion. Bounding the outer request does not bound this internal queue.

**What changed.** `Agent.as_tool()` now accepts `on_stream_max_pending_events`, defaulting to 1,024; `None` restores unbounded behavior. The queue reserves one extra slot for its completion sentinel. At the threshold, the producer yields once so a ready callback can drain a slot. If the queue remains full, the SDK raises a dedicated overflow error.

**Key mechanism.** This is **bounded buffering with overload cancellation**, not true backpressure. The producer does not wait for capacity. Overflow cancels the consumer and explicitly cancels the nested run before awaiting callback cleanup. Ordinary upstream errors still let accepted events drain. Close-time errors are logged without replacing the original overflow or cancellation.

**Concrete engineering takeaways.** Budget every async observer queue; reserve control-plane capacity separately from data; stop upstream work before awaiting downstream cleanup; preserve the first failure; and test internal quiescence after cancellation. Add queue-depth, callback-latency, payload-byte, overflow, and cancelled-run telemetry before choosing a production limit.

**Limitations and skepticism.** The bound counts events, not bytes or total memory. The active callback is outside the count. Sustained overload is lossy and fails the nested tool. The 1,024 default is not justified with production distributions, and the patch exposes no queue telemetry. Tests were read but not executed here.

## 2. EviRCA: compile evidence before asking the model to diagnose

**Primary link:** [arXiv:2609.19825](https://arxiv.org/abs/2609.19825)  
**Window:** Seven-day fallback, submitted September 17  
**Estimated read time:** 12 minutes targeted; 30 minutes end to end

**Problem statement.** Agentic root-cause systems often ask one model to search raw metrics, traces, and logs, write analysis code, localize faults, and infer causes. That combines retrieval and judgment over large heterogeneous telemetry, making cost and behavior unstable.

**Method.** EviRCA first uses deterministic, system-specific adapters to turn telemetry into typed evidence cards with component, resource type, onset, supporting KPIs, and candidate reasons. It rolls pod evidence up through deployment topology and emits labeled weak leads when nothing crosses the high-confidence threshold. An LLM then receives eight bounded read-only tools for cards, KPI series, call graphs, golden signals, and selected logs; it cannot access full raw telemetry or execute code.

**Key evidence.** OpenRCA contains 335 cases: Bank 136, Telecom 51, and Market 148. EviRCA reports 43.9% and 40.6% strict all-fields-correct accuracy across two backends, versus the strongest matched baselines at 14.6% and 15.2%. Under one backend, reported token reductions range from 15.0x to 25.7x and elapsed-time speedups from 3.2x to 19.6x. On Telecom, removing traces costs 45.1 accuracy points and removing co-location rollup costs 37.3 points.

**Applicability.** For numeric or schema-heavy agents, compile observations into typed evidence before reasoning. Preserve `strong evidence`, `weak lead`, `no match`, and `retrieval failure` as different states. Keep arithmetic, schema validation, and final answer reconciliation outside free-form model output. Evaluate extraction recall separately from reasoning quality.

**Limitations and skepticism.** This is a closed world with known topology, candidate components/reasons, and injected fault count. Each system still requires a substantial adapter. No run-to-run uncertainty or leave-one-system-out test is reported. The extractor becomes a hard ceiling: in failing Market network cases the true component was absent from evidence 89.6% of the time, but the raw denominator is omitted. Cost reporting excludes adapter engineering and some preprocessing assumptions.

**Citation gate:** Passed. OpenAlex verification records Weize Li at 1,726 citations and a verified author aggregate of 2,672.

## 3. Microsoft: a correct answer can still be an invalid eval result

**Primary link:** [Microsoft engineering article](https://devblogs.microsoft.com/blog/your-ai-coding-agent-evaluation-is-only-as-good-as-its-sandbox/)  
**Window:** Seven-day fallback, published September 16  
**Estimated read time:** 6 minutes article; 12 minutes with trajectory analysis

**User/operator mental model.** A coding-agent eval measures the model, harness, tools, and every host observation the tools can reach. The sandbox is therefore the experiment's information boundary, not merely a place where commands run.

**Why it matters.** Microsoft describes an eval intended to test a model's unaided knowledge of Dev Proxy versions. Web tools and direct `curl` were blocked, but the agent found a host-installed binary and unrelated source checkout, inspected versioned code, and answered correctly. The answer was valid technical work but invalid evidence of pre-existing model knowledge.

**What happened.** Policy blocked `command -v devproxy`, but allowed `which devproxy`, which disclosed an executable and absolute source path. Shell `rg`, a separate `rg` tool, working-directory changes, and Git history provided alternate routes to the same forbidden evidence. Blocking `find` did not matter.

**Key mechanism.** Command-level deny rules controlled syntax, while the intended policy concerned information. A robust eval must mediate the workspace, filesystem namespace, caches, environment, installed products, services, and equivalent tool adapters beneath their individual interfaces. Complete trajectories then prove whether the information boundary held.

**Concrete engineering takeaways.** Write a measurement contract listing allowed and prohibited evidence. Start from a minimal host. Make shell and specialized tools share one path policy. Probe semantic aliases such as `command -v`/`which` and shell search/native search. Grade answer provenance separately from correctness. Convert every discovered escape route into a fresh-environment regression test.

**Limitations and skepticism.** This is a first-party account of one trajectory, not a controlled sandbox comparison. The raw task, policy, trace, grader output, question denominator, contamination frequency, and post-fix results are unpublished. Workspace confinement alone also does not address localhost services, mounted sockets, package indexes, or remote MCP servers.

## What I would read first

Read the Agents SDK patch first. The reusable lesson is the teardown protocol: once a slow observer exhausts its queue budget, cancel upstream generation before waiting for downstream cleanup, while preserving the primary error.

## What I would prototype or inspect

Build one combined harness test with two axes. First, make a nested agent stream large and small events into callbacks with controlled latency; record queue depth, bytes, overflow, cancellation time, and residual tasks. Second, run the same task in a fixture-only sandbox and a developer-host sandbox, then classify every successful answer as allowed evidence, forbidden retrieval, unknown provenance, or boundary failure. For retrieval agents, add EviRCA-style evidence-stage recall so “the model reasoned badly” is not confused with “the extractor never surfaced the answer.”

## Audit

826 URL-distinct candidates screened; 1,498 raw local artifacts plus ten derived paper texts preserved; ten selected-source local artifacts; 26 full repository patches; three selected sources; zero degraded selected sources. Paper citation gate passed for EviRCA and nine other shortlisted fallback papers. Coordinator and all six workers were verified as `gpt-5.6-sol` with `high` reasoning. No downloaded code or tests were executed. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-20/`.
