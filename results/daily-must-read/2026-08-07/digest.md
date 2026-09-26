# Applied AI Engineering Daily Must-Read

**Friday, August 7, 2026**

Primary discovery window: 2026-08-06 16:12 UTC to 2026-08-07 16:12 UTC. Because fewer than three sources in that strict window cleared the final quality bar, this edition uses the labeled seven-day fallback for the paper. Routine Codex and Claude Code release-note coverage was excluded.

## Ranked Top 3

| Rank | Source | Topic | Window | Read |
|---:|---|---|---|---:|
| 1 | [Towards a Risk Assessment of Malicious Skill Files in Coding Agents](https://arxiv.org/abs/2608.05223) | Agent skill supply-chain security | 7-day fallback | 7 min |
| 2 | [OpenAI Agents: bind tool approvals to concrete invocations](https://github.com/openai/openai-agents-python/commit/4720150fde047baa4e88b16082b282bee3a5e87d) | Approval correctness across replay and resume | Strict 24h | 6 min |
| 3 | [Vercel AI SDK: ACP harness meta-adapter](https://github.com/vercel/ai/commit/ff0f708e917e3f556f889ed9158b396a17f3828c) | Multi-runtime agent harness infrastructure | Strict 24h | 5 min |

## 1. Malicious Skill Files Are an Executable Supply-Chain Boundary

**Primary:** [arXiv 2608.05223](https://arxiv.org/abs/2608.05223) · [replication repository](https://github.com/awsm-research/AgentJailbreak)

**Problem statement.** Coding-agent skills mix natural-language instructions with executable scripts, yet agents often ingest them as trusted operating guidance. The paper asks whether an attacker can hide real shell payloads behind benign skill descriptions and induce enterprise-grade coding agents to commit to or claim execution.

**Method.** The authors transform 471 Atomic Red Team shell commands into 2,826 adversarial skills using six generator models, covering 11 MITRE ATT&CK tactics. They run Gemini CLI and Qwen Code in isolated repositories on one controlled web-app scaffolding task, retain 5,629 completed runs, and classify transcripts with three local judges. Success is grounded declared intent or confirmation in the transcript, not successful payload effect. The evaluator requires quoted evidence, vetoes refusal-only evidence, applies a narrow declared-intent correction, and is checked against a blinded human disagreement sample.

**Key evidence, paper-reported.**

- Gemini CLI is labeled exploited in 95.5% of runs by raw majority vote and 96.1% after the declared-intent correction; Qwen Code is 71.6% and 74.0%, respectively.
- The human-derived estimates contain both operating points. On split cases, panel-versus-human agreement is reported as Cohen's kappa 0.83 for Gemini and 0.85 for Qwen.
- Explicit safety recognition appears in only 1.99% of runs. The risk is not limited to overtly destructive commands: pooled exploitability is highest for Initial Access (91.2%) and Defense Evasion (90.4%).
- Only one of 5,629 runs had intent-independent evidence that the payload actually executed; the authors attribute this to the 120-second harness and treat it as a strict lower bound. The headline rates must not be read as completed-command rates.

**Applicability.** Treat skills, repository instructions, hooks, and referenced scripts as executable dependencies, not prompt text. A production control should establish provenance, hash the complete skill package, statically inspect every referenced executable, constrain its capabilities, and require approval at the resulting tool invocation. The paper's proposed pre-ingestion scanner is a useful starting point, but it is not itself evaluated.

**Limitations and skepticism.** This is a strong stress test, not a universal exploitability constant. The skills are synthetic, use one "mandatory preflight" masking pattern, target only two CLI agents, run one task with a 120-second limit, and count grounded execution intent or log confirmation rather than live compromise. The human gold standard has one annotator, and inter-judge agreement on Qwen is poor (Fleiss' kappa -0.06). Those caveats weaken the exact percentages more than the underlying trust-boundary finding.

**Citation gate.** PASS. Exact coauthor Kla Tantithamthavorn is resolved through Monash University's profile and matching ORCID; the saved OpenAlex record reports 5,756 citations.

## 2. Approval Must Authorize an Invocation, Not a Reusable Call ID

**Primary:** [openai/openai-agents-python commit 4720150f](https://github.com/openai/openai-agents-python/commit/4720150fde047baa4e88b16082b282bee3a5e87d)

**User/operator mental model.** A user sees a pending shell, MCP, computer, function, custom-tool, or patch operation and approves that exact action. The decision must remain attached to the same semantic invocation through interruption, serialization, resume, and provider replay. A provider-supplied call ID is correlation metadata; by itself it is not an authorization principal.

**Why it matters.** If a changed payload can reuse an approved call ID, or if a completed call is replayed after restoration, the runtime can execute something the user did not approve or execute the same side effect twice. The affected artifacts are approval records, invocation lifecycle state, serialized run state, nested-agent checkpoints, and realtime pending-call maps.

**What changed, verified from the patch.** The SDK introduces a canonical invocation record keyed by a non-empty provider call ID but bound to invocation type, an authorization scope, and a SHA-256 semantic fingerprint. Fingerprints normalize relevant identity and payload fields, including arguments, actions, operations, environment, and caller. Reuse of a call ID with changed identity or payload raises a model-behavior error. Records track executed and completed state, are serialized with run state, and allow exact completed replays to be omitted rather than re-executed. Sticky approvals remain scoped, and old serialized states use an explicit legacy reconstruction path.

**Concrete engineering takeaways.**

- Define authorization as a tuple such as `(run lineage, tool identity, normalized payload, capability scope)`, with the provider ID only as an index.
- Persist lifecycle state before releasing an approval-bound call to execution; reject changed-payload reuse and suppress exact completed replay.
- Canonicalize structured arguments before hashing, and include every field that can change effect or authority.
- Add conformance tests for reused IDs across changed arguments, tool-name collisions, MCP approvals, nested runs, realtime sessions, interruption, serialization, and resume.

**Limitations and skepticism.** This is a 9,778-line cross-cutting patch, so the audit surface is substantial. The commit itself contains the tests, including a dedicated 2,902-line call-ID-reuse suite, but this digest did not run the SDK test suite. Correctness also depends on model providers honoring the documented requirement for stable, non-empty, per-invocation call IDs.

## 3. ACP as a Harness Meta-Adapter, With the Translation Tax Made Explicit

**Primary:** [vercel/ai commit ff0f708e](https://github.com/vercel/ai/commit/ff0f708e917e3f556f889ed9158b396a17f3828c)

**User/operator mental model.** An application uses one `HarnessAgent` API while selecting an ACP v1 runtime through a small profile. The user still gets streamed text and reasoning, native and host tools, approvals, skills, cancellation, and resumable sessions; the profile owns installation and authentication differences, while the generic adapter owns protocol and sandbox behavior. Session state includes ACP session identity, bridge coordinates, authentication and implementation identity, replay position, projected-skill state, and recovery metadata.

**Why it matters.** Dedicated adapters multiply lifecycle and security bugs across agent runtimes. This patch centralizes the hard state machine while keeping Claude Code, Codex, and Grok Build differences declarative.

**What changed, verified from the patch.** The new experimental `harness-acp` package supports simple exact-version NPM acquisition and frozen-lockfile acquisition, direct or AI Gateway authentication with runtime-resolved environment values, a sandbox bridge, ACP stream translation, native tools, host tools relayed through a harness-owned MCP server, explicit approvals, skill projection, session-mode mappings, and resume/load or replay recovery. Compatibility checks reject lifecycle state from the wrong harness, implementation, authentication profile, skill set, or sandbox. Permission requests require one-shot allow and reject options; unsupported session modes fail explicitly, while unmapped runtimes auto-approve only tool kinds allowed by the Harness permission mode and surface the rest to the caller.

**Concrete engineering takeaways.**

- Put protocol translation, event correlation, approval flow, and recovery in one adapter; keep package, command, auth, model, and permission-mode details in immutable profiles.
- Store compatibility fingerprints with resumable state and fail closed when runtime, credentials, skills, or sandbox identity changes.
- Keep host tools in a separately owned execution plane, even when they are advertised to the agent through MCP.
- Make unsupported semantic gaps explicit. ACP v1 lacks portable step boundaries, per-step usage, manual compaction, mid-turn steering, and built-in tool filtering.

**Limitations and skepticism.** The package is explicitly experimental and the patch is roughly 25,000 lines, much of it examples and tests. End-to-end verification is author-reported for three profiles, not reproduced here. Permission semantics are not uniform: the documented Codex ACP profile supports only `allow-all` because its restrictive modes would introduce a nested sandbox. A generic protocol reduces adapter count, but it does not eliminate runtime-specific behavioral testing.

## What I Would Read First

Read the malicious-skills paper's threat model, evaluator validation, recommendations, and threats-to-validity sections first. Then read the approval patch's new invocation-identity module: together they show the same design rule at two layers, namely that natural-language provenance and provider correlation IDs are not authorization boundaries.

## What I Would Prototype or Inspect

1. Add a skill-ingestion manifest to an agent runtime: source URL, immutable digest, referenced-file closure, requested capabilities, scanner verdict, and reviewer identity.
2. Property-test approval binding by mutating every effect-bearing field while reusing a call ID; every mutation should fail before execution.
3. Run one existing harness workload through the ACP adapter and compare lifecycle, approval, usage, replay, and host-tool traces against the native adapter before considering migration.

## Audit

499 distinct candidates screened; 55 local artifact records preserved; 12 selected-source artifact records; 3 selected sources; 0 degraded selected sources. Paper citation gate: PASS via one exact author with 5,756 citations. Source-specific full-read reports: 3. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-07`.
