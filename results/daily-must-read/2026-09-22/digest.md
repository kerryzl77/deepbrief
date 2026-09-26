# Daily Applied AI Engineering Must-Read

**September 22, 2026**  
**Primary window:** September 21, 16:01 UTC to September 22, 16:01 UTC  
**Audience:** engineers building agent harnesses, sandboxes, tool runtimes, evals, and production AI systems

All three selections fall inside the primary 24-hour window. No fallback item was needed. The common theme is that agent reliability increasingly depends on typed boundaries around adaptive optimization, untrusted execution, and untrusted tool metadata.

## Ranked top three

| Rank | Source | Area | Why it made the cut | Read |
|---:|---|---|---|---:|
| 1 | [Benchling: multi-tenant agent-code isolation](https://aws.amazon.com/blogs/machine-learning/how-benchling-secured-multi-tenant-ai-agents-with-amazon-bedrock-agentcore/) | Sandboxing | A concrete production composition of account, network, identity, tenant, and continuous-test controls | 7 min |
| 2 | [RRSI: Regularized Recursive Self-Improvement of Agent Harnesses](https://arxiv.org/abs/2609.24972) | Harness evolution / evals | Treats automated harness optimization as adaptive benchmark reuse and adds explicit transfer and cost gates | 8 min |
| 3 | [Google ADK: fence MCP descriptions before model exposure](https://github.com/google/adk-python/commit/a519b6f6235146d5bc18f19582f8d4360b9adb64) | MCP / tool security | A code-backed pattern for separating raw tool metadata from the model-facing representation | 5 min |

## 1. Benchling composes sandbox controls around generated code

**Primary source:** [AWS Machine Learning Blog](https://aws.amazon.com/blogs/machine-learning/how-benchling-secured-multi-tenant-ai-agents-with-amazon-bedrock-agentcore/)

**User/operator mental model.** A researcher triggers an AI workflow that generates scientific code. Trusted production code determines the tenant and job scope, then sends execution to a short-lived Code Interpreter session in a separate untrusted AWS account. The session receives temporary credentials for one tenant path and can reach approved S3 destinations, but has no general internet route.

**Why it matters.** The useful pattern is not a single sandbox product. It is the composition of different failure boundaries: separate account, ephemeral execution, no IGW/NAT, default-deny DNS, constrained VPC endpoints, per-job STS credentials, tenant-prefix session policy, and adversarial CI checks.

**What changed / reported deployment.** Benchling says the system has run since April at more than 600 sessions per day across more than 250 tenants per week, with no reported security incidents or cross-tenant leakage. Those are vendor/customer self-reports, not independently audited measurements.

**Key mechanism.** DNS rules run as explicit deny at priority 10, narrow allow at 100, and catch-all `NODATA` at 200. S3 gateway/interface endpoints restrict reachable buckets. IAM and a launch-time session policy restrict the authorized tenant prefix. CI simulates DNS tunneling, direct unauthorized connections, and out-of-scope S3 access; a successful exfiltration attempt blocks release.

**Concrete engineering takeaways.** Bind tenant identity in trusted control-plane code before minting credentials. Test the intersection of route, endpoint, role, session, bucket, and prefix policies. Add tenant-confusion cases, positive controls, credential expiry/revocation tests, cross-session residue tests, and output-channel tests. Treat allowed S3 writes as an exfiltration/persistence surface, not merely a result channel.

**Limitations / skepticism.** The post publishes no IAM policies, infrastructure code, test implementation, independent penetration test, latency/cost data, or detection methodology. It does not explain result return, credential injection, erasure guarantees, peak concurrency, or same-bucket cross-tenant isolation. Claims such as "every exfiltration vector" exceed the disclosed evidence.

**Evidence labels.** Verified source facts are the disclosed architecture and tests. The tenant-confusion and allowed-output-channel risks are engineering inferences. Complete exfiltration prevention is unverified.

## 2. RRSI regularizes automated harness optimization

**Primary source:** [arXiv 2609.24972](https://arxiv.org/abs/2609.24972)

**Problem statement.** Repeatedly editing a harness against one finite benchmark is adaptive test-set reuse. Score-only search can memorize benchmark details, promote noisy winners, and retain expensive complexity that does not transfer.

**Method.** RRSI keeps model weights frozen and regularizes both proposal and selection. Proposal controls include an annealed edit-count budget, an edit ledger with rejected evidence, exploration when progress stalls, and pruning of components with no measured gain. Selection uses an LLM leakage critic, a calibrated score-noise floor, token-cost constraints, structural novelty, and a design-validity guard. Candidates must pass non-compensatory checks before promotion.

**Key evidence.** On the Harvey LAB workspace setting, unregularized evolution scored 92.8 on the evolve set but 40.3 average OOD at 3.80M policy tokens per trial. RRSI accepted a smaller evolve score of 90.5, reached 43.6 OOD, and used 2.42M tokens. The initial harness used 1.56M tokens, so RRSI is cheaper than unregularized evolution but still materially more expensive than no evolution. Across coding, workspace, and design, the paper reports gains on five OOD benchmarks plus one ID-held-out split; cross-policy checks are positive but limited.

**Applicability.** The reusable contribution is an acceptance policy for harness changes: maintain evolve, untouched ID, and genuinely OOD surfaces; record exact edits and attribution; calibrate measurement noise; and gate safety, validity, cost, and leakage separately instead of collapsing them into one score.

**Limitations / skepticism.** This is finite benchmark-driven harness search, not model-weight or open-ended self-improvement. The paper does not report total evolution tokens, wall time, dollar cost, candidate count per round, confidence intervals, or multiple independent evolution seeds. Its ablations remove groups of regularizers, not each one. Three within-band selection weights are claimed to be in Table 5 but are absent.

**Citation gate.** Passed. OpenAlex identifies coauthor Tomas Pfister with Google affiliation and 10,289 citations, above the required 1,000 threshold. See author-citation-audit.md (local research intermediate discarded).

## 3. Google ADK treats MCP descriptions as untrusted model input

**Primary source:** [Google ADK commit `a519b6f`](https://github.com/google/adk-python/commit/a519b6f6235146d5bc18f19582f8d4360b9adb64)

**User/operator mental model.** An MCP server supplies tool names, descriptions, and nested schemas. Applications need the exact declaration for inspection, but passing that same text to a model lets a remote server place instruction-shaped content beside first-party instructions. ADK now maintains a raw declaration and builds a separately fenced model-facing declaration.

**Why it matters.** Tool metadata is prompt input and needs an explicit provenance class. The patch demonstrates where to apply the transformation: at model serialization, while preserving immutable raw evidence for UIs and audits.

**What changed.** Top-level and recursively nested schema descriptions are wrapped as untrusted data. Reserved fence markers are elided, value positions such as `enum` and `default` are not wrapped, and one system preamble explains the boundary. The patch covers seven files, 1,025 additions, and extensive unit/integration fixtures.

**Key mechanism.** ADK recursively copies schemas, fences `description` fields, handles map-valued schema keywords, preserves semantic values, then replaces the declaration already added to the LLM request. Reverse lookup handles duplicate tool names. Raw declarations remain unchanged for non-model consumers.

**Concrete engineering takeaways.** Split raw and model-facing metadata; recurse across all schema paths; add behavioral injection evals beyond structural tests; instrument every fail-open branch; and pair prompt containment with tool allowlists, argument policy, approvals, scoped credentials, and execution isolation.

**Limitations / skepticism.** This is prompt containment, not a security boundary, and the commit provides no measured attack-success reduction. Scope is MCP only. Unsupported non-string system instructions fail open with a log, arbitrary titles remain unfenced, Unicode lookalikes are not normalized, and exact marker elision can mutate rare legitimate schema values. The stated one-time Gemini context-cache miss is not benchmarked.

## What I would read first

Read the Benchling architecture first, specifically the tenant-scope credential flow and the CI exfiltration tests. Then read RRSI's acceptance rules and ablation table; they map directly to any automated prompt, tool, or harness optimizer.

## What I would prototype or inspect

1. Build a sandbox policy matrix that deliberately mismatches authenticated tenant, job metadata, STS session policy, S3 prefix, and returned output identity.
2. Add an edit ledger and non-compensatory acceptance gates to one harness-optimization loop; report evolve, ID, OOD, final-runtime cost, and total search cost separately.
3. Audit every externally supplied tool-description path in your runtime and preserve two forms: exact raw metadata for operators and typed, provenance-labeled metadata for the model.

## Audit

**190 curated candidates; 170 preserved artifacts; 3 selected sources backed by 10 selected artifacts; 0 degraded selected sources; paper citation gate: PASS; model gate: PASS (`gpt-5.6-sol`, high, coordinator and all six workers).** Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-22`.

Supporting records: candidate ledger (local research intermediate discarded), artifact manifest (local research intermediate discarded), fanout report (local research intermediate discarded), evidence matrix (local research intermediate discarded), runtime audit (local research intermediate discarded), and selected-source record (local research intermediate discarded).
