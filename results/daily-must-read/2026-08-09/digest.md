# Applied AI Engineering Must-Read Digest - 2026-08-09

Primary window: 2026-08-08T16:15:38Z to 2026-08-09T16:15:38Z. The two engineering sources are strict-window commits. No strict-window paper passed both gates, so the paper slot uses the clearly labeled seven-day fallback.

## Ranked Top 3

| Rank | Source | Window | Best reason to read | Time |
|---:|---|---|---|---:|
| 1 | [Exact-path mount credential acknowledgements](https://github.com/openai/openai-agents-python/commit/192e6c7a3295bc553d469d54a20ae4422d1f5459) | 24h | A serious sandbox policy design for intentionally crossing credentials into model-controlled runtimes | 6 min |
| 2 | [Durable pending input in RunState](https://github.com/openai/openai-agents-python/commit/7bf73afa47ac48c1efb599d0b1505cee994e74f5) | 24h | A concrete persisted state machine for late user input, server acceptance, hooks, tools, and resume | 6 min |
| 3 | [PRWeaver](https://arxiv.org/abs/2608.02693) | 7-day fallback | Matched executable evidence that broad shared history can make long-horizon security review worse | 6 min |

## 1. Exact-Path Mount Credential Exposure Acknowledgements

**Primary link:** [commit `192e6c7a`](https://github.com/openai/openai-agents-python/commit/192e6c7a3295bc553d469d54a20ae4422d1f5459)

**User/operator mental model.** Mounting cloud storage into an agent sandbox has two different trust shapes. A provider can mount outside the sandbox, leaving credentials beyond the model-controlled process boundary. Alternatively, an in-container helper such as `rclone`, `s3fs`, `gcsfuse`, Blobfuse, or S3 Files receives or discovers authority inside that boundary. The latter is sometimes operationally necessary, but it should never happen because a broad boolean happened to be set.

**Why it matters.** The patch turns an intentional security-boundary crossing into a path-bound, runtime-only application decision. It distinguishes inline credentials scoped to one mount from broader authority such as ambient/workload identity or external credential files. Some helpers require both acknowledgements.

**What changed.** Trusted code can call `with_in_container_mount_credential_exposure_acknowledged(path)` or the broad-authority counterpart. The selected strategy, mount type, provider, credential fields, completeness, and exact destination still undergo centralized validation. Root paths, wildcards, parent segments, backslash forms, sibling paths, unsupported channels, partial credentials, and manifest-backed secret files remain rejected.

**Key mechanism and affected state.** The acknowledgement policy is a Pydantic private attribute. It is rejected from manifest input, omitted from `model_dump()`, and absent from serialized session state. Resume requires a current trusted manifest with exact credential-free topology; only then is runtime policy rebound. Validation runs before sandbox side effects and again at activation/restoration using the live resolved path. For Blaxel, credential bytes move through the file API into randomized `0600` files, are excluded from persistence/fingerprints before write, and are removed in `finally` rather than embedded in shell commands.

**Concrete engineering takeaways.** Dangerous opt-ins should bind to an exact resolved resource, not a provider-wide flag. Keep authority separate from persistable topology, require trusted rebind after resume, model narrow secrets separately from ambient authority, and trace both acknowledgement and activation decisions. Use mount-specific, short-lived credentials even when exposure is acknowledged.

**Limitations and skepticism.** Acknowledgement records exposure; it cannot prevent sandbox code from stealing authority afterward. The capability matrix is manually maintained, live FUSE/provider behavior is not tested, and abrupt termination could leave a credential file until sandbox teardown. The legacy Vercel boolean remains at the API surface, though it is translated into exact current paths internally. Upstream tests were inspected, not run locally.

**Estimated read time:** 6 minutes.

## 2. Durable Pending Input in RunState

**Primary link:** [commit `7bf73afa`](https://github.com/openai/openai-agents-python/commit/7bf73afa47ac48c1efb599d0b1505cee994e74f5)

**User/operator mental model.** An application can pause a nonterminal agent run, append new user input to serialized state, persist it, and resume later. The input should arrive immediately before the next model call, after any already-issued tool has finished, without being lost, duplicated, or delivered before its guardrails run.

**Why it matters.** Steering and human-in-the-loop systems need an explicit admission boundary. Treating late input as an ephemeral prompt append fails under model errors, server-managed conversations, stream cancellation, input filters, approval pauses, hook failures, and process restarts.

**What changed.** `RunState.add_input()` stores normalized, deep-copied pending occurrences. State now persists pending input, a durable next-model-call step, server-response acceptance, LLM-end-hook start, generated/session items, merge markers, tool outputs, and occurrence IDs. Terminal or potentially terminal states reject staging when a future model call is not guaranteed.

**Key mechanism and affected state.** Client-owned history converts pending input to durable `InputItem`s and persists them before dispatch. Server-managed conversations retain the original pending occurrence until a successful response proves that the delivered request was accepted. UUID-backed occurrence IDs distinguish identical messages across hydration and repeated resume. Input filters must preserve enough lineage to associate delivered items with pending occurrences; ambiguous rewrites fail closed. Accepted-response and tool/hook phase markers prevent the SDK from replaying work whose side-effect boundary is uncertain.

**Concrete engineering takeaways.** Build late input as a write-ahead state machine, not a queue beside the prompt. Use occurrence identity instead of content fingerprints, align commit points with the component that owns history, preserve source lineage through transforms, and persist phase markers around hooks and tools. Completed or ambiguous states should be explicitly non-resumable rather than guessed through.

**Limitations and skepticism.** SDK bookkeeping cannot make arbitrary external effects transactional. The patch does not test concurrent writers, a real process crash, cross-store atomicity, live server conversations, or durable database sessions. Applications still need single-writer resume discipline, atomic checkpoint persistence, and idempotent tools. The patch extends schema `1.15` without a version bump, which may complicate capability detection between builds. Upstream tests were inspected, not run locally.

**Estimated read time:** 6 minutes.

## 3. PRWeaver

**Primary link:** [arXiv 2608.02693](https://arxiv.org/abs/2608.02693)

**Problem statement.** Code-review benchmarks usually place a complete bug or vulnerability in one PR. Real malicious capability can emerge from several individually plausible changes mixed with maintainer work. PRWeaver tests whether review agents recover the composed security violation rather than merely flag suspicious local lines.

**Method.** The authors create 208 attacks over ten repositories and render each four ways: monolithic R0; decomposed R1; R2 with genuine benign PRs interleaved; and R3 with each malicious component fused into a coherent benign carrier and attacker-written description. Every prefix must build, host tests must pass, the exploit must activate only after the complete chain, and each build-valid leave-one-out variant must disable it. The 832 renderings are evaluated across six auditor/model systems spanning OpenCodeReview, Claude Code, and Copilot Code Review.

**Key evidence.** Decomposition alone does not hurt sequence detection: R1 is within 0-5 points of R0 and never lower. At 16 interleaved benign PRs, R2 falls 5-13 points below R1; carrier-fused R3 falls 10-18 points. The sharpest operational result uses Claude Haiku 4.5 across three harnesses at 24 benign PRs: native per-PR review detects 50-60%, while putting the whole release window into one active context collapses detection to 16-22%. Hiding history-inspection commands at R2/N=16 costs only 4-11 points, so passive access to more history is not the missing solution.

**Applicability.** Production reviewers should retain explicit security invariants, retrieve compact causal predecessors, and separate local diff inspection from composed-capability analysis. PR descriptions are untrusted evidence. Harness evaluation matters too: with the same Haiku model, R2/N=16 differs by ten points across frameworks.

**Limitations and skepticism.** Attacks and decompositions are model-generated, 195 of 208 attacks are Python, histories are reconstructed, and there is one run per evaluation cell. A model judges detection outcomes; the human-validation sample size and agreement are not reported. R3 combines carrier code and adversarial narrative, so it does not isolate which causes the degradation. The paper shows that unfiltered shared context is harmful, not that optimized cross-PR retrieval or invariant memory cannot help.

**Citation gate:** PASS. Exact coauthor Xiaofei Xie is resolved through his [SMU-affiliated homepage](https://xiaofeixie.bitbucket.io/), [DBLP ORCID record](https://dblp.org/pid/127/0713), and matching [OpenAlex author](https://openalex.org/A5084396416), which reports 6,741 citations.

**Estimated read time:** 6 minutes.

## What I Would Read First

Read the mount patch's `Manifest` policy and activation-time validation first. It is the most reusable implementation pattern today: authorization is exact-path, non-serializable, separated by authority class, and rechecked at time of use.

## What I Would Prototype or Inspect

1. Add a runtime-only capability ledger to a sandbox manifest: exact resource identity, narrow versus broad authority, acknowledgement principal, activation event, and resume rebind audit.
2. Model your agent's pause/resume path as explicit persisted phases. Inject failures after input admission, provider acceptance, hooks, tool start, side effect, and output persistence; verify what can safely replay.
3. Build a cross-PR review eval that retrieves only changes affecting the same security invariant or causal path. Compare it with per-PR review and broad release-window stuffing under a fixed model.

## Audit

500 candidates screened; 56 local artifact records; 3 selected sources with 12 selected-artifact records; 0 degraded selected sources; paper citation gate PASS (Xiaofei Xie, 6,741 OpenAlex citations). Seven-day fallback used for the paper because no strict-window paper cleared both gates. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-09/`.
