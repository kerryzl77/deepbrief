# Daily Applied AI Engineering Must-Read

**Run:** 2026-08-30 09:16 PDT  
**Primary window:** 2026-08-29 09:16 PDT to 2026-08-30 09:16 PDT  
**Fallback:** Seven days, used for the paper because no paper appeared in the strict window

## Ranked Top Three

| Rank | Source | Focus | Window | Read |
|---:|---|---|---|---:|
| 1 | [Google ADK nested HITL resumption](https://github.com/google/adk-python/commit/6d145180611956b2065704189517fd6a0ff1a063) | Agent runtime / durable state | 24h | 6 min |
| 2 | [vLLM cache-salt scheduler DoS bound](https://github.com/vllm-project/vllm/commit/1dc464d42681d22f38caf1fdc1eb632dc4421c45) | Inference serving security | 24h | 4 min |
| 3 | [HarnessLens](https://arxiv.org/abs/2608.27311) | Harness evolution / eval allocation | 7-day fallback | 7 min |

## 1. Google ADK: Nested Human Approval Is a Durable State-Machine Problem

**Primary link:** [commit](https://github.com/google/adk-python/commit/6d145180611956b2065704189517fd6a0ff1a063)

**User/operator mental model.** An ADK workflow or agent tool may pause inside a child branch to request human input or credentials. A later process invocation resumes from persisted events rather than a live Python stack. The runtime must determine whether to keep waiting, replay the interrupted outer call so the nested node can consume the answer, or continue to the model.

**Why it matters.** The former two-event/direct-ID model could not reliably associate a user response on a child branch with the outer workflow call. This is the same class of lifecycle bug that appears when pause state, event identity, and branch lineage are treated as incidental logs instead of a durable execution protocol.

**What changed and mechanism.** The patch adds a tri-state `ResumeDecision`, scans relevant branch history for outstanding calls and responses, parses complete branch run IDs, recognizes ADK input/credential HITL responses on child branches, and replays the historical call event through the existing tool postprocessor with fresh output event IDs. A 323-line unit suite covers older pauses, direct and name-based answers, unrelated branches, nested HITL, long-running calls, and complete parallel answers; a previously skipped multi-HITL workflow test is enabled.

**Concrete takeaways.** Resume from semantic state rather than event proximity. Store branch lineage structurally. Distinguish “the human answered” from “the interrupted tool finished.” Make pause/replay/continue explicit and test process-restart composition.

**Limitations/skepticism.** Replay targets the entire historical function-call event. Partial interruption of parallel calls could revisit completed siblings; the patch does not test duplicate side effects or partial parallel completion. The nested matcher also recognizes only ADK’s built-in input and credential HITL names.

**Estimated read time:** 6 minutes.

## 2. vLLM: Bound Pre-Inference Control Metadata

**Primary link:** [commit](https://github.com/vllm-project/vllm/commit/1dc464d42681d22f38caf1fdc1eb632dc4421c45)

**User/operator mental model.** `cache_salt` is per-request namespace state used to isolate prefix-cache identities between tenants. It is accepted on Anthropic Messages, OpenAI chat/completions/responses, pooling, and scale-out generation surfaces.

**Why it matters.** The field was an unbounded attacker-controlled string. The commit identifies scheduler CPU exhaustion as the consequence, making this a cheap pre-inference resource-exhaustion path rather than a GPU-capacity issue.

**What changed and mechanism.** Seven declarative validation lines add a 1,024-character maximum across six request models, plus a non-empty lower bound for pooling. Oversized input is therefore rejected at protocol validation before normal scheduler/cache processing.

**Concrete takeaways.** Bound routing, cache, tenancy, and idempotency metadata as aggressively as prompts. Audit every compatibility endpoint for the same semantic field. Define whether limits apply to characters or encoded bytes, and retain body limits, rate limits, and scheduler admission controls.

**Limitations/skepticism.** The patch contains no regression tests, scheduler code, exploit benchmark, threshold justification, or byte-level limit. It verifies the boundary mitigation, but not the exact downstream amplification or whether internal constructors bypass these protocol models.

**Estimated read time:** 4 minutes.

## 3. Paper: HarnessLens

**Primary link:** [arXiv:2608.27311](https://arxiv.org/abs/2608.27311)

**Problem statement.** Harness optimizers often verify every proposed prompt, skill, or tool-description change against a fixed or random task batch. Unrelated rollouts dilute the intended effect and can make noisy aggregate gains look like evidence for the edit.

**Method.** HarnessLens derives proposals from trajectories, attaches each to a targeted behavior and editable component, and selects conversion, positive-control, preservation, and diagnostic tasks. Current and candidate harnesses run under matched conditions. An edit advances only when trajectory evidence attributes a recovery to it without an attributable regression, then passes a mostly fresh confirmation batch.

**Key evidence.** Across OpenCode, Codex, and Pi on four benchmarks, HarnessLens was best or tied-best in 8 of 12 pairs and never scored below the initial harness. Average held-out pass@1 improved by 13.6%, 7.6%, and 9.2%, respectively. On 19 OpenCode candidate iterations, a metric-only rule would accept 10 edits while the attribution gate accepted 5; six metric-positive edits lacked attributable recovery. Ablations show both behavior-aware task selection and attribution gating contribute.

**Applicability.** Engineering inference: persist an evidence envelope with each harness diff, including motivating trajectories, target behavior, conversion cases, and preservation cases. Use paired current/candidate runs and a separate confirmation gate. Treat “retain the existing harness” as a successful outcome when evidence is weak.

**Limitations/skepticism.** All target agents and evolution roles use one model family. Cost comparisons are not matched: HarnessLens treats trials and model sessions as equal units, while baseline maxima count rollouts. TEST uses one fresh trial per task, ablations cover only OpenCode, and model-mediated attribution is not calibrated against human audits.

**Citation gate.** Passed. Fudan corresponding author Deqing Yang maps to OpenAlex `A5068187260`, whose saved record reports 1,502 citations.

**Estimated read time:** 7 minutes.

## What I Would Read First

Read the ADK patch first if you own resumable agents or approval workflows. Read HarnessLens first if you are building automated prompt, tool-schema, or skill optimization.

## What I Would Prototype or Inspect

1. A persisted resume-state invariant suite covering nested approval, process restart, partial parallel completion, and duplicate-side-effect prevention.
2. Request-boundary fuzzing for every control-plane field that reaches shared schedulers or caches.
3. A harness-change evidence envelope with paired candidate/control rollouts, capability-specific preservation tests, and fresh confirmation before promotion.

## Audit

1,662 candidates screened; 195 strict-window candidates; 98 local artifact records; 4 selected artifacts for 3 selected sources; 0 degraded selected sources. Paper citation gate: **passed**. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-30/`.

