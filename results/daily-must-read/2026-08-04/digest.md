# Applied AI Engineering Must-Read Digest

**August 4, 2026**  
Primary window: 2026-08-03 16:04 UTC to 2026-08-04 16:04 UTC. The two code items are from this window. AgenticRepair is a clearly labeled **7-day fallback** from July 31.

## Ranked Top 3

| Rank | Source | Window | Why it earned a slot | Read |
|---:|---|---|---|---:|
| 1 | [Vercel AI SDK: signed code-mode continuations](https://github.com/vercel/ai/commit/8b7f805068adc295b0966a4d515cc124c6f4c09a) | Last 24 hours | A concrete pause/approval/resume protocol for nested agent tools, with deterministic replay and an important anti-replay gap | 7 min |
| 2 | [Codex: negotiate MCP extensions per session](https://github.com/openai/codex/commit/ee46c5ba0e5341ba3d0777bd3f195f365cfdf89b) | Last 24 hours | Shows how host UI capabilities must flow into session ownership, downstream handshakes, connection reuse, caches, and subagents | 6 min |
| 3 | [AgenticRepair](https://arxiv.org/abs/2607.29422) | 7-day fallback | Tests whether compiling structural, runtime, and historical evidence before editing improves vulnerability repair | 6 min |

## 1. Vercel Code Mode: Resume by Signed Replay, Not Process Suspension

**Primary link:** [commit 8b7f8050](https://github.com/vercel/ai/commit/8b7f805068adc295b0966a4d515cc124c6f4c09a)

**User/operator mental model.** Vercel's experimental code mode runs JavaScript inside a QuickJS worker. The JavaScript can call several host tools through a bridge. Consider a script that first searches a database, then tries to send an email. Search may execute immediately, while send-email requires human approval.

With interrupt mode enabled, code mode stops before the sensitive tool and returns a structured interrupt plus a signed continuation. The host persists that object, shows an approval UI, and later submits the decision. Resume does **not** thaw the old worker, restore a VM, or serialize the JavaScript heap. It creates a fresh QuickJS run from the beginning. An ordered ledger returns the recorded search result without executing search again; execution then reaches the pending email call and performs or denies it. A later approval creates another continuation and repeats the cycle.

**Why it matters.** Long-lived agent approvals often cross process restarts, queues, replicas, and user delays. Saving a suspended runtime is expensive and brittle. A signed replay recipe is compact and portable, while still avoiding repeated execution of completed nested tools when control flow is deterministic.

**What changed.** The patch adds callback and interrupt approval modes, generic host interruptions, approval-message adapters, public continuation helpers, a deterministic guest clock and random generator, an ordered tool-result ledger, worker drain handshakes for concurrent calls, and experimental resume APIs.

**Key mechanism.** The continuation contains transformed source, outer invocation identity, initial time/random state, every completed/rejected/interrupted tool entry, issuance and expiry times, a random nonce, and an HMAC-SHA256 signature. Resume verifies the signature and public envelope, checks source equality, then matches each replayed bridge call by position, tool name, and exact input JSON. Fulfilled and rejected entries replay their recorded outcome; only the matched pending entry consumes the new resolution.

**Concrete engineering takeaways.** Treat this design as event-sourced restart. Persist continuations as sensitive records because tool inputs and outputs are plaintext. Use a stable server-only key across legitimate replicas; the random in-process default will not survive restart. Authenticate the approver outside the continuation protocol, bind tool versions across the approval window, and make side effects idempotent.

Most importantly, add an atomic consumed-capability record keyed by nonce and interrupt ID. The signature proves integrity and expiry, but this patch has no consumed-nonce store. Submitting the same still-valid pending continuation twice can execute the approved side effect twice.

**Limitations and skepticism.** The APIs are experimental. The commit says AI Core approval wiring is future work, documentation is incomplete, and end-to-end verification is marked `na`. The patch has unit/package tests for replay, denial, concurrent approvals, envelope mismatch, and generic interrupts, but no duplicate-submission, cross-replica, restart, expiry, rotation, or full approval-product tests. I inspected the patch but did not run the suite.

## 2. Codex: MCP Capabilities Become Loaded-Session Identity

**Primary link:** [commit ee46c5ba](https://github.com/openai/codex/commit/ee46c5ba0e5341ba3d0777bd3f195f365cfdf89b)

**User/operator mental model.** A desktop or IDE client connects to Codex app-server. Codex then opens separate downstream connections to MCP servers that provide tools and resources. Some host clients can render MCP App UI resources, while others cannot. A downstream server needs to know the actual host's supported extension and MIME profile before choosing what representation to return.

The host now declares an extensions map during app-server initialization. When it starts, resumes, or forks a thread, Codex snapshots that profile into the loaded session. Codex advertises it in each downstream MCP initialize handshake. Direct tool calls, model-selected calls, and internal subagents use the same profile; later turns cannot silently change it. This patch negotiates UI support but does not implement the renderer itself.

**Why it matters.** MCP capabilities are not decorative request metadata. They affect what a server may return and how a privileged host surface may render it. Reusing a server connection or cached tool catalog negotiated under a different host profile creates capability confusion.

**What changed.** The app-server protocol gains a structured extensions map. Codex allowlists `openai/form` and `io.modelcontextprotocol/ui`, preserves the old form-support boolean as a legacy alias, propagates the normalized profile through start/resume/fork and internal child creation, and removes per-turn mutation of the old flag.

**Key mechanism.** The complete extension profile is part of downstream MCP connection identity and the stdio tool-catalog cache key. A connection initialized for a UI-capable host therefore cannot be transparently reused for a non-UI session solely because its server URL, auth, and configuration match. Known extension settings preserve future object fields, including supported UI MIME types.

**Concrete engineering takeaways.** Snapshot negotiated capabilities at the lifecycle boundary where the dependent connections are created. Include them in every cache and pooling identity whose contents can vary by capability. Propagate them explicitly into child agents. Preserve unknown fields inside known extension namespaces for forward evolution, but allowlist namespaces rather than forwarding arbitrary client claims.

**Limitations and skepticism.** Extension negotiation is not content authorization, HTML trust, or renderer sandboxing. The loaded-session profile is not shown being serialized into durable thread history; a future resume may legitimately negotiate a new profile. Known extensions with non-object settings affect identity but are omitted from downstream initialization, suggesting normalization should reject malformed shapes earlier. The patch lacks a direct two-client isolation test and complete end-to-end resume/fork/subagent handshake coverage. I did not build Codex.

## 3. AgenticRepair: Compile Security Evidence Before Editing

**Primary link:** [arXiv 2607.29422](https://arxiv.org/abs/2607.29422)

**Problem statement.** Vulnerability repair starts with richer evidence than ordinary issue fixing: a security description, sanitizer crash, cross-file memory flows, runtime ownership transitions, and repository history. A general repair loop may spend its budget rediscovering these signals or start editing before they are assembled into a coherent diagnosis.

**Method.** AgenticRepair begins after triage with a vulnerable C/C++ repository, human description, sanitizer trace, prepared Docker environment, and supplied proof-of-concept harness. Three read-only agents run in parallel: a structure agent uses repository and CodeQL-style analysis; a runtime agent uses the harness, debuggers, Valgrind, and sanitizers; and a history agent mines preceding commits. Their compressed findings are inserted into per-task episodic memory. A fourth agent gets up to 75 steps to edit, build, run the PoC, observe sanitizer output, and revise.

The useful mental model is evidence compilation into a per-task context artifact, not cross-task learning. The paper does not specify a durable retrieval database, typed context schema, contradiction resolution, or exact synthesis procedure.

**Key evidence.** On all 300 SEC-Bench instances, the paper reports 220 strict successes with GPT-5.2 versus 134 for the same-model Smolagents baseline: 73.3% versus 44.7%, a 28.6 percentage-point difference. Ninety successful patches modify multiple files. However, removing any one context facet changes strict success by only 0.5-2.0 points. The 44.5-point drop for the single-agent scaffold is not shown to be compute-matched against three additional 20-step analysis agents.

The most actionable result may be the failure taxonomy: 53 of 80 strict failures are malformed or truncated patches rejected by `git apply`. Before adding another analysis agent, use structured file edits or a validated patch transaction.

**Applicability.** Build explicit evidence collectors before high-risk edits and hand off typed claims with source anchors, confidence, support/contradiction links, and recommended actions. Keep stable diagnosis separate from volatile build/test observations. Treat history as untrusted intent evidence. Follow the supplied PoC with regression tests, exploit variants, fuzzing, and functional invariants.

**Limitations and skepticism.** The baseline budgets, tokens, wall time, tool parity, and dollars are not reported comparably. There are no repeated runs or significance intervals. Success primarily means one supplied PoC exits under the sanitizer criteria; it is not general proof that the vulnerability is eliminated or behavior preserved. Patch-similarity checks do not rule out CVE/root-cause leakage, and the history environment is not documented as scrubbed of later fix references. The claimed replication package was not linked on the saved arXiv page and was not reproduced here.

**Citation gate.** Passed through exact coauthor [Kla Tantithamthavorn](https://research.monash.edu/en/persons/kla-tantithamthavorn/), who publishes as Chakkrit Tantithamthavorn. The identity was resolved using his official Monash profile and matching ORCID; [OpenAlex A5081449581](https://openalex.org/A5081449581) reports 5,756 citations.

## What I Would Read First

Read the Vercel patch report first. The transferable concept is signed deterministic replay, but the production lesson is the gap between integrity and exactly-once execution: an expiring HMAC capability still needs atomic consumption or idempotent effects.

## What I Would Prototype or Inspect

Prototype a continuation store with encrypted payloads, shared-key rotation, authenticated approval records, and atomic `(nonce, interruptId)` consumption; then submit the same approval concurrently to prove only one side effect occurs. For MCP, inspect every connection pool and tool-catalog cache to ensure negotiated capabilities participate in identity. For repair agents, compare equal-budget staged evidence compilation against one monolithic agent and use structured edits before evaluating another context facet.

## Audit

387 distinct candidates screened; 144 in the strict 24-hour window; 43 local artifacts preserved (28 before shortlist fetches); 11 selected-source artifacts; 3 selected sources; 0 degraded selected sources. One 7-day-fallback paper surfaced and passed the author-citation gate through an exact coauthor with 5,756 citations. Source-reader fanout completed 3/3 with no retries. ArXiv API discovery was blocked, so paper discovery was supplemented from locally preserved seven-day artifacts and public web search; the selected paper itself has complete saved HTML, PDF, and extracted text.

Artifact directory: /Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-04
