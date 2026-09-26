# Daily AI Engineering Must-Read Digest - 2026-06-22

Audience: senior applied AI engineer building Codex/Claude Code-like agents, sandboxed tool runtimes, retrieval/document agents, evals, tracing, and production AI systems.  
Window: last 24 hours primary; fewer than three sources cleared the bar, so this digest uses the 7-day fallback window.  
Non-overlap: this excludes routine official OpenAI Codex and Anthropic Claude Code changelog coverage unless the source has broader engineering significance.

## Ranked Top 3

| Rank | Source | Topic | Why it cleared the bar | Est. read |
|---:|---|---|---|---:|
| 1 | [SafeClawBench: Separating Semantic, Audit-Evidence, and Sandbox Harm in Tool-Using LLM Agents](https://arxiv.org/abs/2606.18356) | Agent harness, sandbox safety evals | Directly attacks a blind spot in agent evals: semantic "refusal/pass" labels are not enough when tool state can still be harmed. | 8 min |
| 2 | [Decoupling Search from Reasoning: A Vendor-Agnostic Grounding Architecture for LLM Agents](https://arxiv.org/abs/2606.18947) | Retrieval infra, MCP, production grounding | Turns search into a controllable MCP-compatible retrieval gateway with routing, caching, source rendering, and output-contract control. | 6 min |
| 3 | [ProvenanceGuard: Source-Aware Factuality Verification for MCP-Based LLM Agents](https://arxiv.org/abs/2606.18037) | Document agents, provenance, tracing | Makes source attribution a first-class verification target for MCP/document agents, not a cosmetic citation feature. | 5 min |

Total estimated read time: 19 minutes.

## 1. SafeClawBench

Primary link: [arXiv:2606.18356](https://arxiv.org/abs/2606.18356)  
Supporting link: [Hugging Face dataset page](https://huggingface.co/datasets/sairights/safeclawbench)  
Local review: `reviews/subagents/read-safeclawbench.md`

Why it matters: If you are building Codex-like or Claude Code-like agents, this is the most useful source in today's set because it evaluates safety at the layer where harm actually lands: tool calls, persistent state, messages, files, databases, and sandbox-observed outcomes.

What changed: The paper introduces SafeClawBench, a 600-case benchmark across six attack families. The central move is to split evaluation into three endpoints: semantic attack acceptance, audit-visible evidence of harm, and sandbox-observed tool/state harm.

Key mechanism: The benchmark compares a semantic view of whether the model accepted a harmful request with an execution view of whether tool or state side effects actually occurred. The strongest result for agent engineers is that, in the matched Core-Exec analysis, 291 of 347 observed sandbox harms occurred where the semantic endpoint passed. In other words, a semantic judge alone would have missed most of the harms that the execution oracle saw.

Concrete engineering takeaways:

- Treat semantic refusal/pass as one signal, not the safety verdict.
- Add execution-state oracles to agent evals: before/after file state, DB state, message state, memory state, and tool-output audit trails.
- Score harm by attack family and tool surface, not just aggregate model pass rate.
- Preserve traces in a way that can distinguish requested intent, model plan, tool call, tool result, and persistent side effect.

Limitations and skepticism: This is a stress-test benchmark, not an estimate of production incident rates. I did not execute a benchmark runner locally. Treat the dataset as eval material, not as training data or operational telemetry.

## 2. Decoupling Search From Reasoning

Primary link: [arXiv:2606.18947](https://arxiv.org/abs/2606.18947)  
Local review: `reviews/subagents/read-decoupled-search-grounding.md`

Why it matters: This is a practical architecture paper for production retrieval agents. It argues that native model search is convenient but couples too many control surfaces: retrieval provider, source selection, latency, cost, evidence injection, formatting behavior, and generation behavior.

What changed: The paper proposes Decoupled Search Grounding, an MCP-compatible gateway that handles provider routing, source-aware rendering, fallback, retrieval-depth control, exact caching, and semantic caching outside the model.

Key mechanism: The search layer becomes a provider-agnostic tool plane. The LLM receives grounded evidence from the gateway while the application keeps control over provider choice, cache policy, citation rendering, and schema preservation. The paper also names a useful failure mode: Search-Induced Verbosity, where enabling search changes the answer style or output contract even when the application wants a compact structured response.

Concrete engineering takeaways:

- Put search behind a stable tool protocol instead of binding application behavior to one model vendor's native search feature.
- Separate retrieval policy from answer schema so source grounding does not break structured outputs.
- Log route, provider, cache hit, retrieval depth, source count, latency, and cost as first-class trace fields.
- Use exact and semantic caching only when the freshness contract allows it; route freshness-sensitive queries differently.

Limitations and skepticism: Native search still has an edge on freshness-sensitive tasks. Some production workload details and raw retrieved snippets are not public, and parts of the scoring rely on judge-based evaluation. The result is still directionally useful because the architecture maps well to real agent infrastructure.

## 3. ProvenanceGuard

Primary link: [arXiv:2606.18037](https://arxiv.org/abs/2606.18037)  
Local review: `reviews/subagents/read-provenanceguard.md`

Why it matters: Retrieval systems can be factually right against pooled context while citing the wrong document. For document agents, that is not a cosmetic bug; it breaks auditability, user trust, and downstream decision workflows.

What changed: ProvenanceGuard defines and evaluates source-aware factuality for MCP-based agents. It consumes MCP traces with stable tool IDs, source IDs, and raw outputs; decomposes answers into atomic claims; routes each claim to candidate evidence; applies NLI; and checks whether the cited source is the source that actually supports the claim.

Key mechanism: The verifier separates factual support from attribution correctness. On held-out claims, the paper reports block F1 of 0.802 and source accuracy of 0.858. On harder multi-source probes, exact source attribution becomes much weaker, with reported source accuracy of 0.503 and source-plus-relation accuracy of 0.229. That gap is the engineering signal: source binding is a separate, difficult problem.

Concrete engineering takeaways:

- Treat citations as structured claims tied to source IDs, not as final-answer decoration.
- Preserve raw MCP tool outputs and stable source identifiers so verification can run after generation.
- Evaluate claim support and source attribution separately.
- Add a "citation repair or abstain" path when answer support is present but attribution confidence is low.

Limitations and skepticism: The evaluated system is a medical MCP stack, so broad generalization is not proven. Multi-source attribution remains weak. Some repair results use the same verifier family for triggering and evaluating repair, so independent validation would be stronger.

## What I Would Read First

Read SafeClawBench first. It gives the clearest harness design lesson for tool-using agents: safety evals need execution-grounded state oracles, not just semantic judges.

## What I Would Prototype Or Inspect

Prototype a small eval harness that runs the same task through three channels:

- semantic accept/refuse judgment,
- audit-visible evidence from the model/tool trace,
- sandbox-observed state diff after tool execution.

Then add DSG-style retrieval trace fields and ProvenanceGuard-style source IDs to the same trace schema. The shared theme across all three sources is that agent reliability improves when side effects, evidence, source identity, and policy decisions become explicit trace objects.

## Audit

- Candidate count: 150
- Raw artifact count: 20
- Selected artifact count: 3
- Degraded-source count: 0
- Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-06-22`
- Supporting files: `sources/candidates.jsonl`, `sources/manifest.jsonl`, `reviews/fanout-report.md`, `reviews/subagents/*.md`, `verification/evidence-matrix.md`
