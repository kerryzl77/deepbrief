# Applied AI Engineering Must-Read Digest

**2026-09-05** | Primary window: 24 hours ending `2026-09-05T16:06:43Z`

Two selections are from the strict window. Because no paper was published inside that window, the paper slot uses the clearly labeled seven-day fallback. Total estimated reading time: **18 minutes**.

| Rank | Must read | Area | Window | Read |
|---:|---|---|---|---:|
| 1 | [MCP Python SDK: endpoint-scoped redirects and resource-bound bearer tokens](https://github.com/modelcontextprotocol/python-sdk/commit/c6762e821c527925f0b617db216d00fbd1d0bf99) | MCP transport and auth | Strict | 6 min |
| 2 | [SWE-Gate: Passing Functional Tests Is Not Enough for Software Engineering Agents](https://arxiv.org/abs/2609.04167) | Coding-agent evaluation | **7-day fallback** | 7 min |
| 3 | [Microsoft Agent Framework: preserve streamed annotations](https://github.com/microsoft/agent-framework/commit/2c49f50cf08ebb6c1687146336f039051f159333) | Retrieval and citation transport | Strict | 5 min |

## 1. MCP Python SDK: make the configured endpoint an authority boundary

**Primary sources:** [same-origin redirect policy](https://github.com/modelcontextprotocol/python-sdk/commit/c6762e821c527925f0b617db216d00fbd1d0bf99) and [bearer-token resource validation](https://github.com/modelcontextprotocol/python-sdk/commit/0c9136841ff092987a20700ff9c2c9789bda2f40).

**User/operator mental model.** An MCP operator names an endpoint twice: the client URL says where requests may go, and the server's public resource URL says which bearer tokens belong there. Redirects may normalize the endpoint, but must not transfer requests or credentials to another authority. A token may authenticate a principal, but still be invalid for this resource.

**Why it matters.** Tool runtimes routinely combine long-lived sessions, OAuth discovery, bearer headers, and attacker-influenced HTTP responses. The two patches close adjacent confused-deputy paths: forwarding MCP/OAuth traffic across an arbitrary redirect, and accepting a valid token minted for a different resource.

**What changed.** MCP transports no longer rely on general-purpose `follow_redirects=True`. The SDK applies a redirect policy to SSE, Streamable HTTP, and OAuth subrequests. Separately, servers can enable `AuthSettings.validate_token_resource` to compare a verified token's resource with `resource_server_url`. Redirect containment takes effect immediately; resource validation is opt-in for compatibility, warns when left unset with a configured resource URL, and is documented to become the default in 3.0.

**Key mechanism.** A redirect is followed only if it preserves the HTTP method, contains no userinfo, and stays on the same scheme/host/port, except for a same-host default-port HTTP-to-HTTPS upgrade. Cross-origin moves, downgrades, port changes, and POST redirects that rewrite the method are rejected; intermediate bodies are drained and hop counts are bounded. On the server, bearer middleware runs the operator's verifier first, then normalizes and compares the token resource URL before creating authenticated context.

**Concrete engineering takeaways.** Treat redirect policy as part of a tool protocol, not an HTTP-client convenience. Apply it to OAuth side requests as well as the main transport, test every session operation, sanitize rejected locations, and preserve liveness after policy failures. On the server, make token audience/resource binding explicit at the middleware boundary and test wrong-resource, missing-resource, refresh, and migration cases.

**Limitations/skepticism.** The redirect policy intentionally breaks legitimate cross-origin/CDN/vanity-host redirects unless operators configure the final URL. Resource enforcement remains off for legacy configurations until the planned 3.0 flip, and the SDK still relies on the verifier for signatures, issuer checks, and non-URL audience conventions. This was a static full-patch review; tests in the patches were not rerun locally.

## 2. SWE-Gate: test review constraints separately from functional correctness

**Primary sources:** [paper](https://arxiv.org/abs/2609.04167) and [public replication package](https://github.com/DeepSoftwareAnalytics/SWE-Gate). **Window:** seven-day fallback, published `2026-09-03T17:53:34Z`; there was no strict-window paper.

**Problem statement.** Repository repair benchmarks usually ask whether a patch passes issue-oriented functional tests. Maintainer reviews also impose compatibility, lifecycle, schema, ordering, error-semantics, and other acceptance constraints that a functionally correct patch can violate.

**Method.** SWE-Gate extracts atomic constraints from real pull-request review comments, transfers them into compatible Python repositories, and synthesizes 303 repair instances across 75 repositories. Each instance separates functional tests from constraint tests and includes a functionally passing but non-compliant patch plus a gold patch. Four models are run in one coding-agent scaffold under paired conditions that either expose or omit the natural-language constraint while retaining the same hidden tests.

**Key evidence.** The released labels reproduce the paper's headline aggregate: under the constraint-provided condition, 644 repairs pass functional tests and 221 of those fail constraint tests, a 34.3% hidden-failure rate. They also reproduce the reported joint-success deltas when constraints are shown. However, the audit found 36 groups in the +C archive where the exact same instance and encoded patch receive different functional outcomes, plus three same-model/same-instance patches with different outcomes across +C and -C. These contradictions mean the model comparisons and ablation deltas are not yet reliable evidence of a single deterministic evaluation regime.

**Applicability.** Agent evals should represent acceptance criteria as a second executable test surface and report functional success, conditional constraint following, and joint success separately. For production coding agents, preserve reviewer rationale and constraint provenance in task state; for harness evals, add compatibility, lifecycle cleanup, scope generalization, and sentinel distinctions rather than only more happy-path tests.

**Limitations/skepticism.** The strongest concern is internal evaluation consistency: byte-identical patches have contradictory test, container, or apply outcomes, and 26 +C infrastructure failures are asymmetrically counted as zeros while every -C record is marked evaluated. The slim package omits run logs and evaluator-version provenance, 48 instances lack released validation matrices, and construction-stage counts/rejections are absent despite the paper's reference to supplementary material. The tasks are also LLM-assisted synthetic transfers, Python-only, and selected for constraints that can be made executable. Treat the benchmark mechanism as promising and the reported model rankings/ablation as provisional until an immutable rerun is published.

**Citation gate.** **PASS.** Coauthor Hongyu Zhang's disambiguated OpenAlex record reports 20,677 citations, independently exceeding the 1,000-citation threshold. Topic, Chongqing University affiliation, and ORCID were used to reject a same-name search result and select [OpenAlex author A5100412598](https://openalex.org/A5100412598).

## 3. Agent Framework: preserve late citations by correlating events, not adjacency

**Primary source:** [commit](https://github.com/microsoft/agent-framework/commit/2c49f50cf08ebb6c1687146336f039051f159333).

**User/operator mental model.** A Foundry-hosted Responses call can stream answer text first and deliver citations later as annotation-only updates. Before this patch, those late annotations could disappear, leaving a grounded answer without citation objects in the stream or final response.

**Why it matters.** Citation loss at an adapter boundary makes retrieval output unauditable even when upstream retrieval succeeded. The failure is a state/correlation problem, not a retrieval-quality problem.

**What changed.** The .NET output converter now recovers response item IDs from flattened updates or recognized OpenAI event shapes, attaches annotation-only content only to the matching open message, deduplicates it, and maps URL, file, file-path, and container-file citations. The patch adds converter, handler, HTTP serialization, and hosted web/Azure Search scenarios across streaming and non-streaming responses.

**Key mechanism.** The open response item ID is the join key between text and delayed metadata. Missing IDs are handled conservatively: an annotation without an ID is dropped when the current message has one, rather than attributed to the wrong answer. Accepted citations remain buffered with the output-text item and appear in annotation events, done events, the completed response, and non-streaming JSON.

**Concrete engineering takeaways.** Give every streamed semantic item a durable correlation ID. Exercise metadata in both incremental and terminal representations, test mismatched and absent IDs, and define structural deduplication per citation type. Instrument unsupported annotation shapes and dropped correlations so citation-preservation regressions become observable.

**Limitations/skepticism.** Metadata preservation does not establish that a citation supports the claim, that spans are valid, or that a URL is trustworthy. Unsupported event/annotation shapes are skipped; late annotations after item closure and interleaved messages are not covered. Live tests exercise URL citations, while file citation forms use unit or in-process coverage. Tests were inspected in the patch but not executed locally.

## What I would read first

Read the MCP redirect predicate, transport call sites, and bearer-resource wiring first. It is the most transferable design here because it defines authority once and carries that invariant through transport, OAuth, middleware, failures, and migration behavior.

## What I would prototype or inspect

Add two focused checks to an agent stack: a transport conformance suite that injects redirect and wrong-audience failures into every tool/session operation, and an eval slice that pairs ordinary task tests with independently executable review constraints. For retrieval agents, inspect whether late citation metadata is joined by a durable item ID or merely attached to the latest text buffer.

## Audit

**1,796 candidates** | **87 raw/local artifact records** | **3 selected sources** | **5 selected primary artifacts** | **0 degraded selected sources** | **Paper citation gate: PASS** | Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-05`
