# Daily Must-Read: 2026-09-13

**Measure the whole agent workflow, not a convenient proxy.** Today's selections ask whether fewer output tokens mean lower cost, whether an available endpoint means usable conversation state, and whether safe base-model behavior survives retrieval.

Prepared for the September 13 cutoff, **16:05:46 UTC**. Primary window: the preceding 24 hours. **Seven-day fallback used** for two selections because fewer than three primary-window sources survived final curation. Later retrieval timestamps do not move the cutoff. Digest reading time: approximately five minutes.

| Rank | Must-read | Window | Main reason |
|---|---|---|---|
| 1 | [Quesma's RTK evaluation](https://quesma.com/blog/does-rtk-make-ai-coding-cheaper/) | Sep 11, fallback | Test whole-task economics, not a compression counter |
| 2 | [SGLang Responses persistence](https://github.com/sgl-project/sglang/commit/14a131ad5b43bbb9dd7c5e91968e21e0c6432e4c) + [PD routing](https://github.com/sgl-project/sglang/commit/6220f45d8e9a932857b5490e81d1fe9bfc70e841) | Sep 13, primary | Foreground API support does not imply stored conversations |
| 3 | [RAG-Safety-Bench](https://arxiv.org/html/2609.11758v1) | Sep 10, fallback | Separate retrieval answerability from safety |

**Evidence key:** verified code means inspected source, not executed tests. Experimental findings are attributed to their authors. Engineering implications are recommendations, not measured results. Two sources have explicit evidence qualifications below.

## Quesma: Measure Task Cost, Not Filtered Tokens

**Seven-day fallback, September 11. Source read: about 10 minutes.** [Primary evaluation](https://quesma.com/blog/does-rtk-make-ai-coding-cheaper/).

**Operator mental model.** RTK rewrites shell calls to return less text to a coding agent. Smaller outputs can save input tokens, but can also change the agent's subsequent turns.

**Author-reported evidence.** Quesma ran Terminal-Bench 2.1 with RTK 0.45.0: 85 Claude Code/Fable tasks and 89 OpenCode/DeepSeek tasks, five attempts per arm, 1,740 attempts total. Four Fable refusal tasks were excluded. Total spending per observed pass changed about -3% and +7%, respectively. Equal-task average cost changed +1% and +17%; Fable's aggregate savings depended largely on one task. [Methods and charts](https://quesma.com/blog/does-rtk-make-ai-coding-cheaper/).

**Key mechanism.** DeepSeek's average turn used 7% less input, but there were 18% more turns. A local compression counter therefore missed a consequential whole-run change.

**Engineering implication.** Compare total spending, spending per pass, task-weighted effects and pass rates on matched tasks before adopting compression.

**Limitations / qualified evidence.** This is one evaluator's two-stack experiment, not proof compression never helps. Attempt trajectories are available only on request; pricing and confidence-interval methods are incomplete. We inspected the report and figure data, not reproduced the runs.

## SGLang: A Responses Endpoint Is Not a Conversation Store

**Primary window, September 13. Source read: about 15 minutes.** [Persistence change](https://github.com/sgl-project/sglang/commit/14a131ad5b43bbb9dd7c5e91968e21e0c6432e4c) and [HTTP prefill/decode routing](https://github.com/sgl-project/sglang/commit/6220f45d8e9a932857b5490e81d1fe9bfc70e841), one linked item.

**Operator mental model.** You can serve an agent's foreground Responses requests through separate prompt-processing and token-generation workers. That does not mean those workers share conversation history.

**Verified code.** The router dispatches to both workers and returns decode output. Response storage now defaults off even on standalone servers. Effective retention requires `--enable-response-store` plus a truthy request `store`; responses may still echo `store:true` when nothing is retained. With storage disabled, predecessor IDs and background requests are rejected. PD workers cannot enable storage, so clients must send explicit history. [Code and tests](https://github.com/sgl-project/sglang/commit/14a131ad5b43bbb9dd7c5e91968e21e0c6432e4c).

**Engineering implication.** Add upgrade tests for continuation, streaming errors and effective retention. Deploy compatible router/worker versions together.

**Limitations.** Enabled history is process-local, unbounded and lost on restart, not durable sessions. Default-off is not a zero-logging guarantee. Tests use mocked generation or workers; no throughput gain, GPU cleanup guarantee or tenant isolation was demonstrated by this review.

## RAG-Safety-Bench: Separate Retrieval Success from Safety

**Seven-day fallback, September 10. Focused read: 15 minutes for method and results; full paper: 45-60 minutes.** [Paper](https://arxiv.org/html/2609.11758v1).

**Problem and method.** A poor retriever can look safe simply because it never finds enabling information. This benchmark supplies fixed contexts: none, answer-bearing, related but audited as answer-free, or random. It evaluates 346 harmful questions across four conditions and five 7B-14B open models: 6,920 responses, not independent questions.

**Author-reported evidence.** For Qwen-2.5-7B, unsafe-answer accuracy rises from 15.9% without retrieval to 82.9% with answer-bearing context, each over 346 questions. This measures delivery of reference harmful content, not the separate majority-judge harmfulness metric or real-world effectiveness. [Table 3](https://arxiv.org/html/2609.11758v1).

**Applicability, inferred.** Reuse the four-condition diagnostic and distinguish safety refusal from inability to answer.

**Limitations / qualified evidence.** Prompts and context lengths are not fully controlled; targets are small models, and results were not reproduced. The full read found prose-versus-figure discrepancies in judge agreement and one category discussion. Do not generalize topical-context harm to every model.

**Citation gate: passed.** Kathleen C. Fraser has 3,718 total citations in the preserved, identity-matched [Scholar profile](https://scholar.google.ca/citations?user=uGeC7NMAAAAJ&hl=en); this is an archived observation, not today's exact count.

## What I would read first

**Quesma**, especially the contrast between total spending, equal-task averages and spending per observed pass. It is directly relevant to evaluating changes to a coding-agent harness.

## What I would prototype or inspect

Run a small matched baseline/compression experiment with task success, full token-cost breakdown, turns and tool errors recorded together. For SGLang, inspect the effective server storage setting and test a two-turn continuation after upgrading. For retrieval, adapt the four context conditions with equal-length controls and human review of judge disagreements. These are proposed checks, not experiments completed in this digest.

## Audit

**325 distinct candidates screened:** 229 repository changes, 69 papers, 27 engineering-post/builder leads. **151 distinct raw artifacts**, plus 34 derived text extractions; 188 manifest records contain 185 distinct content hashes. **8 selected core artifacts**, covering all three selections; supplemental immutable code and citation evidence are also preserved. **3 completed selected-source reads**, plus an ADK reserve read. **2 qualified/degraded sources**, zero selected sources missing core evidence. **Paper gate passed:** identified author with 3,718 observed total citations.

Coverage is sampled, not exhaustive. The date-bounded arXiv API timed out twice, including one retry; later live listings were screened by individual submission history. A nonselected Braintrust page failed web-open and its retry, but its direct HTTP artifact was available. No selected-source fetch or full-reader failure remained. Some source snapshots were fetched after the cutoff; immutable commits/versioned papers and publisher dates establish scope, not perfect historical capture of every live-page byte. No downloaded tests or benchmarks were executed. No final PDF was rendered.

Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-13`.

Candidate audit (local research intermediate discarded) · Artifact manifest (local research intermediate discarded) · Fan-out report (local research intermediate discarded) · Evidence matrix (local research intermediate discarded) · Author-citation gate (local research intermediate discarded) · Selection rationale (local research intermediate discarded)
