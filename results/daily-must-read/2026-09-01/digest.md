# Applied AI Engineering Must-Read Digest

**1 September 2026**  
Strict discovery window: `2026-08-31 16:03 UTC` to `2026-09-01 16:03 UTC`. All three selections landed inside the strict 24-hour window, so the seven-day fallback was not needed.

## Ranked Top Three

| Rank | Source | Layer | Why it cleared the bar | Read |
| ---: | --- | --- | --- | ---: |
| 1 | [Vercel AI SDK: workflow-safe signed tool approvals](https://github.com/vercel/ai/commit/11109ae0fff79c3f8e2acca7af1145477c29cb53) | Durable agent authorization | Turns a replayed approval from trusted transcript data into a signed artifact bound to the exact tool invocation. | 6 min |
| 2 | [MCP TypeScript SDK: DPoP sender-constrained token support](https://github.com/modelcontextprotocol/typescript-sdk/commit/dcc01028ff6a499a5728c2b6181c1727d52e2fab) | Tool-protocol OAuth | Implements the client control loop that makes a stolen access token insufficient without the corresponding key. | 6 min |
| 3 | [What's in Your Agent's Context?](https://arxiv.org/abs/2609.01222) | Harness security paper | Gives context assembly an explicit role-and-scope privilege model and tests persistence after the malicious origin is removed. | 7 min |

## 1. Signed Tool Approvals For Durable Agents

**Primary link:** [Vercel AI SDK commit `11109ae`](https://github.com/vercel/ai/commit/11109ae0fff79c3f8e2acca7af1145477c29cb53)

**User/operator mental model.** A `WorkflowAgent` can pause before a sensitive tool call, show an approval UI, persist the conversation, and resume on another worker. The dangerous boundary is the resumed client history: without authentication, an altered approval response can look indistinguishable from the one the user actually approved.

**Why it matters.** The change treats approval as an authorization artifact, not a boolean embedded in a transcript. That is the right model for any durable coding or operations agent whose state crosses a browser, database, queue, or worker restart.

**What changed.** The agent can take an environment-variable reference for an approval secret at construction or per stream. It signs the approval ID, tool-call ID, tool name, and validated input when issuing the request; carries the signature through durable stream and UI conversions; and verifies it before shared approval validation and tool execution. Tests cover missing or modified signatures, changed IDs, tool names, and schema-valid input changes, plus issue/resume across separate workflow runs.

**Key mechanism.** Secret resolution occurs inside durable signing and verification steps, so serialized workflow state contains the reference and signed request, not the raw key. This cleanly separates persisted authorization state from worker-local secret state.

**Concrete engineering takeaways.** Sign a canonical authorization record at issuance and verify at the last point before the effect. Test the exact production serializer across pause, UI storage, reconnect, and resume. For higher-value actions, extend the record with principal, tenant, workflow/run, policy version, audience, expiry, key ID, and atomic one-time consumption.

**Limitations/skepticism.** The diff imports the shared signing helper rather than exposing its canonicalization, algorithm, encoding, or comparison implementation. The visible record has no expiry, identity/audience binding, key ID, multi-key rotation, or explicit one-time-use state. Enabling signatures also invalidates pending unsigned approvals, so rollout and rotation need an operational plan.

**Estimated read time:** 6 minutes.

## 2. DPoP At The MCP Transport Boundary

**Primary link:** [MCP TypeScript SDK commit `dcc0102`](https://github.com/modelcontextprotocol/typescript-sdk/commit/dcc01028ff6a499a5728c2b6181c1727d52e2fab)

**User/operator mental model.** An MCP host uses OAuth to call remote tool servers. A normal bearer token is usable by whoever steals it. DPoP binds token use to a client-held signing key and to the concrete HTTP method and URL, reducing the value of a leaked token.

**Why it matters.** Agent hosts increasingly retain broad, long-lived tool credentials while running untrusted content and custom transports. Sender-constrained tokens move credential defense from convention into the protocol path that actually sends the request.

**What changed.** The SDK adds opt-in persistent `DpopSession` state, ES256 WebCrypto keys, RFC 9449 proofs, access-token hashes for resource calls, per-origin nonces, and bounded nonce retries. It upgrades requests to the `DPoP` authorization scheme only when the issued token says `token_type: DPoP`, preserving Bearer compatibility otherwise. Streamable HTTP, SSE, announced POST endpoints, and caller-provided fetch implementations are covered.

**Key mechanism.** Proof generation is installed at the final fetch layer, below OAuth and reauthorization wrappers. That placement lets each proof bind to the wire-level request after transport selection and lets nonce challenges be handled without reconstructing the agent's higher-level operation.

**Concrete engineering takeaways.** Make the authorization provider own durable key/session state and the transport own per-request proof construction. Store the key at the same lifecycle boundary as the client identity, redact proof JWTs from traces, and instrument key thumbprint, normalized target, nonce retries, token type, and reauthorization count.

**Limitations/skepticism.** The host still owns secure persistent key storage and multi-process coordination. The patch parses advertised algorithms but does not visibly select or reject against them, and tests do not establish redirect safety, server-side replay enforcement, proxy behavior, or completed conformance runs against real servers.

**Estimated read time:** 6 minutes.

## 3. Context Privilege Escalation Across Agent Harnesses

**Primary link:** [arXiv `2609.01222`](https://arxiv.org/abs/2609.01222)

**Problem statement.** Agent harnesses assemble prompts from repositories, environment metadata, memories, skills, configuration, and tool outputs. Existing prompt-injection framing does not capture when harness logic promotes low-trust content into a higher message role or persists it into a wider scope.

**Method.** The paper defines MessageRole CPE and Cross-Scope CPE, then introduces CORA: an LLM-assisted static and dynamic pipeline that discovers context sources, instruments model-endpoint requests with canaries, infers role and scope, enumerates source-pair privilege transitions, and performs a second launch after removing the original low-trust source.

**Key evidence.** Across 12 version-pinned harnesses, CORA found 463 candidate sources and runtime-verified 282. It enumerated 1,761 candidate CPE paths; GPT-5.4-mini behaviorally verified 1,028 and GPT-5.5 verified 1,034, both reported as 58%. Manual inventories for Codex and Gemini CLI yielded reported source-discovery precision/recall of 100%/93% and 97%/91%. The paper also presents five end-to-end scenarios and reports disclosure to all twelve maintainers.

**Applicability.** Give every context source explicit provenance, role, scope, loader, and write authority. Add a context manifest to traces. For regression tests, seed a canary in an untrusted source, remove that source, relaunch in another workspace, and assert that it cannot reappear in a higher role or wider memory scope. Apply this to repository metadata, retrieved documents, skill registries, memory tools, compaction, and subagent handoffs.

**Limitations/skepticism.** Vulnerability claims apply to the exact versions in the paper's census, not current products; the authors report some mitigations but do not map fixed versions to public diffs. Precision/recall was manually grounded for only two harnesses. CORA uses an LLM for code reasoning and environment recipes, behavioral verification varies by model and task, and the promised source release was not available in the inspected artifact set.

**Citation gate.** Passed. OpenAlex identities matching paper authors and 2026 UIUC affiliation list Xiaojing Liao at 1,341 citations and Luyi Xing at 1,136; either independently clears the 1,000-citation requirement. See [Liao](https://openalex.org/A5084889167) and [Xing](https://openalex.org/A5036446600).

**Estimated read time:** 7 minutes.

## What I Would Read First

Read the Vercel approval patch first. It is the most immediately reusable end-to-end design: authorization record, durable state, secret boundary, UI transport, resume path, and tamper tests all meet in one change.

## What I Would Prototype Or Inspect

Prototype a small authorization envelope shared by tool approvals and MCP calls: canonical payload, principal/audience, run and policy IDs, expiry, key ID, single-use state, and trace-safe fingerprints. Then add a two-run context-promotion eval inspired by CORA to verify that untrusted repository or document content cannot persist into global memory after its origin disappears.

## Audit

- Candidates screened: **1,686** distinct records (**576** strict-window)
- Raw/local artifacts preserved before synthesis: **94**
- Selected sources: **3**; selected artifacts: **4**
- Degraded selected sources: **0**
- Paper citation gate: **passed** for the selected strict-window paper
- Discovery/full-read subagents: **6 / 4**, no retries required
- Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-01`

Material claims are mapped to local evidence and public primary links in `verification/evidence-matrix.md`. Engineering recommendations are marked as implications rather than source claims.
