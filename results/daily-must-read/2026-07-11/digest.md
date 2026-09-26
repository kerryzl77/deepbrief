# Daily Applied AI Engineering Must-Read

**July 11, 2026 | Primary window plus clearly labeled 7-day fallback | Estimated reading time: 18 minutes**

Only one primary-window source cleared the final bar, so two stronger items from the 7-day fallback are included. Today's theme is that agent quality depends on explicit operational structure: a product-shaped tool policy, a mined workflow model for stateful testing, and a static trust boundary around system instructions.

| Rank | Source | Window | Topic | Read |
|---:|---|---|---|---:|
| 1 | [Better tools made Copilot code review worse](https://github.blog/ai-and-ml/github-copilot/better-tools-made-copilot-code-review-worse-heres-how-we-actually-improved-it/) | 7-day fallback | Harness/tool policy | 7 min |
| 2 | [Mining Workflow Graphs for Black-Box Boundary Testing of Conversational LLM Agents](https://arxiv.org/abs/2607.06873v1) | 7-day fallback | Stateful agent evals | 8 min |
| 3 | [CodeQL 2.26.0 adds system-prompt-injection detection](https://github.blog/changelog/2026-07-10-codeql-2-26-0-adds-kotlin-2-4-0-support-and-ai-prompt-injection-detection/) | Primary 24h | AI application security | 3 min |

## 1. GitHub: shared tools need a product-specific control policy

**User/operator mental model.** A Copilot code-review user still opens a pull request and receives review comments; there is no new UI or switch. The change is inside the review agent. After GitHub replaced review-specific navigation tools with shared Copilot CLI `grep`, `glob`, and `view` tools, the agent began behaving like a general repository explorer: broad searches led to broad reads, guessed paths, more searches, and accumulated context. GitHub says the initial migration cost more and found fewer useful issues. The corrected agent stays anchored to the diff and loads only the evidence needed to confirm or dismiss a review risk.

**What changed.** GitHub kept the shared tools but rewrote their instructions around a reviewer workflow: start from the diff, formulate a concrete question, batch cheap `grep`/`glob` discovery, use `view` only for known files or ranges, and recover from a bad query without widening into speculative browsing.

**Key mechanism.** Tool output is persistent working context, not disposable terminal output. The regression was therefore a control-policy mismatch rather than a capability failure. GitHub's trace harness compared call ordering, errors, returned context, evidence relevance, and review-quality metrics. The tuned version reportedly made a similar number of calls but spent more of them on relevant evidence. GitHub reports roughly 20% lower average production review cost than control without a quality signal that blocked shipping.

**Engineering takeaways.** Treat tool descriptions as executable API contracts. Separate discovery from reading, measure evidence density rather than call count alone, give bounded agents an anchor and stopping condition, and evaluate tool traces alongside final outputs. Shared implementations do not imply a universal policy: GitHub reports that the same narrowing instructions did not produce the same win for the broader, interactive Copilot CLI job.

**Limitations.** This is a first-party engineering report. GitHub does not disclose model versions, benchmark size, raw traces, absolute cost, variance, or the definition of useful comments. "No blocking quality signal" is weaker than proving identical quality, and narrow diff-first search can still miss nonlocal defects.

## 2. Paper: mine the hidden workflow before testing its boundaries

**Problem.** A conversational agent can fail at a confirmation gate, identity prerequisite, eligibility check, or value validation only after several prerequisite turns. A one-shot adversarial prompt cannot reliably reach these states, and a black-box tester cannot inspect the agent's prompts, tools, or internal state to learn where the boundaries are.

**Method.** AgentEval first explores fresh agent sessions and collects text traces. An LLM abstracts raw turns into recurring user actions and agent activities; deterministic code turns those labels into a directly-follows workflow graph. The system enumerates nodes, edges, starts, and ends as possible boundary locations, ranks them, replays an observed route to each selected state, then applies a perturbation such as skipping a prerequisite or continuing prematurely. A separate runner executes the test and a separate judge returns pass, fail, or inconclusive from the visible conversation. The generated plan can be replayed after model, prompt, policy, tool, or guardrail changes.

**Key evidence.** Across four tau^3-bench service-agent domains, the paper reports 23-38 distinct boundaries per agent with 50 boundary tests. On airline, phase-guided discovery raises functional coverage recall from 0.72 to 0.97. Structural graph targeting reports 23 distinct boundaries versus 12 for prompt-only generation; merely putting the graph into prompt context yields 9. The full airline system uses 285 LLM calls, 1.55 million tokens, and 2.5 hours. These are paper-reported results, not reproduced here.

**Applicability.** The method is a useful mental model for regression testing resettable service agents: discover recurring routes, make hidden state transitions explicit, and generate tests against structural locations rather than asking an LLM for "edge cases" in the abstract. It is particularly relevant to booking, support, account, and approval workflows.

**Limitations and skepticism.** Code and prompts are not yet released. Every configuration was run once, the privileged auditor is itself an LLM, and a trace-only oracle cannot detect silent backend corruption. Transactional boundary-test validity is only 0.78-0.79 because generated customer/record identities sometimes mismatch. More seriously, the reported duplicate-rate values do not reconcile with the paper's stated formula, validity rates, and 50-test budget; that metric should not be trusted without clarification.

**Citation gate.** Passed. The paper and official University of Ottawa profile identify the same Lionel Briand across Ottawa and Lero; the matching OpenAlex profile reports 29,384 citations. See the [official profile](https://www.uottawa.ca/faculty-engineering/school-electrical-engineering-computer-science/directory/lionel-briand).

## 3. CodeQL treats system instructions as a static trust boundary

**User/operator mental model.** CodeQL 2.26.0 is not a runtime prompt-injection firewall. During static code scanning, it can now identify a JavaScript/TypeScript path where a modeled untrusted value enters the program and flows into a modeled AI SDK argument with system-instruction authority. The result is a code-level risk finding before deployment, not evidence that an attack occurred or that a model followed malicious text.

**What changed.** The new `js/system-prompt-injection` query detects flows from user-provided values to system prompts. GitHub also expanded prompt-related sink models for selected OpenAI, Anthropic, and Google GenAI APIs, including OpenAI Realtime instructions and Google system instructions/cached content. The legacy OpenAI completions prompt is classified as a user-prompt sink because that API has no role separation.

**Key mechanism.** Static taint analysis marks modeled entry points as sources, propagates that label through understood data-flow steps, and reports a path when it reaches a modeled system-prompt sink. The sink modeling is the important engineering artifact: prompt roles are security semantics, not merely SDK syntax.

**Engineering takeaways.** Keep system instructions derived from trusted configuration or code, review new findings after query-pack upgrades, and maintain custom models for wrappers or internal SDKs. Absence of an alert is not a safety guarantee because unmodeled sources, sinks, dynamic code, retrieval paths, and framework abstractions may be invisible.

**Limitations.** The release provides no benchmark, precision/recall result, severity, sanitizer model, or exhaustive SDK coverage claim. GitHub.com receives the update automatically; GHES availability is deferred to a future release or manual CodeQL upgrade.

## What I would read first

Read the GitHub harness post first. It gives the most immediately reusable model: tool capability, tool instructions, task anchor, and trace-based eval must be designed together. Read the paper second if you own stateful service-agent evals.

## What I would prototype or inspect

1. Add an "evidence density" trace metric: relevant bytes/tokens returned per tool call, split by discovery and read operations.
2. For one resettable agent workflow, mine a small directly-follows graph from successful traces and generate tests per node/edge boundary; compare it with prompt-only edge-case generation.
3. Run CodeQL 2.26.0 against one AI service and inspect whether internal prompt wrappers need custom source/sink modeling.

## Audit

255 candidate records screened, including 183 substantive sources and 72 blocked-feed diagnostics; 50 raw/local artifacts preserved; 6 selected artifacts across 3 sources; 0 degraded selected sources. Paper gate passed for arXiv:2607.06873v1 through an affiliation-resolved Lionel Briand citation profile. Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-07-11/`.
