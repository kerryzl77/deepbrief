# Applied AI Engineering Must-Read Digest

**August 2, 2026**  
Primary window: 2026-08-01 16:01 UTC to 2026-08-02 16:01 UTC. Because only one source in that window cleared the bar, items marked **7-day fallback** come from July 26 onward.

## Ranked Top 3

| Rank | Source | Window | Why it earned a slot | Read |
|---:|---|---|---|---:|
| 1 | [Change2Task](https://arxiv.org/abs/2607.28591) | 7-day fallback | A concrete system for turning historical PRs into modern, executable coding-agent tasks with restoration and validation | 10 min |
| 2 | [OpenAI Agents: streamed tool-guardrail accounting](https://github.com/openai/openai-agents-python/commit/fc084ae29cd751b801c2779c9ebd23ff6bad1668) | Last 24 hours | A small runtime fix that exposes a larger invariant: streaming and non-streaming runs must produce equivalent audit state | 5 min |
| 3 | [CrewAI: trace actual skill use](https://github.com/crewAIInc/crewAI/commit/ebe0082acaafd2559152a37a0d201e167a5f280a) | 7-day fallback | Distinguishes “skill configured” from “skill executed,” which is the unit needed for agent trace attribution | 4 min |

## 1. Change2Task: Compile Repository History Into Modern Agent Tasks

**Primary link:** [arXiv 2607.28591](https://arxiv.org/abs/2607.28591)

**Problem statement.** Coding-agent data is not just an issue and a patch. A useful task needs a runnable repository state, dependencies, tools, an agent-facing specification, and a verifier. Historical benchmarks provide real developer intent but freeze old repository snapshots; fresh synthetic tasks reuse modern environments but may lose real maintenance intent. Change2Task asks whether a merged historical PR can be reconstructed as a verified task on a healthy modern descendant of the same repository.

**Method.** Think of the output as a task bundle with three states:

1. **Healthy modern base H:** target and regression checks pass.
2. **Task state C:** the historical maintenance obligation is reintroduced; target checks expose it while regressions still pass.
3. **Restored state H':** a restoration patch returns target and regression checks to passing.

The system derives intent, target checks, regression checks, and an edit profile from the source PR, freezes a runnable descendant commit, then escalates through three construction routes. Patch Reversal directly undoes a still-compatible change. Code Mapping replaces a uniquely matched modern code block with its historical pre-change form. Agent Reconstruction receives PR evidence, modern context, checks, scope, and failure feedback and gets at most four attempts. Every candidate must pass lifecycle, scope, fidelity, and semantic-alignment gates.

**Key evidence.** The authors report 900 finalized tasks from 1,130 construction-eligible changes across bug fixing, feature addition, test generation, API migration, and security repair. On 621 matched Bug Fix candidates, Change2Task recovered 500 tasks versus 387 for SWE-smith PR Mirror, a 29.2% relative gain. Across 3,600 matched historical/modern agent-task pairs, outcome agreement was 89.7% with no aggregate solve-rate difference. Reusing 388 modern bases for 900 tasks reduced measured setup time by 58.4%, retained storage by 71.2%, and matched end-to-end expenditure by 10.8%.

**Applicability to this reader.** The transferable design is not “ask an LLM to reverse a PR.” It is the surrounding compiler contract: freeze the base before construction; preserve source provenance; generate both task and restoration patches; require target pass/fail/pass and regression pass/pass/pass; constrain edits; and compare the modern realization against the source change profile. That is directly useful for continuously refreshed coding-agent evals and for producing verifier-backed training environments.

**Limitations and skepticism.** The 79.6% rate is over a filtered eligible set that already has traceable intent, executable checks, a surviving modern behavior host, and a runnable descendant. More importantly, 615 of 900 finalized tasks used model-based Agent Reconstruction; only 285 came from the two deterministic routes. The paper evaluates public Python and Java corpora and relies heavily on executable oracles and semantic judging. Treat the results as evidence for a disciplined construction pipeline, not a general recovery rate for arbitrary repository history.

**Citation gate:** passed through exact coauthor Dongmei Zhang. Her Microsoft identity was cross-checked and a public bibliometric profile reports 11,027 citations, above the 1,000-citation hard threshold.

## 2. OpenAI Agents: Streamed Runs Now Preserve Tool-Guardrail Results

**Primary link:** [commit fc084ae](https://github.com/openai/openai-agents-python/commit/fc084ae29cd751b801c2779c9ebd23ff6bad1668)

**User/operator mental model.** An Agents SDK tool can run an input guardrail before execution and an output guardrail afterward. In streaming mode, callers receive events while the agent runs and then inspect the final RunResultStreaming or persist it as RunState. Before this patch, the guardrails could run correctly during each turn, yet their result objects were not copied into the final streamed run record. An audit UI or orchestration layer could therefore see an empty or incomplete guardrail history even though enforcement happened.

**Why it matters.** This is a bookkeeping bug at a security and observability boundary. The user-visible tool behavior may look correct, while the post-run evidence differs depending on whether the caller used streaming. That breaks auditability, replay diagnostics, and parity between API modes.

**What changed and key mechanism.** The patch adds a helper that appends each turn's input- and output-guardrail result lists to the long-lived streaming result. The normal loop calls it after recording raw responses. The resumed-run path skips accumulation when the next step loops back to the model, preventing the same approved tool call from being counted twice.

**End-to-end evidence.** New tests cover ordinary completion, two tool turns, agent handoff, interruption for tool approval, RunState persistence, resumed completion, stop-on-first-tool behavior, and resumed handoff. Several cases compare streaming directly with non-streaming execution.

**Concrete engineering takeaways.**

- Treat the final streaming result as a behavioral API, not merely a token transport.
- Build parity tests over accumulated state across streaming and non-streaming modes.
- Test handoff, interruption, approval, resume, and serialization branches; happy-path token output will not reveal accounting gaps.
- Give continuation states explicit duplicate-accounting semantics.

**Limitations and skepticism.** The saved patch contains the test source but no independent test execution or CI result. It does not cover guardrail rejection/exception behavior, cancellation during a guardrail, or ordering across heterogeneous concurrent tools. Those remain useful follow-up tests.

## 3. CrewAI: Trace Skill Execution, Not Just Skill Availability

**Primary link:** [commit ebe0082](https://github.com/crewAIInc/crewAI/commit/ebe0082acaafd2559152a37a0d201e167a5f280a)

**User/operator mental model.** In CrewAI, a skill is a reusable capability loaded for an agent. Discovery, load, activation, and failure events describe setup. They answer “what could this agent use?” The runtime SkillUsedEvent answers “what did it actually execute, on which task, and how many times?”

**Why it matters.** Before this patch, SkillUsedEvent existed but the tracing listener was not subscribed to it. An agent could use one skill across twenty turns while the trace showed only the one-time activation event. That makes per-task attribution, usage counts, and skill-level quality or cost analysis unreliable.

**What changed and key mechanism.** A seven-line production change subscribes the trace listener to SkillUsedEvent and forwards the original event object under the skill_used action key. The event is forwarded once per use, preserving its payload for downstream serialization rather than reconstructing a reduced copy.

**End-to-end evidence.** Tests emit a usage event and verify collector reachability, assert object identity, verify three executions produce three trace events, and confirm existing activation tracing still works. The fixture scopes handlers because the event bus is process-wide, preventing test registrations from leaking.

**Concrete engineering takeaways.**

- Model capability inventory and runtime use as separate event types.
- Test trace cardinality and payload identity, not only event-name presence.
- Scope subscriptions on singleton event buses so tests and hot-reload lifecycles cannot leak handlers.
- Expect per-use events to increase trace volume; add sampling or aggregation only with explicit semantics.

**Limitations and skepticism.** The diff does not include SkillUsedEvent emission sites, downstream serialization/storage, concurrency behavior, backpressure, or volume measurements. It verifies the listener boundary, not the entire observability pipeline.

## What I Would Read First

Read Change2Task's construction and validation sections first. The reusable idea is the H -> C -> H' lifecycle plus provenance, scope, and fidelity checks; the model-based reconstruction is only one stage inside that contract.

## What I Would Prototype or Inspect

Add a cross-mode result-parity suite to an agent harness: run the same multi-turn tool scenario in streaming and non-streaming modes, including approval interruption and resume, then compare guardrail results, tool metadata, handoffs, traces, and serialized continuation state. Separately, inspect whether your tracing schema distinguishes capability activation from per-execution use.

## Audit

488 candidates screened; 48 in the strict 24-hour window; 53 raw artifacts downloaded (45 before shortlist fetches); 11 selected-source artifacts; 3 selected sources; 0 degraded selected sources. One paper surfaced and passed the author-citation gate through an exact author with 11,027 citations. Source-reader fanout completed 3/3 with no reader retries; two GitHub metadata fetches were retried as public commit pages after API rate limits.

Artifact directory: /Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-02
