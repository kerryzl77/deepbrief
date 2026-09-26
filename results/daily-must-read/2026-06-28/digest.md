# Daily Must-Read Applied AI Engineering Digest - 2026-06-28

Reader profile: senior applied AI engineer building Codex/Claude Code-like agents, sandboxed tool runtimes, retrieval/document agents, evals, tracing, and production AI systems.

Primary window: last 24 hours from 2026-06-28 09:02 America/Los_Angeles. Fallback used: 7-day fallback for one MCP SDK item and the daily paper slot. Estimated read time: 19 minutes.

## Ranked Top 3

| Rank | Source | Window | Topic | Why it made the cut | Est. |
| --- | --- | --- | --- | --- | --- |
| 1 | [OpenAI Codex plugin source-policy runtime enforcement](https://github.com/openai/codex/commit/9dbdb4e2c08723e8fc9c18f64d7ccad3dadc03a7) | Primary | Plugin marketplace security / enterprise policy | Strongest primary-window runtime/security item; policy now shapes loaded plugin state, discovery, read paths, and cache refresh admission. | 7 min |
| 2 | [MCP Python SDK RFC 6570 URI templates](https://github.com/modelcontextprotocol/python-sdk/commit/24717cc8eb1701880151697c817e6c7e999a3c9e) | 7-day fallback | MCP resource routing and path-safety | High-signal protocol SDK change: richer resource templates plus pre-handler security semantics. | 6 min |
| 3 | [Agentic Generation of AST Transformation Rules for Fixing Breaking Updates](https://arxiv.org/abs/2606.24446v1) | 7-day fallback paper slot | Agentic code repair / reusable migration rules | Paper slot with strong author gate; reframes repair agents as reusable AST transformation generators instead of one-off patch writers. | 6 min |

## 1. OpenAI Codex Plugin Source-Policy Runtime Enforcement

Primary link: [openai/codex commit 9dbdb4e2c087](https://github.com/openai/codex/commit/9dbdb4e2c08723e8fc9c18f64d7ccad3dadc03a7)

User/operator mental model: this is about enterprise control over where Codex plugins and plugin marketplaces may come from. A user can still have a plugin enabled in raw local config, and plugin files may still exist in cache. After this patch, if enterprise requirements say that marketplace source is not allowed, Codex projects the raw config into an allowed runtime view: the plugin becomes inactive, disappears from list/read/discovery flows, and is not refreshed back into active cache state. Think "policy-hidden at runtime", not "deleted from disk".

Why it matters: plugin systems are a tool-authority boundary. A policy that only blocks future installs is not enough if previously installed or cached plugins can still load. This patch makes source policy participate in runtime plugin state, marketplace discovery, plugin reads, CLI reporting, and background refreshes.

What changed: the patch routes effective marketplace/plugin config through the enterprise source policy, filters plugin list/read/discovery and CLI marketplace source reporting, validates background cache refresh sources, and includes policy-projected plugin state in cache/refresh keys so requirement changes invalidate stale plugin results. It also changes non-curated refresh to continue past a broken plugin and return per-entry errors.

Key mechanism: `project_effective_user_config` builds a policy-projected copy of user config. `configured_plugins_from_stack` now reads from that projection and takes `codex_home`, so loader/manager/cache-key paths derive plugin state from policy rather than raw config. Marketplace listing keeps curated sources or configured marketplace names admitted by policy. Plugin reads validate marketplace installation under policy. Background refresh receives projected plugin keys and policy-admitted roots, then accumulates per-plugin refresh errors instead of aborting the whole batch.

Concrete engineering takeaways:

- Keep raw config intact for auditability, but force runtime load/read/list/refresh paths through a policy-projected view.
- Treat cached plugin files as untrusted unless the current source policy still admits their marketplace.
- Put policy-projected state into cache keys; otherwise a policy change can keep stale plugin visibility alive.
- For multi-source plugin refresh, accumulate per-entry errors so one broken marketplace does not block healthy marketplaces.

Limitations and skepticism: this is PR 2 of 2 and depends on the admission model/source matcher in a prior PR, so the full matching semantics are not proven by this artifact alone. I did not build Codex or run tests; test results are source-reported in the patch. The user-facing label for "enabled in config but inactive by policy" is not visible in this diff.

Local evidence: `sources/raw/repo-commit-openai-codex-9dbdb4e2c087.patch` and `reviews/subagents/read-repo_commit-openai-codex-9dbdb4e2c087.md`.

## 2. MCP Python SDK RFC 6570 URI Templates With Path-Safety Checks

Primary link: [modelcontextprotocol/python-sdk commit 24717cc8eb17](https://github.com/modelcontextprotocol/python-sdk/commit/24717cc8eb1701880151697c817e6c7e999a3c9e)

User/operator mental model: MCP resources are server-exposed data addressed by URIs. A resource template is the pattern clients can discover and fill in before calling `resources/read`. Before this patch, Python SDK templates were close to simple `{var}` route patterns. Now server authors can express richer URI shapes: single-segment IDs, multi-segment paths, optional query parameters, and exploded path segments. More importantly, client-controlled template values are decoded and checked before handler code runs.

Why it matters: MCP servers often expose filesystem, document, repo, database, or service resources. A template system that captures `../../etc/passwd` or an absolute path and passes it straight into a handler is a production footgun. This patch makes template expressiveness and path-safety policy part of the SDK surface rather than ad hoc handler code.

What changed: `@mcp.resource` now accepts an RFC 6570 subset: `{name}`, `{+path}`, `{?limit,sort}`, `{/path*}`, and related operators. The SDK parses templates at decoration time, rejects ambiguous/unsupported shapes, requires defaults for optional query-bound handler parameters, and adds `ResourceSecurity` plus `safe_join` path helpers.

Key mechanism: `ResourceTemplate` stores a parsed `UriTemplate` and a `ResourceSecurity` policy. Matching delegates to `UriTemplate.match()`, then validates each extracted scalar or exploded list element for path traversal, absolute path forms, and null bytes. A security failure raises `ResourceSecurityError`; `ResourceManager` converts that to "Unknown resource" and stops fallback to later templates, preventing a strict template from being bypassed by a permissive one. Low-level server users can import `UriTemplate` and path security utilities directly, but must apply the policy themselves.

Concrete engineering takeaways:

- Parse and reject ambiguous resource templates at registration time, not on the first user request.
- Treat path-shaped template values as hostile even after percent decoding.
- Use a distinct security failure internally, but return the same client error shape as "not found" to avoid leaking policy detail.
- Keep the containment boundary separate: `ResourceSecurity` is a pre-filter; filesystem handlers should still use `safe_join`.

Limitations and skepticism: this is an RFC 6570 subset, not full RFC 6570. Matching is an SDK-defined inverse because RFC 6570 specifies expansion, not matching. The default absolute-path detector intentionally treats values like `x:y` as Windows drive-relative, so non-filesystem identifiers with that shape may need exemptions. I did not run the SDK test suite.

Local evidence: `sources/raw/repo-commit-modelcontextprotocol-python-sdk-24717cc8eb17.patch` and `reviews/subagents/read-repo_commit-modelcontextprotocol-python-sdk-24717cc8eb17.md`.

## 3. Paper: Agentic Generation of AST Transformation Rules for Fixing Breaking Updates

Primary link: [arXiv 2606.24446v1](https://arxiv.org/abs/2606.24446v1)

Citation-gate note: passed. OpenAlex verifies Martin Monperrus at 7,106 citations and Benoit Baudry at 6,133 citations, both above the user's paper threshold.

Problem statement: when a dependency update breaks many client projects, current LLM repair systems usually generate project-specific patches. That does not scale when the same API-level incompatibility appears across multiple repos. The paper asks whether an agent can generate a reusable AST transformation rule instead.

Method: BIGBAG gives a coding agent a broken Maven client, compiler feedback, AST transformation engine docs, a blank transformation template, and new-version API/Javadoc docs. The agent runs a generate-apply-verify loop to synthesize a standalone Java AST transformation using Spoon or JavaParser. BIGBAG then reapplies the generated rule in isolation to verify that the rule itself fixes the seed client, and only verified transformations are tested on other projects broken by the same dependency update.

Key evidence: on 157 BUMP compilation-failure breaking updates, the best configuration reaches a 94.3% compilable-rule rate, and the best repair configuration reaches a 78.6% fix rate. JavaParser is generally easier for agents than Spoon because its API surface is simpler. Transfer is real but partial: 43 of 129 verified external targets are fixed, a 33.3% cross-project fix rate, with much better transfer when clients use the affected API uniformly.

Applicability to this reader: the core pattern is useful for dependency-update bots, internal SDK migrations, and platform deprecations. Ask the agent to produce a reusable migration rule, reject string/regex/pom bypasses, verify the rule independently, then roll it out across clients. This is more operationally valuable than one-off repo patches when the same change appears in many services.

Limitations and skepticism: the evaluation is Java/Maven only, runs each model/engine/update once, and treats build/test success as the correctness signal. Transfer failures show the main weakness: a rule synthesized from one seed project may cover only that seed's visible usage pattern. The natural next step is multi-client seeding or an explicit API-change inventory.

Local evidence: `sources/raw/arxiv-2606-24446v1.html`, `sources/papers/arxiv-2606-24446v1.pdf`, `sources/papers/arxiv-2606-24446v1.txt`, `verification/paper-author-citations-openalex.jsonl`, and `reviews/subagents/read-arxiv-2606-24446v1.md`.

## What I Would Read First

Read the Codex plugin policy patch first. It is the most directly reusable production pattern today: policy projection as the runtime source of truth for tool/plugin authority.

## What I Would Prototype Or Inspect

Prototype a policy-projected tool catalog: raw config stays unchanged, but every list/read/execute/cache-refresh path receives only the policy-projected catalog and includes a policy digest in cache keys. Separately, inspect whether your MCP resource handlers need URI-template path checks before handler invocation.

## Audit

Candidate count: 517. Raw artifact count: 63. Selected source count: 3. Selected artifact count: 5. Degraded selected-source count: 0. Paper citation gate: passed via OpenAlex for Martin Monperrus and Benoit Baudry. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-06-28`.
