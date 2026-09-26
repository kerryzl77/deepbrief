# Daily Applied AI Engineering Must-Read

**September 26, 2026**  
**Primary window:** September 25, 16:02 UTC to September 26, 16:02 UTC  
**Seven-day fallback screened:** September 19-26; used for the paper only  
**Targeted source reading:** 18 minutes

Two new code changes address different agent trust boundaries: who may resolve an MCP credential after an executor reconnect, and what an agent-accessible file operation may open or truncate. The paper selection is a labeled seven-day fallback. It supplies a document-agent evaluation lesson that neither code patch covers: adding a tool loop can make evidence-intensive tasks worse unless the task actually benefits from self-retrieval.

## Ranked top three

| Rank | Source | Area | Why read it | Targeted read |
|---:|---|---|---|---:|
| 1 | [Codex MCP credential provenance](https://github.com/openai/codex/commit/c7e80f873f) | Agent harness / MCP security | A full patch tracing credential authority through reconnect, catalog, runtime, and caches | 6 min |
| 2 | [Synthetic Hospital](https://arxiv.org/abs/2609.30027) **(7-day fallback)** | Retrieval/document-agent evals | Ground-truth-first longitudinal records expose evidence omission and tool-loop regressions | 7 min |
| 3 | [Agents SDK special-file guard](https://github.com/openai/openai-agents-python/commit/848ba479a3) | Sandboxed file tools | An inspectable ordering fix: validate the opened object before destructive truncation | 5 min |

## 1. Codex: an executor's MCP declaration must not borrow host credentials

**Primary link:** [Commit `c7e80f873f`](https://github.com/openai/codex/commit/c7e80f873f), committed September 25 at 17:15 UTC.

**User and operator mental model.** An executor supplies an MCP-server declaration, potentially naming an environment variable containing a bearer token. The Codex host catalogs that server, connects to it, and caches both connection and tool metadata. On a later reconnect, the executor may lack the capability to resolve its own environment headers. The danger is treating a cached executor-owned declaration as permission to resolve a same-named **host** environment secret. The [commit rationale and patch](https://github.com/openai/codex/commit/c7e80f873f) identify that provenance boundary.

**Why it matters and what changed.** `McpCredentialPolicy::ExecutorOnly` now travels from registration through catalog materialization and effective-server construction. Executor-owned declarations fail closed when they would require host bearer-token fallback or host environment header/helper resolution; host-configured declarations keep their prior fallback. Connection identities and tool-catalog fingerprints include the policy and avoid reading host values for executor-only entries. The patch also distinguishes a selected HTTP plugin's **source** environment from its execution destination. [The complete diff](https://github.com/openai/codex/commit/c7e80f873f) shows each propagation point.

**Key mechanism and evidence.** A reconnect test uses different host and executor credential canaries, downgrades advertised executor capabilities, forces a fresh logical connection, and asserts the host canary never reaches captured HTTP requests. Unit tests cover catalog rebuilds, policy-specific cache identity, and bearer lookup. These are test assertions in a 21-file patch, **not tests rerun for this digest**. The commit alone does not prove a tagged release or deployed protection. [Patch and tests](https://github.com/openai/codex/commit/c7e80f873f).

**Engineering takeaway (inference).** Carry declaration provenance as durable security state, including in cache keys; never re-derive credential authority from current capabilities or destination alone. Test reconnect after a capability downgrade with same-named secrets on both sides.

**Limitations.** The review used the full commit diff, not a complete checkout or production trace. The test's proxy/canary scenario is controlled, and other credential-bearing paths were not exhaustively audited. **Targeted read: 6 minutes.**

## 2. Synthetic Hospital: benchmark the evidence chain, not just medical recall

**Primary link:** [Park, Chen, and Dettmers, *Synthetic Hospital*](https://arxiv.org/abs/2609.30027). **Seven-day fallback:** arXiv first posted it September 24 at 16:00:56 UTC, outside today's 24-hour window.

**Problem statement.** Longitudinal electronic health-record tasks need multiple visits and chart sections, but real records are difficult to share and generally lack complete observable ground truth. The authors build fictional records whose facts and labels are set before notes are narrated, allowing a retrieval or document agent's evidence path to be scored. This is a benchmark-construction claim, **not proof of clinical safety**. [Paper construction and Figure 1](https://arxiv.org/pdf/2609.30027).

**Method.** Public medical-education cases are mapped to diagnosis/finding graphs and standardized ontologies, clustered into **1,268 patients and 5,602 encounters**, rendered as longitudinal charts, and exposed through a simulated EHR with tool access. Patient-disjoint splits cover diagnosis, whole-patient and specialty summaries, chart-section retrieval, and imaging indication. The authors report 200 public diagnosis, summary, and retrieval instances each, with 800 training and 268 held-out patients. [Paper Tables 2-3 and appendices](https://arxiv.org/pdf/2609.30027).

**Key evidence.** On the public split, the best tested diagnosis severity-weighted F1 is **0.732** (200 instances); the best whole-patient key-finding F1 is **0.550** (200), implying substantial omission even in the leading summary; the best chart-section retrieval P@5 is **0.833** (200). In a separate 100-patient, three-model tool-agent study, the reported extra loop hurts summary, retrieval, and imaging across the nine model-task combinations outside diagnosis, while self-retrieving diagnosis improves for the tested models. These are separate experiments with different denominators. [Tables 3-4](https://arxiv.org/pdf/2609.30027) report the scores and design.

**Applicability (inference).** For a document agent, compare a deterministic section-gathering baseline plus one model turn against a general tool loop. Measure evidence-section ranking, temporal linkage, negation, final-answer omission, and cost separately. Use the benchmark's explicit provenance to diagnose *where* a correct fact was lost, not merely whether the final answer scored.

**Limitations and skepticism.** The cases are synthetic and intentionally diagnostically informative, not population-calibrated or a substitute for messy real charts. A blinded realism result of **53%** came from 100 judgments over only **ten distinct records**. The agent comparison uses one scaffold and a 40-action budget, so it does not establish that tool use generally hurts. Physician reference scores use only 13 patients, not the full public split. The PDF and [public repository](https://github.com/sparkcpark/synthetic_hospital) were identified; its code, dataset, and scorer were not run or independently audited.

**Citation gate: PASS.** The exact [OpenAlex work](https://openalex.org/W7214380492) assigns coauthor Tim Dettmers to [author ID `A5067514564`](https://openalex.org/A5067514564), whose saved profile reports **5,359** citations; [CMU](https://csd.cmu.edu/people/faculty/tim-dettmers) corroborates the affiliation. See the local author audit (local research intermediate discarded). **Targeted read: 7 minutes.**

## 3. Agents SDK: validate the opened file before truncating it

**Primary link:** [OpenAI Agents SDK commit `848ba479a3`](https://github.com/openai/openai-agents-python/commit/848ba479a3), committed September 25 at 21:45 UTC.

**User and operator mental model.** An agent's sandbox file tool reads or overwrites a workspace path. The final path component may be replaced by another process or may already be a FIFO, socket, or device. A leaf `O_NOFOLLOW` flag rejects symlinks but does not establish that the object is a regular file; a FIFO open may wait for a peer, and `O_TRUNC` may act before validation. [The before/after diff](https://github.com/openai/openai-agents-python/commit/848ba479a3) makes this ordering visible.

**Why it matters and what changed.** Shared UnixLocal read/write operations now pre-screen the leaf, open with `O_NOFOLLOW | O_NONBLOCK`, validate the resulting descriptor with `fstat`, and only then call `ftruncate` for a write. The descriptor check handles a leaf swapped after pre-screening; nonblocking open avoids hanging on a peerless FIFO. New tests cover FIFO and swapped-leaf behavior, stable special files, regular-file preservation, and Linux file leases. [Patch and tests](https://github.com/openai/openai-agents-python/commit/848ba479a3).

**Engineering takeaway (inference).** Put destructive effects *after* descriptor-level type validation, and test both the stable special-file case and a replacement between `stat` and `open`. Audit all callers that share the helper, not only the method named `write`.

**Limitations.** The precheck cannot eliminate every race or all possible device-open side effects. The tests were read, not executed; package release, cross-platform behavior, incident frequency, and performance impact were not verified. **Targeted read: 5 minutes.**

## What I would read first

Start with the Codex reconnect test and policy propagation, then Synthetic Hospital's Tables 3-4. The first shows an authority boundary; the second shows that a more elaborate agent loop is not automatically a better evidence reader.

## What I would prototype or inspect

1. Reconnect an executor-discovered MCP server after removing its environment-header capability; put a same-named credential on the host and assert that neither requests nor cache reuse expose it.
2. On a longitudinal document set, compare fixed section gathering with a 40-action retrieval agent; log evidence recall, omitted facts, final-answer quality, latency, and tool cost separately.
3. In sandbox file-tool tests, replace a validated regular leaf with a FIFO before `open`; assert no hang, no peer-visible bytes, and no truncation before `fstat`.

## Audit

**145 distinct candidates screened** (including 37 explicitly re-screened prior leads); **60 full raw PDF/HTML/diff artifacts plus 51 metadata/author records** preserved (111 manifest records); **3 selected sources backed by 7 selected local artifact records**; **0 degraded selected sources**; paper citation gate **PASS**; runtime gate **PASS** (`gpt-6-sol`, high for coordinator and all seven workers). The seven-day fallback was used only for the paper. A separately read IterSynth preprint was held because its exact-work OpenAlex author ID did not match the high-citation profile used in initial discovery. The artifact directory is `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-26`.

Audit files: candidates (local research intermediate discarded), manifest (local research intermediate discarded), fanout report (local research intermediate discarded), full-read reports (local research intermediate discarded), evidence matrix (local research intermediate discarded), author citation audit (local research intermediate discarded), and runtime audit (local research intermediate discarded). No PDF was rendered.
