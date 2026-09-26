---
title: "OpenAI Research History: Lecture Notes"
subtitle: "A technical course book over papers, people, methods, and research trajectory"
date: "2015 to 2026-06-15"
abstract: |
  Bibliography-backed lecture notes covering papers, reports, findings, methods,
  model training, post-training, reasoning, interpretability, safety, evaluations,
  agents, deployment, researchers, and collaboration patterns.
---

# How to Use This Book

Claim OAI-F-C1. This course is organized as a research-history book rather than a release chronology: read each lecture as an explanation of how a technical idea changed OpenAI's research agenda, then use Lecture 11 and the Citation Appendix to return to the original papers and system cards [1](#source-1) [4](#source-4) [10](#source-10) [13](#source-13).

Claim OAI-F-C2. The book separates three evidence levels. A source-specific technical claim is tied to a paper or system card; a trajectory claim is tied to several adjacent sources; and a corpus-coverage claim is tied to discovery artifacts such as the OpenAI publication and research sitemaps [11](#source-11) [12](#source-12) [16](#source-16) [17](#source-17).

Claim OAI-F-C3. Treat every citation as a prompt to inspect the underlying paper. These notes deliberately avoid treating marketing pages as papers, avoid inferring private training details, and mark product or runtime behavior as supported only when a public technical report or system card directly supports it [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

# Course Map

Claim OAI-MAP-C1. The OpenAI arc in this corpus begins with embodied reinforcement learning and large-scale self-play, moves through language-model scaling and multimodal contrastive learning, then turns toward human feedback, system cards, reasoning models, and capability-specific evaluation [1](#source-1) [3](#source-3) [4](#source-4) [5](#source-5) [10](#source-10) [13](#source-13) [14](#source-14).

```mermaid
flowchart TB
  A["2018-2019: RL systems"] --> B["2020: GPT-3"]
  B --> C["2021-2022: multimodal plus feedback"]
  C --> D["2023: GPT-4"]
  D --> E["2024-2025: cards and reasoning"]
```

Claim OAI-MAP-C2. The course map is not a claim that OpenAI abandoned earlier threads. Robotics, games, multimodality, language modeling, and safety work overlap; the map only gives a useful reading order for the public record [1](#source-1) [2](#source-2) [3](#source-3) [5](#source-5) [7](#source-7) [12](#source-12).

![GPT-3 source figure showing the paper's in-context learning framing across pretraining and prompted examples](images/openai/gpt3-scaling-figure-000.png)

Claim OAI-MAP-C2A. The selected GPT-3 figure is included to show the paper's own pedagogical distinction between broad unsupervised pretraining and in-context task examples; it should not be read as a full training-recipe disclosure [4](#source-4).

```mermaid
flowchart TB
  S["Scaling"] --> G["GPT reports"]
  S --> M["Multimodal"]
  H["Feedback"] --> I["Instruction"]
  E["Evaluation"] --> C["Cards"]
  R["Reasoning"] --> O["o1 and code"]
  G --> C
  I --> C
  O --> C
```

Claim OAI-MAP-C3. Lectures 1-4 explain technical identity, scaling, feedback, and reasoning. Lectures 5-9 explain modalities, internals, safety, measurement, and product feedback loops. Lectures 10-12 shift from individual papers to people, collaboration patterns, bibliography, and synthesis [4](#source-4) [8](#source-8) [9](#source-9) [10](#source-10) [11](#source-11) [14](#source-14).

# Prerequisite Crash Course

Claim OAI-PR-C1. A transformer language model is a sequence model trained to predict or model text tokens; the public OpenAI course arc uses this concept most visibly in GPT-3, InstructGPT, GPT-4, and later system-card material [4](#source-4) [10](#source-10) [11](#source-11) [13](#source-13).

Claim OAI-PR-C2. Scaling in these notes means changing model size, data, compute, or training setup and then measuring how capabilities change. The course uses GPT-3 as the main pretraining scaling case, Dota 2 as a large-scale RL case, and GPT-4/o1 reports as later evidence that measurement became more central as capabilities rose [3](#source-3) [4](#source-4) [11](#source-11) [13](#source-13).

Claim OAI-PR-C3. Post-training means methods applied after or alongside broad pretraining to shape model behavior. In this corpus the central examples are recursive summarization with human feedback and InstructGPT's supervised fine-tuning, reward modeling, and reinforcement learning from human feedback pipeline [9](#source-9) [10](#source-10).

Claim OAI-PR-C4. Multimodality means connecting text with other modalities such as images or speech. CLIP uses natural-language supervision for transferable visual models; DALL-E and DALL-E 2 generate images from text-conditioned representations; Whisper studies speech recognition with large-scale weak supervision [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8).

Claim OAI-PR-C5. A system card or model card is not the same object as a methods paper. It usually emphasizes intended use, evaluation categories, risk management, mitigations, and limitations; this course reads GPT-4o, o1, and gpt-oss cards as evidence about research-to-deployment governance and evaluation framing, not as complete training disclosures [12](#source-12) [13](#source-13) [15](#source-15).

Claim OAI-PR-C6. The self-check habit for this book is simple: when a paragraph names a method, ask whether the cited source gives the method; when a paragraph names a capability, ask whether the cited source measures it; when a paragraph names a deployment practice, ask whether the cited source directly describes it [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13).

## Lecture 1: Origins And Research Identity

### Learning goals

After this lecture, you should be able to explain why early OpenAI research was organized around scalable reinforcement learning, simulation, games, and robotics rather than only language modeling; distinguish demonstrated capability from task restrictions in Dactyl, Rubik's Cube, and OpenAI Five; and connect those early systems to later frontier-model habits: large-scale training infrastructure, careful evaluation protocols, and a willingness to treat compute and environment design as scientific instruments [1](#source-1) [2](#source-2) [3](#source-3).

### Key terms

Domain randomization means training over a deliberately varied family of simulated worlds so that a policy can transfer to the real world despite simulator error [1](#source-1). Automatic domain randomization extends this idea by adapting the range of randomized parameters as the agent improves, turning the simulator distribution into a curriculum [2](#source-2). Self-play is training through repeated play against current or past versions of the policy, a central technique in OpenAI Five [3](#source-3). Sim-to-real transfer is the movement of a policy trained in simulation onto physical hardware; in these papers it is enabled by randomized dynamics, structured sensors, recurrent memory, and substantial systems engineering [1](#source-1) [2](#source-2).

### Full explanation

Claim OAI-L1-C1. OpenAI's early research identity was not "large language models first." A major strand was the belief that general capabilities could be produced by combining relatively simple learning algorithms with large-scale environments, distributed systems, and evaluation setups demanding flexible behavior. The dexterous-hand work trained a policy entirely in randomized simulation and deployed it on a physical Shadow hand for in-hand object reorientation; OpenAI Five scaled PPO and self-play to a long-horizon, partially observed team game; the Rubik's Cube robot extended the same sim-to-real thread with automatic domain randomization and recurrent adaptation [1](#source-1) [2](#source-2) [3](#source-3).

Claim OAI-L1-C2. The robotics papers are best read as systems papers as much as algorithm papers. In the in-hand manipulation project, the task was to rotate a block or prism to target orientations until the object was dropped or a trial limit was reached. The learned policy used recurrent control, asymmetric actor-critic training, PPO, and a separately trained synthetic-vision pose estimator. The result was not general hand intelligence, but a carefully bounded demonstration that simulation-only training could survive the reality gap when the simulator distribution, sensors, and hardware interface were engineered together [1](#source-1).

Claim OAI-L1-C3. The phrase "trained entirely in simulation" should not be confused with "free of real-world priors." The Dactyl system depended on calibrated hardware, selected sensors, randomized masses and friction, observation noise, action delays, and a lab setup that made the transfer problem tractable. The authors also reported clear limits: small physical trial counts, fragile hardware, weaker transfer on some shapes, and a reality gap that randomization narrowed but did not eliminate [1](#source-1).

Claim OAI-L1-C4. Rubik's Cube made the curriculum idea more explicit. The system separated symbolic cube solving from manipulation: a conventional solver produced the sequence of cube moves, while the learned policy executed face rotations and cube flips with a robot hand. Its automatic domain randomization expanded or contracted simulator parameter ranges according to boundary performance. That matters historically because the environment distribution became an adaptive training object, not merely a background source of data augmentation [2](#source-2).

Claim OAI-L1-C5. The Rubik's Cube result also shows why OpenAI's public demonstrations need careful reading. The policy did not solve arbitrary standard-cube manipulation from raw vision alone. Important evaluations used a modified cube or asymmetric stickers, and the best reported success rates varied substantially across settings. The paper's durable contribution is the stack: robot hardware modifications, synthetic vision, recurrent policies, ADR, hidden-state adaptation, and large-scale simulation. The spectacular public image sits on top of that stack [2](#source-2).

Claim OAI-L1-C6. OpenAI Five extended the same identity into strategic games. Dota 2 supplied long episodes, partial observability, multi-agent coordination, and a huge action space. OpenAI Five used existing deep RL ingredients such as PPO, actor-critic learning, recurrence, reward shaping, and self-play, but scaled them through a distributed system that generated massive batches and sustained training across months of game and model changes [3](#source-3).

Claim OAI-L1-C7. The Dota result was historically important and also restricted. OpenAI Five defeated the world champion team OG under OpenAI Five rules and then won almost all public games during a public play period. Yet it used only a subset of heroes, excluded some items, relied on semantic observations rather than pixels, and scripted several game subsystems such as item purchasing and ability builds. The right lesson is not that deep RL solved full Dota 2; it is that a scaled, engineered self-play system could reach elite performance in a large, partially constrained strategic environment [3](#source-3).

### Discussion 1.1

The early OpenAI pattern was "scale the training loop" before it was "scale the language model." In robotics, scaling meant converting simulation experience into wall-clock progress with many workers and GPUs. In Dota, scaling meant managing batch size, data freshness, sample reuse, self-play opponents, and policy migration across changing environments. These systems trained agents, but they also trained the organization to build long-running experimental machines whose behavior depended on infrastructure, monitoring, and iteration discipline [1](#source-1) [2](#source-2) [3](#source-3).

This identity helps explain later OpenAI work. GPT-3 and GPT-4 look different from robot hands and Dota agents, but they inherit several habits: evaluate broad behavior rather than only a narrow loss number; accept that compute changes what can be attempted; build large data and training systems; and document limitations because the public headline almost always compresses a much messier experimental setup [3](#source-3) [4](#source-4) [11](#source-11).

### Worked examples

Example 1: interpreting "the robot solved Rubik's Cube." A precise reconstruction is: a symbolic solver generated a sequence of moves; a recurrent policy, trained in randomized simulation, manipulated the cube to execute those moves; some evaluations relied on modified sensing or stickers; and full-scramble success was limited. This wording preserves the achievement while avoiding the false claim that the robot learned cube-solving search or robust standard-object vision from scratch [2](#source-2).

Example 2: interpreting "OpenAI Five was superhuman." A precise reconstruction is: OpenAI Five beat elite human teams under a constrained hero pool and rule set, with semantic observations and some scripted subsystems. The claim is still important because the environment involved long horizons, teamwork, partial observability, and strategic adaptation. The constraint does not erase the result; it locates it [3](#source-3).

Example 3: interpreting "domain randomization solves sim-to-real." A precise reconstruction is: domain randomization helped transfer by making policies robust to many simulated variations, but transfer still depended on calibrated simulator means, sensor choices, recurrent memory, hardware maintenance, and evaluation conditions. Randomization was an enabling mechanism, not a universal guarantee [1](#source-1) [2](#source-2).

### Common mistakes

Mistake 1: treating early OpenAI as only a prelude to ChatGPT. The robotics and game papers were central to OpenAI's research identity because they made scale, RL, distributed infrastructure, and generality testable in demanding environments [1](#source-1) [2](#source-2) [3](#source-3).

Mistake 2: mistaking public demos for unrestricted task mastery. Dactyl, Rubik's Cube, and OpenAI Five all involved constrained tasks, engineered interfaces, and evaluation caveats. Those caveats are part of the historical lesson, not a reason to ignore the work [1](#source-1) [2](#source-2) [3](#source-3).

Mistake 3: describing PPO or self-play alone as the breakthrough. The papers repeatedly show that algorithms mattered only inside a broader system: simulators, worker fleets, policy surgery, data freshness, reward shaping, hardware repairs, and evaluation design [1](#source-1) [2](#source-2) [3](#source-3).

### Self-check questions

1. What did automatic domain randomization add beyond manually chosen randomization ranges, and why did that matter for Rubik's Cube transfer [2](#source-2)?
2. Which parts of OpenAI Five were learned, and which parts were constrained or scripted [3](#source-3)?
3. Why is "trained entirely in simulation" an incomplete description of the Dactyl result [1](#source-1)?
4. How did early RL infrastructure anticipate later frontier-model training practices [1](#source-1) [3](#source-3) [11](#source-11)?

### Source citations

This opening lecture triangulates OpenAI's early identity through robot-hand manipulation [1](#source-1), cube solving [2](#source-2), large-scale Dota self-play [3](#source-3), and the later GPT-3/GPT-4 language-model turn [4](#source-4) [11](#source-11).

## Lecture 2: Scaling, Pretraining, Data, And Compute

### Learning goals

After this lecture, you should be able to describe GPT-3 as a pivot from task-specific fine-tuning toward in-context task specification; explain why data mixture, benchmark contamination, and compute accounting became central in web-scale language modeling; and place GPT-4 as both a capability milestone and a reporting milestone, because it disclosed broad outcomes while withholding many training details [4](#source-4) [11](#source-11).

### Key terms

Pretraining is broad next-token learning before task-specific adaptation or prompting [4](#source-4). In-context learning is task adaptation inside a prompt without gradient updates to model weights [4](#source-4). Few-shot prompting supplies demonstrations in the context window; zero-shot and one-shot prompting reduce that number to none or one [4](#source-4). Predictable scaling refers to using smaller training runs to forecast larger-run losses or capabilities before the full frontier run is complete [11](#source-11).

### Full explanation

Claim OAI-L2-C1. GPT-3 made a new interface to pretrained models visible. The paper trained a 175-billion-parameter autoregressive language model and evaluated it on many tasks by expressing the task in text, often with examples placed in the context window. The model weights were fixed during evaluation. This made the prompt itself a program-like object: it described the task, supplied demonstrations, and constrained the continuation the model should produce [4](#source-4).

Claim OAI-L2-C2. GPT-3's historical contribution was not simply "bigger is better." It combined scale, broad data, a standardized prompt interface, and a benchmark suite that let researchers compare zero-shot, one-shot, and few-shot settings. The model family spanned multiple sizes, and the largest model used a broad mixture including filtered Common Crawl, WebText-style data, books, and Wikipedia. The result was a clear empirical claim: many in-context behaviors improved with model scale, even when no task-specific gradients were applied [4](#source-4).

Claim OAI-L2-C3. The GPT-3 paper also made evaluation uncertainty part of the story. Web-scale pretraining created benchmark-contamination risks: test examples or near-duplicates could appear in the training data. The authors attempted filtering and clean-subset analysis, but also reported a bug and the practical difficulty of retraining such a large model. That episode is historically important because it showed that, after web-scale pretraining, data provenance and benchmark hygiene were no longer side issues [4](#source-4).

Claim OAI-L2-C4. GPT-3's results were uneven. It performed strongly on some language modeling, question-answering, translation-into-English, synthetic arithmetic, and qualitative generation tasks, but struggled on others, including some natural-language inference, reading-comprehension, and harder symbolic transformations. The paper's own limitations resist the simplified memory that GPT-3 "solved NLP." A better summary is that GPT-3 transformed the research agenda by making general-purpose prompting a serious method while leaving reasoning, reliability, bias, and evaluation limits unresolved [4](#source-4).

Claim OAI-L2-C5. GPT-3 also imported social and economic questions into the main technical report. The paper discussed misinformation, spam, phishing, bias, representation, energy use, and the costs of inference at very large model scale. That matters for a course book because the scaling era did not only create new benchmark curves. It changed who could afford experiments, how release risk was discussed, and how model behavior inherited patterns from broad internet data [4](#source-4).

Claim OAI-L2-C6. GPT-4 continued the scaling trajectory but changed the public evidence style. The report described GPT-4 as a Transformer-style next-token model trained on public and licensed data, then post-trained with RLHF. It reported broad capability, multimodal inputs, predictable scaling, professional-exam performance, MMLU, HumanEval, GSM-8K, multilingual MMLU, visual examples, factuality results, safety evaluations, and system-card risk analysis. At the same time, it withheld architecture, parameter count, training compute, hardware, dataset construction, and many training-method details [11](#source-11).

Claim OAI-L2-C7. The predictable-scaling section of GPT-4 is one of the report's most important technical claims. OpenAI said final loss could be predicted from smaller runs using the same methodology, and it reported a similar forecast for HumanEval pass rate from much smaller compute runs. In frontier-lab practice, this made scaling laws operational: they became tools for deciding whether a full training run was on track, not merely post hoc plots [11](#source-11).

```mermaid
flowchart TB
    A["Pretraining data"] --> B["Next-token LM"]
    B --> C["Scaling probes"]
    C --> D["Forecasts"]
    D --> E["Frontier run"]
    E --> F["Post-training"]
    F --> G["Public report"]
```

The diagram summarizes GPT-4's reported source-specific pattern: broad pretraining and next-token modeling are disclosed at a high level; smaller runs are used to forecast the frontier run; post-training and safety evaluation shape the released system; but the public report mainly exposes outcomes and risk processes rather than a reproducible training recipe [11](#source-11).

### Discussion 2.1

The shift from GPT-3 to GPT-4 is a shift from methodological openness to frontier-lab partial disclosure. GPT-3 gave enough information to understand model sizes, data mixture, prompt formats, benchmark behavior, contamination analysis, and compute order of magnitude. GPT-4 gave much less training detail but much more institutional evidence: predictable-scaling claims, professional and academic exams, visual examples, red-team findings, system-card risk categories, and model-mitigation summaries [4](#source-4) [11](#source-11).

This creates a teaching tension. GPT-4 is a scientific milestone because it expanded measurable capability and multimodal behavior. It is also a documentation milestone because readers must evaluate claims through reported outcomes, safety methodology, and contribution taxonomies rather than full reproducibility. A course history should treat both facts as central [11](#source-11).

### Worked examples

Example 1: few-shot translation. In GPT-3, examples placed in the prompt can establish a translation pattern, and the model continues that pattern without fine-tuning. The result is not proof that the model learned translation from the prompt alone; it may combine pretraining knowledge, task recognition, style adaptation, and local pattern completion [4](#source-4).

Example 2: contamination reasoning. If a benchmark item appears in web-scale pretraining data, performance may reflect memorization or familiarity rather than task generalization. GPT-3's clean-subset analysis was an attempt to estimate the effect, but the paper itself did not claim perfect certainty. The right scholarly posture is to say the authors investigated contamination and found limited apparent effects for many tasks, while preserving remaining uncertainty [4](#source-4).

Example 3: professional exams in GPT-4. The Uniform Bar Exam result became a public signal, but it should be read with the report's appendix details: exam formats, snapshots, prompts, grading procedures, and contamination checks matter. The result is evidence of broad capability under a particular evaluation protocol, not a direct claim that GPT-4 is a human lawyer or student [11](#source-11).

### Common mistakes

Mistake 1: saying GPT-3 introduced instruction following. GPT-3 showed in-context task specification and few-shot prompting, but instruction-following assistants required later post-training methods such as InstructGPT [4](#source-4) [10](#source-10).

Mistake 2: treating GPT-4's withheld details as if they were known. The public report does not verify architecture size, training compute, hardware, or dataset construction. Course prose should not fill those gaps from rumor or inference [11](#source-11).

Mistake 3: reducing scaling to parameter count. The sources show at least four coupled variables: model size, data distribution, compute, and evaluation interface. GPT-3's prompt interface and GPT-4's predictable-scaling discipline are part of the scaling story [4](#source-4) [11](#source-11).

### Self-check questions

1. How does few-shot prompting differ from supervised fine-tuning [4](#source-4)?
2. Why did web-scale data make benchmark contamination a central methodological issue [4](#source-4)?
3. What did GPT-4 disclose about its training, and what did it explicitly withhold [11](#source-11)?
4. Why is predictable scaling operationally important for frontier training runs [11](#source-11)?

### Source citations

The scaling lecture relies on GPT-3 for the pretraining and prompting frame [4](#source-4), InstructGPT for the post-training contrast [10](#source-10), and GPT-4 for later disclosure boundaries around scale and evaluation [11](#source-11).

## Lecture 3: Post-Training, RLHF/RLAIF, Preference Modeling, And Instruction Following

### Learning goals

After this lecture, you should be able to explain why next-token pretraining was not enough for assistant behavior; reconstruct the supervised fine-tuning, reward modeling, and PPO loop used in InstructGPT; distinguish human-feedback alignment from universal alignment; and explain how recursive book summarization connected RLHF to scalable oversight rather than only short chat outputs [9](#source-9) [10](#source-10) [11](#source-11).

### Key terms

Supervised fine-tuning uses human-written demonstrations to teach a pretrained model the desired response style [10](#source-10). Preference modeling trains a reward model from human rankings of alternative outputs [10](#source-10). RLHF uses reinforcement learning to optimize a policy against that learned reward model, often with a KL penalty to keep the policy near a reference model [9](#source-9) [10](#source-10). RLAIF is the related family in which AI-generated judgments or rubrics supplement or replace some human feedback; GPT-4's rule-based reward models are an example of model-assisted reward signals in safety training [11](#source-11).

### Full explanation

Claim OAI-L3-C1. The post-training turn begins from an objective mismatch. GPT-3-style pretraining teaches a model to predict internet text, but an assistant is expected to follow user intent, avoid harmful behavior, be truthful where possible, and format responses usefully. InstructGPT named this mismatch directly and proposed human feedback as a way to move a pretrained model toward helpful, honest, and harmless behavior on an API-like prompt distribution [10](#source-10).

Claim OAI-L3-C2. InstructGPT's method was a three-stage pipeline. First, labelers wrote demonstrations for prompts, and the model was supervised-fine-tuned on those demonstrations. Second, labelers ranked multiple model outputs for a prompt, and those comparisons trained a scalar reward model. Third, the supervised model was optimized with PPO against the reward model, with regularization such as KL penalties and, in the PPO-ptx variant, a mix of pretraining gradients to reduce capability regressions [10](#source-10).

Claim OAI-L3-C3. The data source was as important as the algorithm. InstructGPT used labeler-written prompts to bootstrap early instruction-following behavior, then drew heavily on OpenAI API Playground prompts submitted to earlier instruction models, with filtering, deduplication, and split controls. The datasets were tiny compared with pretraining corpora, but large enough in human-feedback terms to reshape model behavior. This is why the paper became a canonical example of post-training leverage [10](#source-10).

Claim OAI-L3-C4. The headline preference result should be remembered carefully: smaller InstructGPT models could be preferred to much larger raw GPT-3 models on the target prompt distribution, and 175B InstructGPT was strongly preferred to 175B GPT-3. The claim is not that RLHF made a small model universally smarter. It is that human-feedback post-training changed user-facing behavior enough that labelers preferred the aligned model on real-use prompts [10](#source-10).

Claim OAI-L3-C5. Recursive book summarization shows the same feedback family in a different setting: scalable oversight. The problem was that humans cannot cheaply supervise some outputs end to end, such as faithful summaries of entire books or complex domains. The paper decomposed long texts into chunks, summarized leaves, recursively summarized child summaries, and used human demonstrations, comparisons, reward models, and RL to train policies over that tree [9](#source-9).

Claim OAI-L3-C6. The recursive summarization paper is historically valuable because it exposes both the promise and the brittleness of decomposition. The method reduced the human time needed for local judgments and produced plausible full-book summaries, but errors could compound, local chunks could lose globally important themes, and higher-level summaries could inherit mistakes from child summaries. The result was a proof of concept for scalable oversight, not a solved long-context understanding system [9](#source-9).

Claim OAI-L3-C7. InstructGPT also made the governance problem visible. The paper explicitly did not claim alignment with humanity as a whole. It aligned outputs to a feedback process involving labelers, researcher instructions, API users, interface choices, and organizational policy. Labelers were not globally representative, the data was overwhelmingly English, and harmful-instruction refusal behavior remained unresolved. These limits are not peripheral; they define what RLHF meant in this era [10](#source-10).

Claim OAI-L3-C8. GPT-4 extended post-training from assistant preference optimization into layered safety infrastructure. The technical report and system card describe RLHF, expert red teaming, refusal behavior, policy evaluations, and rule-based reward models that use human-written rubrics and model-generated classifications to reward policy-conforming outputs. This is an important bridge from RLHF to RLAIF-like and model-assisted safety systems, while still leaving residual jailbreak, multilingual, calibration, and over-refusal risks [11](#source-11).

### Discussion 3.1

Post-training changed what counted as a model. A GPT-3-style base model was a broad text predictor. InstructGPT showed that a second training layer could transform the same family of pretrained models into instruction followers. GPT-4 then presented frontier systems as products of pretraining plus post-training plus safety evaluation plus deployment policy. The public artifact was no longer just a model weight recipe; it was a whole behavior-shaping pipeline [10](#source-10) [11](#source-11).

This shift also changed the role of human labor. Human-written demonstrations, pairwise rankings, labeler instructions, safety rubrics, and red-team feedback became central training and evaluation resources. The human was not only an evaluator after the fact; human judgment became part of the optimization loop [9](#source-9) [10](#source-10) [11](#source-11).

### Worked examples

Example 1: preference modeling. Suppose a prompt asks for a travel packing list and the model produces four answers. A labeler ranks them by usefulness, safety, and faithfulness to the request. A reward model learns to predict the ranking. PPO then updates the assistant policy toward outputs that the reward model scores higher, while regularization tries to prevent the policy from drifting too far or exploiting reward-model artifacts [10](#source-10).

Example 2: recursive oversight. A full book is too long for a model context window and too costly for each labeler to judge from scratch. The recursive method summarizes chapters or chunks, summarizes those summaries, and finally produces a whole-book summary. This can save human time, but if a crucial motif never appears in any local summary, the final summary cannot recover it [9](#source-9).

Example 3: rule-based reward modeling. In GPT-4 safety training, a model-assisted classifier can judge whether a candidate answer follows a written policy rubric, then supply an additional reward signal. This is not the same as a human directly ranking every answer, and it should be described as a reported model-assisted safety mechanism rather than as proof that the system fully understands policy intent [11](#source-11).

### Common mistakes

Mistake 1: saying RLHF "aligns with humans" without specifying which humans and which process. InstructGPT aligned to labeler preferences, researcher instructions, and API prompt distributions under OpenAI's setup, not to an abstract global consensus [10](#source-10).

Mistake 2: treating reward models as objective truth. Reward models approximate observed preferences and can be overoptimized. KL penalties, PPO-ptx, and evaluation audits exist partly because reward-model optimization can create regressions or artifacts [10](#source-10).

Mistake 3: treating decomposition as guaranteed scalability. Recursive summarization helped supervise long outputs, but fixed decomposition can lose context, compound errors, and fail when global meaning depends on dispersed evidence [9](#source-9).

### Self-check questions

1. What are the three main stages of InstructGPT's RLHF pipeline [10](#source-10)?
2. Why did PPO-ptx mix pretraining gradients into post-training [10](#source-10)?
3. What makes recursive book summarization an alignment paper rather than just a summarization paper [9](#source-9)?
4. How do GPT-4's rule-based reward models change the feedback story [11](#source-11)?

### Source citations

The post-training lecture treats recursive book summarization as a supervision-depth experiment [9](#source-9), InstructGPT as the main instruction-following pipeline [10](#source-10), and GPT-4 as a later report that shows how evaluation and safety framing expanded [11](#source-11).

## Lecture 4: Reasoning, Test-Time Compute, Tool Use, And Agents

### Learning goals

After this lecture, you should be able to explain how the o-series reframed capability as deliberate test-time reasoning; distinguish hidden chain-of-thought, monitoring, and user-visible answers; analyze competitive programming as an evaluation domain for reasoning models; and describe how tool use and agentic scaffolding expanded both capability and risk evaluation [11](#source-11) [13](#source-13) [14](#source-14).

### Key terms

Test-time compute is computation spent during inference, including extended reasoning, sampling, self-checking, tool calls, or candidate selection [13](#source-13) [14](#source-14). Chain of thought is intermediate reasoning; in o1, the system card treats hidden reasoning as safety-relevant while warning that faithfulness and legibility remain open questions [13](#source-13). Tool use means letting a model call external systems such as code execution, web-like tools, chemistry tools, or evaluation harnesses; GPT-4 and competitive-programming sources show tool-mediated reasoning as both useful and risky [11](#source-11) [14](#source-14). Agentic scaffolding wraps a model in prompts, memory, tools, loops, and evaluators to attempt longer tasks [13](#source-13) [14](#source-14).

### Full explanation

Claim OAI-L4-C1. GPT-4 already hinted that frontier models were moving beyond static text completion. The system card included tool-interaction risk examples and evaluations of autonomous replication and resource acquisition, while emphasizing that tested versions were not effective at those tasks under the evaluated conditions. That framing matters: before o1, OpenAI was already treating tool-mediated action and autonomy as safety categories, not merely product features [11](#source-11).

Claim OAI-L4-C2. The o1 system card made deliberate reasoning the center of the model identity. It described the o1 series as trained with large-scale reinforcement learning to reason using chain of thought, "think" before answering, refine strategies, and recognize mistakes. The card used an analogy between faster intuitive responses and slower deliberate reasoning, but course prose should treat that as a model-behavior description, not as literal cognitive equivalence [13](#source-13).

Claim OAI-L4-C3. o1 also changed the safety story. OpenAI argued that reasoning could help the model apply safety policies in context through deliberative alignment. The same reasoning capability also increased the stakes of failures: red-team analysis found that o1 could sometimes give more detailed risky advice, and external evaluations explored scheming-like behaviors under specially crafted conditions. Reasoning improved some measured guardrails while creating new monitoring and governance questions [13](#source-13).

Claim OAI-L4-C4. Hidden chain-of-thought became a governance object. The o1 card described monitoring synthetic o1-preview completions with a GPT-4o deception monitor and categorizing flagged cases such as intentional hallucinations or hallucinated policies. But the card also warned that chain-of-thought faithfulness is unresolved and that external evaluators often saw elicited summaries rather than hidden reasoning. The correct historical claim is that reasoning traces became useful safety artifacts, not that they became transparent windows into the model's mind [13](#source-13).

Claim OAI-L4-C5. Competitive programming supplied a clean but highly structured testbed for reasoning. Problems are objectively graded, require algorithmic insight, and reward self-checking. The OpenAI competitive-programming paper traces a progression from GPT-4o to o1, o1-ioi, and o3. It reports that o1 improved substantially on CodeForces relative to GPT-4o, that o1-ioi added coding-focused RL plus a hand-engineered IOI inference system, and that o3 surpassed the specialized system in reported CodeForces and IOI evaluations with less domain-specific machinery [14](#source-14).

Claim OAI-L4-C6. The o1-ioi system is the clearest worked example of old-style test-time engineering. It split IOI problems into subtasks, sampled many candidate solutions, generated and validated tests, clustered solutions by behavior, used a learned scoring function, and allocated submissions across subtasks. That machinery was powerful but specialized. The paper's later o3 claim is that scaled general-purpose RL produced learned self-verification behaviors, such as writing brute-force checkers, reducing the need for handcrafted contest pipelines [14](#source-14).

```mermaid
flowchart TD
    P["Problem prompt"] --> R["Reasoning model"]
    R --> S["Generate candidate solution"]
    S --> T["Run tests or self-checks"]
    T --> V{"Evidence of failure?"}
    V -- "yes" --> R
    V -- "no" --> A["Submit or answer"]
```

This diagram abstracts the competitive-programming pattern described in the o-series source: generation, checking, revision, and final answer selection become part of inference. The exact proprietary training and scoring details are not fully disclosed, so the diagram should be read as a source-grounded schematic of reported behavior, not a reproduction recipe [14](#source-14).

Claim OAI-L4-C7. The o3 results should be presented with their evaluation assumptions. CodeForces ratings were estimated from simulated contests with full tests and multiple submissions. IOI comparisons include live o1-ioi results, relaxed-submission o1-ioi results, and later retrospective o3 results under official submission limits but with sampling and selection. The numbers are historically significant, yet they are benchmark claims under explicit protocols, not a direct statement that a model competed as a normal human contestant [14](#source-14).

Claim OAI-L4-C8. Agents extend the same logic beyond programming contests. The o1 card reports Preparedness Framework evaluations for cybersecurity, CBRN, persuasion, and model autonomy, including scaffolded tasks and external evaluations. It classified o1 as overall medium risk in the reported framework, with medium CBRN and persuasion and low cybersecurity and autonomy. The key teaching point is the gap between impressive short-horizon reasoning and reliable long-horizon autonomous capability [13](#source-13).

### Discussion 4.1

The reasoning turn did not replace scaling; it redirected scaling toward what happens during inference. GPT-3 asked what a fixed model could infer from examples in a context window. InstructGPT asked how post-training could shape assistant behavior. o1 and o3 asked how reinforcement learning and test-time computation could make models reason, check, revise, and use tools more effectively on hard tasks [4](#source-4) [10](#source-10) [13](#source-13) [14](#source-14).

This also made evaluation harder. A single answer may be the product of hidden reasoning, multiple samples, tool calls, tests, scoring functions, or external scaffolds. Course claims therefore need to specify the inference protocol: one shot, multiple samples, official submission limits, relaxed submissions, full tests, tools, or agent scaffolding. Without that protocol, capability numbers are easy to misread [13](#source-13) [14](#source-14).

### Worked examples

Example 1: self-verification in programming. A reasoning model proposes an optimized algorithm, writes a brute-force solver for small inputs, generates random cases, and compares outputs. If the optimized solution fails, it revises. This behavior is historically important because it moves some verification work into test-time computation, but it still depends on correct test generation and enough inference budget [14](#source-14).

Example 2: chain-of-thought monitoring. A safety monitor scans hidden or summarized reasoning for signs of deception or policy evasion. This may expose useful signals, but the o1 card itself warns that faithfulness is unsettled. Monitoring a trace is therefore a promising method, not proof that the model's actual causal reasoning has been captured [13](#source-13).

Example 3: tool-use risk. GPT-4's system card included a tool-augmented chemistry workflow as a risk example, not as a normal product instruction. The lesson is that tools can turn text reasoning into action-relevant workflows. Evaluating a model without tools may understate risk; evaluating tool-augmented systems requires careful scope, safeguards, and context [11](#source-11).

### Common mistakes

Mistake 1: equating hidden chain of thought with faithful introspection. The o1 card treats faithfulness as an open question and distinguishes hidden reasoning, summaries, monitoring, and final answers [13](#source-13).

Mistake 2: collapsing o1-ioi, o1, and o3 into one system. The competitive-programming paper describes different models, training emphases, inference pipelines, submission limits, and evaluation protocols. Those distinctions carry the historical claim [14](#source-14).

Mistake 3: saying test-time compute means single-shot intelligence. The reported gains often involve sampling, selection, checking, tool execution, or scaffolding. Less hand engineering is not the same as no inference-time machinery [14](#source-14).

### Self-check questions

1. What does the o1 system card claim about large-scale RL and chain-of-thought reasoning [13](#source-13)?
2. Why is chain-of-thought monitoring promising but epistemically uncertain [13](#source-13)?
3. What was specialized about o1-ioi's inference pipeline [14](#source-14)?
4. Why should CodeForces and IOI numbers be reported together with their submission and sampling protocols [14](#source-14)?

### Source citations

Reasoning is built here from few-shot prompting [4](#source-4), instruction-following post-training [10](#source-10), broad GPT-4 evaluations [11](#source-11), the o1 system-card framing [13](#source-13), and a competitive-programming case study [14](#source-14).

## Lecture 5: Multimodality, Speech, Vision, Robotics, And Embodied Work

### Learning goals

By the end of this lecture, students should be able to explain why OpenAI's multimodal work was not a single line of "add images to language models," but a set of translations of the scaling recipe into vision, image generation, speech, and embodied control; distinguish CLIP's contrastive alignment from DALL-E's autoregressive generation and DALL-E 2's CLIP-latent diffusion; describe Whisper as a weak-supervision and task-token speech system rather than an architecture breakthrough; and state why robotics demonstrations depended on simulation, randomization, recurrent adaptation, and hardware constraints rather than general physical intelligence [1](#source-1) [2](#source-2) [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8).

### Key terms

Natural-language supervision means using image captions, transcripts, prompts, or other human text as the supervision channel rather than only fixed class labels. Contrastive learning trains paired modalities to be close in an embedding space and unpaired examples to be far apart. Dynamic classifier synthesis is CLIP's trick of turning class names or prompts into classifier weights through a text encoder. Domain randomization trains policies over a distribution of simulated worlds so that real-world imperfections look like another sampled environment. Task tokens are special tokens that tell one model whether it should transcribe, translate, timestamp, or perform another speech task [1](#source-1) [5](#source-5) [8](#source-8).

### Full explanation

Claim OAI-L5-C1. CLIP is the hinge that made OpenAI's later multimodal story coherent. Its core move was to replace a fixed visual label set with internet-scale image-text pairs and a contrastive objective: image and text encoders learn a shared space in which true pairs are close and mismatched pairs are distant. At inference time, a downstream visual task becomes a language task: write candidate labels as prompts, embed them, and compare them with the image embedding. This is why CLIP should be taught not only as a zero-shot ImageNet result, but as a new interface for vision: the label space is supplied by natural language at use time [5](#source-5).

```mermaid
flowchart TB
  A["Image-text pairs"] --> B["CLIP training"]
  B --> C["Shared space"]
  C --> D["Zero-shot prompts"]
  C --> E["DALL-E rerank"]
  C --> F["DALL-E 2 latent"]
```

Claim OAI-L5-C2. The same CLIP mechanism also created governance problems. Prompt templates and class sets were performance levers, but the paper's own broader-impact analysis shows they were also harm levers: harmful labels, FairFace probes, surveillance-like use cases, and sensitivity to whether labels such as "child" were included all demonstrate that the output categories chosen by developers can change both accuracy and social risk. CLIP's flexibility is therefore the lesson and the warning: a model that can classify almost anything users name also makes naming itself a deployment decision [5](#source-5).

Claim OAI-L5-C3. DALL-E 1 translated the GPT-style autoregressive recipe into image generation by first tokenizing images with a discrete VAE, then modeling text tokens and image tokens as one long sequence with a 12-billion-parameter transformer trained on roughly 250 million image-text pairs. The result was historically important because it reduced text-to-image generation to next-token prediction over a joint text-image stream, but the visual tokenizer was lossy and the reported samples relied on CLIP-like contrastive reranking, often best-of-many rather than a single raw draw [6](#source-6).

Claim OAI-L5-C4. DALL-E 2 changed the abstraction again. Instead of directly producing image tokens from text, unCLIP first predicts a CLIP image embedding from a caption and then decodes that embedding into pixels using diffusion. This separation made image variation, interpolation, and text-diff manipulation natural consequences of the representation, but it also exposed what CLIP latents leave out: precise spelling, reliable attribute binding, and fine detail in complex scenes. The model's strength and its failure modes came from the same bottleneck [7](#source-7).

Claim OAI-L5-C5. Whisper is the speech analogue of this foundation-model pattern. Its architecture is a fairly standard encoder-decoder Transformer over log-Mel spectrograms; the intervention is scale, weak supervision, and task formatting. Training on 680,000 hours of multilingual and multitask audio supervision, including English transcription, non-English transcription, and translation, let one model use decoder task tokens for language identification, no-speech detection, transcription, translation, and timestamping. Robustness came from broad data and unified formatting more than from a novel speech network [8](#source-8).

Claim OAI-L5-C6. Whisper also shows why weak supervision is not free supervision. The paper reports filtering machine-generated transcripts, language mismatches, duplicated text, and bad sources, and it still documents language imbalance, transcript-quality pathologies, text-normalization sensitivity, and long-form hallucination or repetition failures. The correct historical lesson is not that internet transcripts automatically solve ASR, but that large weakly supervised corpora can produce robust zero-shot systems when paired with curation, task tokens, and careful evaluation [8](#source-8).

Claim OAI-L5-C7. OpenAI's robotics work took a very different route to "multimodal" capability. Learning Dexterous In-Hand Manipulation trained a recurrent policy entirely in randomized simulation, then transferred it to a Shadow hand manipulating a block. The system did not learn from human demonstrations; it learned from PPO, domain-randomized MuJoCo/Unity simulations, asymmetric actor-critic training, and a separate synthetic-trained vision estimator. The measured success depended on sensors, calibration, randomization ranges, recurrent memory, and large distributed rollout infrastructure [1](#source-1).

Claim OAI-L5-C8. Solving Rubik's Cube with a Robot Hand extended that logic with automatic domain randomization. The system did not learn the abstract cube-solving algorithm; a conventional solver generated subgoals, and the learned controller executed rotations and flips. ADR expanded or contracted simulator parameter ranges based on boundary performance, creating a curriculum over worlds. The impressive demonstration still used modified sensing setups, restricted protocols, and nontrivial failure rates, so it should be treated as a milestone in sim-to-real dexterous manipulation, not unconstrained general robotics [2](#source-2).

Claim OAI-L5-C9. These multimodal and embodied systems share a deeper pattern: OpenAI repeatedly converted messy real-world domains into scalable training interfaces. CLIP uses text as a flexible classifier language; DALL-E uses visual tokens and CLIP selection; DALL-E 2 uses CLIP latents and diffusion; Whisper uses task tokens over transcripts; robotics uses randomized simulators as data generators. In each case, the interface made scaling tractable, and in each case the interface also defined the boundary of what the system could not faithfully represent [1](#source-1) [2](#source-2) [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8).

### Discussion 5.1

Suppose a lab wants one model family that can see, hear, speak, and act. CLIP suggests a shared representation strategy; Whisper suggests task-token unification; DALL-E 2 suggests a latent bottleneck for generation; robotics suggests environment generation and online adaptation. The discussion question is whether these are converging on one architecture or merely one research style: define a common interface, scale weak or synthetic supervision, then evaluate broad transfer and failure modes [1](#source-1) [5](#source-5) [7](#source-7) [8](#source-8).

### Worked examples

A CLIP-style zero-shot classifier for animal species does not require retraining the image encoder. The developer writes prompts such as "a photo of a tabby cat" or "a photo of a border collie," embeds those strings, embeds the image, and chooses the nearest text embedding. If the prompt set includes harmful, ambiguous, or socially loaded categories, the model will still return some result, which is why prompt and label design belong in both engineering review and safety review [5](#source-5).

A DALL-E 2 variation workflow begins from an image, encodes it into a CLIP image embedding, and decodes from that semantic/style representation through diffusion. The output may preserve subject, pose, and broad style while changing surface details. That is useful for creative variation, but it also explains why exact text rendering or object-attribute binding can fail: the intermediate representation was not designed to preserve every symbolic or relational detail [7](#source-7).

A robot-hand policy trained with domain randomization can be read as doing implicit system identification. If the object is heavier, friction differs, or a joint responds slowly, a recurrent policy can infer those hidden facts from interaction history and adjust. The Rubik's Cube and dexterous-hand papers both show that recurrence and randomized training distributions are central to transfer; without randomization, policies that succeed in simulation can fail sharply on hardware [1](#source-1) [2](#source-2).

### Common mistakes

The first mistake is to treat CLIP as just an ImageNet score. Its more important contribution is that language became an interface for specifying visual tasks, with all the power and risk that implies. The second mistake is to describe DALL-E 2 as "just diffusion"; its distinctive public paper mechanism is CLIP-latent generation plus diffusion decoding. The third mistake is to say Whisper solved speech by architecture; the paper's own framing emphasizes scale, weak supervision, and zero-shot robustness. The fourth mistake is to present the robot hand demos as general physical intelligence rather than carefully engineered sim-to-real systems [1](#source-1) [2](#source-2) [5](#source-5) [7](#source-7) [8](#source-8).

### Self-check questions

1. How does CLIP turn a class name into part of a classifier, and why does that make class design a governance surface [5](#source-5)?
2. What did DALL-E 1 gain and lose by compressing images into discrete tokens before autoregressive modeling [6](#source-6)?
3. Why does DALL-E 2's CLIP-latent bottleneck help variation while hurting spelling and binding [7](#source-7)?
4. What makes Whisper a weak-supervision scaling result rather than a novel-ASR-architecture result [8](#source-8)?
5. Why were domain randomization and recurrent memory essential to the robot hand results [1](#source-1) [2](#source-2)?

### Source citations

This multimodality lecture combines embodied robotics sources [1](#source-1) [2](#source-2), CLIP's language-supervised visual representation work [5](#source-5), the two DALL-E generations [6](#source-6) [7](#source-7), and Whisper's weakly supervised speech-recognition study [8](#source-8).

## Lecture 6: Interpretability And Model Internals

### Learning goals

By the end of this lecture, students should be able to separate behavioral transparency, architectural disclosure, and mechanistic interpretability; explain why GPT-3 made in-context learning visible without explaining its internal algorithm; describe how CLIP, GPT-4, o1, and gpt-oss expose different kinds of internal or quasi-internal evidence; and state the residual gap in the local OpenAI source set: there is no selected OpenAI major paper here that plays the role of a dedicated mechanistic-interpretability or circuit-analysis paper [4](#source-4) [5](#source-5) [11](#source-11) [13](#source-13) [15](#source-15) [16](#source-16) [17](#source-17).

### Key terms

Behavioral interpretability explains a model through observed input-output patterns, benchmark slices, failures, calibration, or refusal behavior. Architectural transparency discloses components such as encoders, decoders, attention patterns, mixture-of-experts layers, or context length. Mechanistic interpretability seeks causal explanations inside the model, such as circuits, features, activations, or algorithms implemented by subnetworks. Chain-of-thought monitoring treats intermediate reasoning text as an audit object, while preserving the caveat that a reasoning trace may not faithfully reveal the underlying computation [11](#source-11) [13](#source-13) [15](#source-15).

### Full explanation

Claim OAI-L6-C1. OpenAI's selected source set is rich in model behavior and relatively thin in local mechanistic interpretability. GPT-3, CLIP, InstructGPT, GPT-4, o1, and gpt-oss all give ways to inspect what models do, how they are trained or post-trained, and where they fail. But the citation registry and local discovery artifacts support treating interpretability-specific OpenAI major papers as a residual gap rather than silently importing a circuits literature that is not in this OpenAI registry [4](#source-4) [10](#source-10) [11](#source-11) [16](#source-16) [17](#source-17).

Claim OAI-L6-C2. GPT-3 is the clearest example of a behavior becoming historically central before its mechanism was understood. The paper made few-shot and in-context prompting a public phenomenon: a fixed-weight autoregressive model could adapt to tasks from demonstrations in the prompt. But it explicitly left open whether this behavior reflected task recognition, style adaptation, memorized patterns, de novo learning in context, or a mixture that varied by task. The model internal algorithm remained unresolved in the paper that popularized the behavior [4](#source-4).

Claim OAI-L6-C3. CLIP provides more structural visibility, but still not mechanistic interpretability in the circuit sense. We can inspect the training objective, the paired image-text embedding space, prompt sensitivity, zero-shot classifier construction, linear probes, retrieval behavior, and bias probes. Those are strong handles for interpreting model use and failure. They do not, by themselves, explain the internal features or circuits by which a vision transformer or ResNet branch binds visual concepts to text [5](#source-5).

Claim OAI-L6-C4. DALL-E 2 shows how an intermediate representation can be interpretable at the system level while opaque at the mechanism level. CLIP image embeddings are meaningful enough that interpolation, image variation, and text-diff operations can manipulate outputs in recognizable ways. Yet the same paper's failures on spelling, binding, and complex scene detail show that "semantic latent" does not mean "fully understood representation." A latent can be useful, controllable, and still not transparent about all information it preserves or discards [7](#source-7).

Claim OAI-L6-C5. GPT-4 marked a documentation turning point. It reported that GPT-4 was Transformer-based, next-token trained, post-trained with RLHF-like methods, and capable across text and image inputs, but it withheld architecture, size, compute, dataset construction, and many training details. This makes GPT-4 highly interpretable as a public capability and safety artifact, but only weakly interpretable as a reproducible model-internals artifact. Students should notice that the report explains outcomes and processes more than internal implementation [11](#source-11).

Claim OAI-L6-C6. Predictable scaling in GPT-4 is a form of internal discipline, not mechanistic explanation. OpenAI reports that final loss and HumanEval performance were predicted from smaller runs using the same methodology. That tells us the training process was sufficiently regular for operational forecasting, and it matters for planning large expensive runs. It does not tell us which circuits implement reasoning, why a particular hallucination occurs, or how a model stores a domain fact [11](#source-11).

Claim OAI-L6-C7. o1 introduced chain-of-thought as a governance-relevant internal artifact. The system card frames o1 as trained with large-scale reinforcement learning to reason before answering, and it discusses chain-of-thought monitoring for deception-like categories. But the card is careful: chain-of-thought is useful for monitoring only if it is faithful, and that faithfulness is an open research question. This is the interpretability tension of reasoning models: traces are more legible than activations, but not automatically truthful explanations [13](#source-13).

Claim OAI-L6-C8. gpt-oss pushes this tension further because it offers open weights, full chain-of-thought access, and a protocol with role hierarchy, channels, and tool calls. That makes it more inspectable than a closed API-only system in some respects: researchers and deployers can inspect weights, reasoning traces, and tool transcripts. Yet the model card warns that raw chain-of-thought may contain hallucinated or policy-inconsistent content and should not be shown directly to users without filtering or summarization. Access is not the same thing as reliable explanation [15](#source-15).

Claim OAI-L6-C9. InstructGPT and recursive book summarization belong in this lecture because they make reward models into behavioral mirrors of human judgment. Reward models, labeler comparisons, Likert ratings, and preference win rates reveal what a training pipeline selected for. They do not expose the internal causal mechanism of the resulting policy. This distinction matters: alignment telemetry is evidence about objectives and outcomes, not a microscope for the model's learned algorithms [9](#source-9) [10](#source-10).

Claim OAI-L6-C10. The residual gap should be stated plainly. In this OpenAI course-book source set, the local evidence supports lessons about behavioral evaluation, representation interfaces, scaling prediction, chain-of-thought monitoring, and open-weight protocol inspection. It does not support a lecture that claims OpenAI's selected public corpus contains a major local mechanistic-interpretability paper comparable to dedicated circuit-analysis work. That absence is itself part of the historical record students should learn to preserve [16](#source-16) [17](#source-17).

### Discussion 6.1

Should chain-of-thought be treated as interpretability? One side says yes: it is a model-produced artifact that can reveal planning, uncertainty, policy reasoning, or deception-like behavior. The other side says not yet: if the trace is optimized, summarized, hidden, or unfaithful, it may be a post hoc narrative rather than a causal account. The OpenAI o1 and gpt-oss cards are valuable because they do not fully resolve this tension; they document it as an active design and safety problem [13](#source-13) [15](#source-15).

### Worked examples

A GPT-3 prompt that gives three translation examples and asks for a fourth may succeed for several possible reasons. The model might recognize a translation task seen during pretraining, infer a format, copy local syntax, or perform a more general in-context algorithm. The paper's evaluations show the phenomenon, but a mechanistic account would require additional causal tools not supplied by the GPT-3 report [4](#source-4).

A CLIP embedding nearest-neighbor search can reveal that images and phrases occupy a shared semantic space. If "a photo of a dog" and a dog image are close, the system-level interpretation is straightforward. But the embedding alone does not say which neurons or attention heads encode ears, fur, text co-occurrence, or dataset artifacts. Behavioral and representation-level interpretation remain short of mechanistic explanation [5](#source-5).

An o1 chain-of-thought monitor might flag a trace that appears to rationalize a false answer or mention policy evasion. That is useful safety evidence. Yet if the model's hidden reasoning and the surfaced summary diverge, or if a model learns to make its trace look harmless, the monitor can understate risk. The card's own caveats make this a worked example in preserving uncertainty [13](#source-13).

### Common mistakes

One mistake is to equate withheld details with absence of science: GPT-4 still reports meaningful scaling, benchmark, and safety evidence, even though it is not reproducible from the paper. A second mistake is to equate visible reasoning with faithful reasoning: chain-of-thought can help monitoring without being a guaranteed transcript of computation. A third mistake is to use CLIP's neat embedding diagrams as if they explained all internal features. A fourth mistake is to ignore the registry gap and write an OpenAI interpretability lecture as if a local mechanistic paper had been read when it had not [5](#source-5) [11](#source-11) [13](#source-13) [16](#source-16).

### Self-check questions

1. What did GPT-3 demonstrate about in-context learning, and what did it leave unexplained [4](#source-4)?
2. Why is a CLIP embedding space interpretable at one level but not a full circuit-level explanation [5](#source-5)?
3. How did GPT-4's public report trade reproducibility detail for capability, scaling, and safety evidence [11](#source-11)?
4. Why does o1's chain-of-thought monitoring depend on the unresolved question of faithfulness [13](#source-13)?
5. What exactly is the residual interpretability gap in this local OpenAI source set [16](#source-16) [17](#source-17)?

### Source citations

The internals lecture uses capability-facing sources as indirect evidence: GPT-3 and CLIP for representation behavior [4](#source-4) [5](#source-5), DALL-E 2 for latent-structure design [7](#source-7), feedback papers for behavioral shaping [9](#source-9) [10](#source-10), system cards for evaluation boundaries [11](#source-11) [13](#source-13) [15](#source-15), and sitemap artifacts for the interpretability-gap note [16](#source-16) [17](#source-17).

## Lecture 7: Safety, Alignment, Governance, Evaluations, And System Cards

### Learning goals

By the end of this lecture, students should be able to trace OpenAI's public alignment path from human-feedback training and scalable oversight to GPT-4-era system cards; explain why "aligned with human feedback" always means aligned through a specific feedback pipeline; compare GPT-4, GPT-4o, o1, and gpt-oss safety documentation; and describe how red teaming, refusal behavior, Preparedness Framework categories, chain-of-thought monitoring, and open-weight adversarial fine-tuning became parts of release governance [9](#source-9) [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Key terms

RLHF is a post-training pipeline that uses demonstrations, preference comparisons, reward models, and reinforcement learning to steer behavior. Scalable oversight decomposes hard tasks into easier subtasks so humans can supervise work they could not directly judge at full scale. A system card documents a deployed system's capabilities, limitations, mitigations, and risk process. A Preparedness Framework score classifies frontier-model risk in categories such as cyber, biological or chemical threats, persuasion, and autonomy. Deliberative alignment trains a model to reason about safety policies in context rather than merely imitate refusals [9](#source-9) [10](#source-10) [12](#source-12) [13](#source-13).

### Full explanation

Claim OAI-L7-C1. The early OpenAI alignment story in this source set begins with a simple but powerful observation: next-token prediction on internet text is not the same objective as following user instructions helpfully, truthfully, and safely. InstructGPT operationalized that diagnosis through supervised fine-tuning on demonstrations, reward modeling from ranked completions, and PPO against the reward model, with KL and pretraining-mix regularization to preserve capabilities. Its headline result was not only that the model became more pleasant; smaller instruction-tuned models could be preferred to much larger raw GPT-3 models on real API-like prompts [10](#source-10).

Claim OAI-L7-C2. But InstructGPT also states the alignment problem more carefully than many summaries do. The system was aligned to a particular group of labelers, researcher instructions, API customer prompts, and deployment choices. The labelers were not a democratic stand-in for all affected people, and the paper explicitly asks whose preferences should matter. This is a foundational governance point: RLHF is a sociotechnical feedback pipeline, not a direct measurement of universal human values [10](#source-10).

Claim OAI-L7-C3. Recursive book summarization moved from short assistant outputs toward scalable oversight. The system chunks long books, summarizes leaves, recursively summarizes child summaries, and uses human demonstrations and comparisons at manageable nodes. This made supervision cheaper than reading and summarizing a full book directly, but it also introduced context loss, compounding lower-level errors, and brittle curricula. The paper is best read as a proof of concept for decomposed oversight, not as evidence that recursive decomposition solves hard supervision [9](#source-9).

```mermaid
flowchart TD
  A["Hard task: whole-book or frontier-model behavior"] --> B["Decompose into smaller tasks"]
  B --> C["Human demonstrations or comparisons"]
  C --> D["Reward model / policy update"]
  D --> E["System behavior"]
  E --> F["Evaluation, red teaming, and system card"]
  F --> B
```

Claim OAI-L7-C4. GPT-4 turned safety documentation into a central public artifact. The report contains benchmark results and scaling prediction, but its appended system card is equally important: it catalogs hallucinations, harmful content, representation harms, disinformation, proliferation, privacy, cybersecurity, emergent behavior, tool interaction risks, economic impacts, acceleration, and overreliance. It also documents expert red teaming, additional safety data, refusals, rule-based reward models, and residual jailbreak risk [11](#source-11).

Claim OAI-L7-C5. GPT-4's safety evidence should be read as layered mitigation, not proof of solved safety. The report says mitigations reduce but do not eliminate failures; examples in the system card are illustrative rather than prevalence estimates; red teaming was not globally representative; and safety evaluations were mostly English and US-centric. This is why the GPT-4 system card is a governance milestone: it records both measured improvements and the remaining difficulty of measuring context-dependent harms [11](#source-11).

Claim OAI-L7-C6. GPT-4o changed the risk surface by adding real-time speech-to-speech and broader multimodal interaction. Its system card describes an autoregressive omni model trained end-to-end across text, vision, and audio, with low-latency audio responses. That changed safety questions from "what text does the model output?" to "what voice can it produce, whom might it identify, what can it infer from accent or speech, how persuasive is spoken interaction, and how does emotional reliance change when the model responds like a person?" [12](#source-12).

Claim OAI-L7-C7. GPT-4o also shows how evaluation methods lag modalities. Many speech evaluations were converted from text to audio using TTS, then scored through text transcripts. The card explicitly warns that this misses intonation, affect, background noise, cross-talk, acoustic artifacts, and other real-use conditions. The method is useful because it lets existing safety evals reach audio quickly, but the limitation is central: modality-native safety requires modality-native measurement [12](#source-12).

Claim OAI-L7-C8. o1 shifted alignment toward reasoning models. The system card says the o1 series is trained with large-scale reinforcement learning to reason using chain of thought, and it introduces deliberative alignment: the model reasons through safety policies in context. This improved some refusal and jailbreak measures, but the card also notes that more detailed reasoning can make failures more consequential when guardrails fail. Reasoning is both a safety affordance and a new risk amplifier [13](#source-13).

Claim OAI-L7-C9. o1's chain-of-thought discussion is one of the most important governance developments in the corpus. OpenAI treats chain-of-thought as a possible monitoring object and reports a deception-monitoring experiment, but also says faithfulness is unresolved. External evaluators did not always have access to hidden chain-of-thought and sometimes used elicited summaries instead. The safety lesson is precise: reasoning traces may help audits, but they are not guaranteed windows into model cognition [13](#source-13).

Claim OAI-L7-C10. gpt-oss changed the release-governance problem because weights are open. A centralized API system can add server-side mitigations, monitor use, and revoke access; an open-weight model can be fine-tuned, hosted, or modified downstream. The model card therefore evaluates not only default behavior but also adversarially fine-tuned variants in biological/chemical and cyber risk settings, simulating stronger post-release attackers. Open-weight release makes downstream governance part of the model's safety case [15](#source-15).

### Discussion 7.1

Which safety artifact should a public release require: a technical report, a system card, a model card, or all three? GPT-4's system card fits a centrally served product, GPT-4o's system card fits a multimodal assistant with voice and affective risks, o1's card fits a reasoning model with chain-of-thought monitoring questions, and gpt-oss's model card fits open weights whose downstream deployments cannot be centrally controlled. The artifact form follows the release form [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Worked examples

Consider a harmful chemistry request. In an InstructGPT-style pipeline, labelers and reward models shape whether the assistant refuses or redirects. In GPT-4, expert red teaming and rule-based reward models add targeted mitigation. In o1, the model may reason through policy before answering. In gpt-oss, a downstream actor might fine-tune away refusals, so the release evaluation must ask what capability remains after adversarial modification. The same request therefore requires different governance assumptions across model generations [10](#source-10) [11](#source-11) [13](#source-13) [15](#source-15).

Consider a voice assistant asked, "Who is speaking?" GPT-4o treats speaker identification as a speech-specific safety category, not just a general question-answering issue. The mitigation is not only a text refusal rule; it includes training behavior, product constraints, voice-output classifiers, and evaluation across languages and voice settings. This illustrates why multimodal safety cannot be reduced to text moderation [12](#source-12).

Consider a long book summary. Recursive summarization lets humans supervise local pieces instead of reading the whole book, then trains a model to assemble higher-level summaries. The benefit is lower supervision cost; the risk is that an early local error may propagate and a global theme may never appear in any local summary. This is the general scalable-oversight dilemma in miniature [9](#source-9).

### Common mistakes

The first mistake is to say RLHF aligns models with "human values" without naming the feedback pipeline. The second is to read a system card as a certificate of safety rather than a structured disclosure of evidence, mitigations, and uncertainty. The third is to assume better reasoning always means safer reasoning; o1 shows that policy reasoning can improve some metrics while making certain failures more detailed. The fourth is to treat open-weight and API-served releases as the same governance problem; gpt-oss shows why they are not [10](#source-10) [11](#source-11) [13](#source-13) [15](#source-15).

### Self-check questions

1. Why is InstructGPT alignment better described as alignment to a feedback pipeline than alignment to humanity [10](#source-10)?
2. What does recursive summarization teach about scalable oversight and context loss [9](#source-9)?
3. How did GPT-4 system-card documentation differ from earlier model papers [11](#source-11)?
4. Why did GPT-4o require speech-specific safety categories and evaluation caveats [12](#source-12)?
5. Why does open-weight release require adversarial fine-tuning evaluation [15](#source-15)?

### Source citations

This safety lecture follows the transition from human-feedback research [9](#source-9) [10](#source-10) to public evaluation and risk artifacts in GPT-4, GPT-4o, o1, and gpt-oss documentation [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

## Lecture 8: Benchmarking, Measurement, Red Teaming, And Capability Forecasting

### Learning goals

By the end of this lecture, students should be able to explain why OpenAI's benchmark history is a history of measurement design, not just score improvement; compare GPT-3 broad prompting benchmarks, CLIP zero-shot transfer, Whisper robustness, GPT-4 predictable scaling, GPT-4o and o1 Preparedness evaluations, and o-series competitive-programming evaluations; and identify contamination, proxy metrics, model snapshots, test-time compute, red-team sampling, and modality mismatch as recurring measurement hazards [4](#source-4) [5](#source-5) [8](#source-8) [11](#source-11) [12](#source-12) [13](#source-13) [14](#source-14).

### Key terms

Zero-shot evaluation tests a model without task-specific gradient updates or examples beyond a prompt. Contamination analysis asks whether benchmark examples or near-duplicates appeared in training data. Effective robustness compares performance outside the narrow training or benchmark distribution. Forecasting uses smaller runs, scaling trends, or held-out tasks to predict larger-run behavior. Red teaming deliberately searches for failures, misuse paths, or policy violations. Test-time compute is computation spent during inference through sampling, reasoning, tool use, or verification [4](#source-4) [8](#source-8) [11](#source-11) [14](#source-14).

### Full explanation

Claim OAI-L8-C1. GPT-3 made broad benchmark portfolios central to public model evaluation. The paper evaluated zero-shot, one-shot, and few-shot prompting across language tasks, synthetic tasks, closed-book QA, translation, arithmetic, and more. The methodological contribution was not merely a 175B-parameter model; it was a standardized way to ask whether one fixed model could adapt from text prompts without fine-tuning. The limitation was equally important: in-context learning was measured as a behavior, while its mechanism and contamination boundaries remained uncertain [4](#source-4).

Claim OAI-L8-C2. CLIP moved measurement into vision by asking whether a single image-text model could transfer across many datasets through natural-language prompts. The results were broad and striking, but the paper itself notes that the 27-dataset suite was assembled during development, prompt engineering and ensembling affected scores, and zero-shot CLIP was weak on specialized, abstract, counting, and fine-grained tasks. This is a recurring benchmark lesson: a model can redefine the evaluation surface while also co-adapting to it [5](#source-5).

Claim OAI-L8-C3. DALL-E and DALL-E 2 show how generative-image measurement depends on selection and proxy loops. DALL-E 1 used contrastive reranking of many candidates; DALL-E 2 used human pairwise evaluations, MS-COCO FID, guidance sweeps, and CLIP-based aesthetic or comparison proxies. These are not invalid methods, but they remind us that "image quality" is constructed from sampling budget, selection model, human preference protocol, diversity metric, and benchmark dataset [6](#source-6) [7](#source-7).

Claim OAI-L8-C4. Whisper made robustness the measurement target. Instead of optimizing only for in-distribution speech benchmarks, the paper compared zero-shot performance across many datasets, languages, noise conditions, and long-form transcription settings. It also shows how fragile speech metrics can be: text normalization can sharply change WER, weak-supervision metadata errors can affect language buckets, and long-form decoding needs heuristics. Robustness measurement is itself a modeling choice [8](#source-8).

Claim OAI-L8-C5. GPT-4's most important measurement contribution may be predictable scaling. The report says final loss and HumanEval performance were predicted from smaller models trained with the same methodology before the final run completed. This shifted scaling laws from retrospective explanation to operational forecasting: large training runs, safety preparation, and deployment planning could be informed by smaller-run extrapolations. But forecasting a benchmark score is not the same as forecasting all deployment behavior [11](#source-11).

Claim OAI-L8-C6. GPT-4 also illustrates benchmark triangulation. The report combines professional exams, academic benchmarks, multilingual MMLU, visual examples, user preference evaluations, factuality tests, calibration, red teaming, and safety refusal metrics. Each has caveats: exam snapshots, grading choices, translation artifacts, contamination checks with false-positive and false-negative risk, and post-training effects such as improved TruthfulQA but worsened calibration. The measurement lesson is to compare many imperfect instruments rather than trust one score [11](#source-11).

Claim OAI-L8-C7. GPT-4o and o1 formalized dangerous-capability measurement through Preparedness Framework categories. GPT-4o reports cyber, biological, persuasion, and autonomy assessments, with overall medium risk because persuasion crossed a medium threshold while other categories were low. o1 reports medium CBRN and persuasion risk, low cyber and autonomy, and extensive caveats that scaffolding, elicitation, longer rollouts, or future updates could change results. Preparedness scores are release gates under uncertainty, not timeless facts about a model family [12](#source-12) [13](#source-13).

Claim OAI-L8-C8. Red teaming is not a single benchmark; it is a search process. GPT-4 used more than 50 experts across safety-relevant domains; GPT-4o used more than 100 external red teamers across 45 languages and 29 countries; o1 included external red teams and specialized evaluations around scheming, cybersecurity, AI R&D, and policy violations. The point is coverage, stress, and discovery, not representative prevalence. Red-team examples should be read as evidence that a failure type can be elicited, not as population rates [11](#source-11) [12](#source-12) [13](#source-13).

Claim OAI-L8-C9. Competitive programming made test-time compute visible as a measurement variable. The o1 and o3 coding paper compares gpt-4o, o1-preview, o1, o1-ioi, and o3 on CodeForces and IOI-style tasks. o1-ioi used specialized inference machinery: thousands of samples, subtask splitting, generated tests, clustering, reranking, and submission allocation. o3 is reported to surpass that specialized system with more general RL-trained reasoning and self-verification, but still uses substantial sampling and selection. "Solved" must therefore be read alongside submission limits, sample counts, ranking assumptions, and compute budgets [14](#source-14).

Claim OAI-L8-C10. gpt-oss adds another measurement frontier: open-weight release risk. The model card evaluates default safety behavior and adversarially fine-tuned variants, with external recommendations incorporated into the process. This is a different kind of benchmark because the evaluator must imagine what capable downstream actors can do after weights leave centralized control. Measurement shifts from "what does the served model do today?" to "what could modified descendants do under plausible adversarial effort?" [15](#source-15).

### Discussion 8.1

Which score would you trust most: GPT-4's bar exam percentile, CLIP zero-shot ImageNet, Whisper effective robustness, GPT-4o Preparedness scores, or o3 CodeForces rating? A careful answer should not pick a universal winner. Each score answers a different question under different assumptions about contamination, prompting, sampling, grading, human comparison, modality, and deployment context [5](#source-5) [8](#source-8) [11](#source-11) [12](#source-12) [14](#source-14).

### Worked examples

The GPT-4 bar exam result is historically salient because it made frontier capability legible to the public. But the technical report's methodology matters: exams used particular snapshots, public or purchased study materials, contamination filtering, and scoring procedures that only approximate human test-taking. The right use of the result is not "GPT-4 is a lawyer," but "a general model reached high performance on a standardized professional exam under a documented simulation" [11](#source-11).

The o3 CodeForces result is similar. A 2724 estimated rating is a powerful signal, but it is based on a contest simulation with full test suites, multiple independent submissions, parallel sampling assumptions, and a likelihood-based conversion from score to rating. That does not erase the achievement; it tells students exactly what kind of achievement it is [14](#source-14).

The GPT-4o speech evaluation workflow converts text safety datasets into audio through TTS, then often scores text transcripts. This is a practical bridge, but it can miss acoustic artifacts, emotion, background noise, cross-talk, and real speaker variation. A measurement can be useful and incomplete at the same time [12](#source-12).

### Common mistakes

The first mistake is leaderboard literalism: treating benchmark numbers as direct measures of intelligence, safety, or deployment reliability. The second is contamination complacency: accepting "checked for overlap" as if it fully solved leakage. The third is hiding inference compute: comparing one-shot human reasoning with thousands of model samples or verifier passes without naming the difference. The fourth is red-team overgeneralization: treating elicited failures as rates or treating absence of elicited failures as proof of absence [4](#source-4) [11](#source-11) [13](#source-13) [14](#source-14).

### Self-check questions

1. Why did GPT-3's prompt-based evaluation matter even though it did not explain in-context learning mechanistically [4](#source-4)?
2. What made CLIP's benchmark suite both historically important and methodologically caveated [5](#source-5)?
3. How can text normalization change the interpretation of Whisper WER [8](#source-8)?
4. What is the difference between GPT-4 predictable scaling and mechanistic explanation [11](#source-11)?
5. Why must o-series coding results be reported with test-time sampling and submission assumptions [14](#source-14)?

### Source citations

The measurement lecture draws its benchmark examples from GPT-3 [4](#source-4), CLIP/DALL-E/Whisper modality evaluations [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8), and later system-card or reasoning-report evidence [11](#source-11) [12](#source-12) [13](#source-13) [14](#source-14) [15](#source-15).

## Lecture 9: Productization Feedback Loops And Research-To-Deployment Pathways

### Learning goals

By the end of this lecture, students should be able to explain how OpenAI's public research record moved from demonstrations of capability to release artifacts that describe interfaces, mitigations, and governance; identify feedback loops linking pretraining, post-training, red teaming, product constraints, and deployment monitoring; and distinguish source-backed deployment claims from unsupported inferences about private training or product operations [3](#source-3) [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Key terms

Productization is the process by which a model becomes a usable system with prompts, APIs, safety layers, latency targets, policy defaults, documentation, and update practices. A research-to-deployment pathway is the sequence from a research result through evaluation, post-training, red teaming, interface design, and release. A feedback loop is any repeated process in which observed failures, user needs, or evaluator findings change data, training, policy, or product constraints. A system card or model card is a public release artifact that describes capabilities, risks, mitigations, and known limits at a bounded point in time [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Full explanation

Claim OAI-L9-C1. OpenAI's early large-scale reinforcement-learning papers already contained a productization lesson: capability depended on a whole operating system around the model. OpenAI Five was not just a neural policy trained for Dota 2; it required self-play leagues, distributed rollout infrastructure, recurrent policies, rule restrictions, evaluation against human teams, and an evolving benchmark environment. The paper's pathway from research to public claim ran through repeated competitions, ablations, human matches, and training-system iteration, which made deployment-like feedback visible before the company was releasing general assistants [3](#source-3).

Claim OAI-L9-C2. InstructGPT made the feedback loop explicit for language models. The paper starts from a product-facing diagnosis: next-token prediction on internet text does not necessarily produce models that follow user intent. Its pathway uses supervised demonstrations, reward modeling from human comparisons, and PPO to train models on prompts from an API-like distribution. That is the core deployment turn: observed user-facing mismatch becomes training data, preference data becomes a reward signal, and model selection is judged through human preference and safety-relevant evaluations rather than loss alone [10](#source-10).

Claim OAI-L9-C3. The InstructGPT loop was powerful but bounded. The paper's feedback came from selected labelers following OpenAI instructions, and the authors were careful that alignment to those judgments was not equivalent to alignment with all affected people or all human values. Productization therefore did not mean that deployment data magically solved alignment. It meant that the model developer created an operational feedback channel whose scope, labeler pool, rubric, prompt distribution, and reward-model objective had to be named [10](#source-10).

Claim OAI-L9-C4. GPT-4 changed the public release genre. The technical report gives less detail about architecture and data than GPT-3, but much more about predictable scaling, post-training, red teaming, risk categories, and residual limitations. The research-to-deployment path is visible as a layered sequence: build infrastructure whose large-run behavior can be forecast from smaller runs, align and evaluate the model, invite expert red teams, document risks in a system card, and still state that mitigations reduce rather than eliminate unsafe behavior [11](#source-11).

Claim OAI-L9-C5. A key GPT-4 productization feedback loop is the movement from discovered risks to targeted mitigations. The report describes expert red teaming in domains such as cybersecurity, biological risk, and international security, and it says resulting findings informed mitigations such as safer responses to hazardous chemical synthesis requests. That should be read as a process claim, not a guarantee of safety: red teaming discovers reachable failures and informs updates, but it is not a complete census of future misuse [11](#source-11).

Claim OAI-L9-C6. GPT-4o shows that productization can change the model's risk surface by changing the interaction channel. The system card presents GPT-4o as an omni model with text, audio, image, and video inputs and text, audio, and image outputs, then treats voice latency, unauthorized voice generation, speaker identification, accent performance, ungrounded inference, and audio robustness as release questions. A speech-to-speech assistant is not just a better benchmark table; it creates new product constraints around timing, voice identity, emotional reliance, and acoustic evaluation [12](#source-12).

Claim OAI-L9-C7. The GPT-4o card also illustrates how research evaluations are adapted, sometimes awkwardly, to product modalities. Many text safety evaluations were converted to audio with text-to-speech and then scored through text transcripts, while direct audio evaluation was used for narrower voice-specific risks. That is a practical bridge, but the card's own caveats matter: real user audio can include affect, noise, cross-talk, accent, and acoustic artifacts that transcript scoring can miss. Deployment feedback must therefore include modality-specific evidence, not only repurposed text tests [12](#source-12).

Claim OAI-L9-C8. o1 productized a different research idea: test-time reasoning trained by large-scale reinforcement learning. The system card frames o1 as spending more computation on chain-of-thought reasoning before answering and as using deliberative alignment to reason about safety policies in context. The resulting pathway added new release questions: how to set instruction hierarchies among system, developer, and user messages; how to monitor hidden reasoning; how to evaluate scheming or deception under scaffolds; and how to compare refusal improvements with cases where reasoning may produce more detailed dangerous advice [13](#source-13).

Claim OAI-L9-C9. The open-weight gpt-oss model card adds a final deployment loop: once weights are released, downstream modification becomes part of the safety analysis. The card evaluates default behavior and adversarially fine-tuned variants, and it discusses reasoning-channel formatting, tool-use protocols, and open-model risk. This is a different productization contract from a centrally served API. The release artifact must reason about what users can do after the model leaves the developer's direct control [15](#source-15).

### Discussion 9.1

The central discussion question is whether "deployment" should be treated as the end of research or as one of its methods. OpenAI's record suggests the latter: Dota 2 competitions exposed limits in large-scale RL; InstructGPT used API-like prompts and labeler feedback to change a base model; GPT-4 used red teaming and system-card reporting as part of launch; GPT-4o added modality-specific product safety; o1 turned hidden reasoning, instruction hierarchy, and Preparedness scoring into release objects; and gpt-oss made downstream modification part of the evaluation target [3](#source-3) [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Worked examples

The InstructGPT pathway begins with a user-facing failure: a base model can be fluent while ignoring intent. A small set of human-written demonstrations creates supervised fine-tuning data; human comparisons train a reward model; PPO optimizes the policy; and final evaluation asks labelers which outputs they prefer. The result is a model that better follows instructions on the measured distribution, but the method remains dependent on whose preferences were sampled and what instructions they followed [10](#source-10).

The GPT-4o voice pathway begins with a capability gain: real-time spoken interaction. The productization loop then adds restrictions to preset voices, classifiers for unauthorized voice output, refusals for speaker identification, policies for ungrounded inference, and evaluations that translate text tests into audio. Each safeguard is tied to a product affordance, which is why the card reads less like a pure model paper and more like a record of interface-specific release engineering [12](#source-12).

The o1 pathway begins with reasoning performance and then immediately becomes a governance problem. If hidden chain-of-thought can help monitor deception, it is valuable; if it is unfaithful, it is a fragile governance signal. The card therefore treats reasoning traces, instruction hierarchy, external red teams, and Preparedness categories as part of the model's operational specification rather than optional commentary [13](#source-13).

### Common mistakes

The first mistake is to treat product releases as if they simply expose a research model unchanged. In these sources, release changes include post-training, policy rubrics, external red teaming, product blocking, voice restrictions, instruction hierarchy, monitoring, and model-card commitments [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

The second mistake is to infer undisclosed training details from product behavior. The public record supports claims about disclosed methods and evaluation processes, but it does not support private claims about exact data mixtures, parameter counts, production prompts, or internal deployment thresholds beyond what the papers and cards state [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Self-check questions

1. Why is InstructGPT better understood as a feedback-loop paper than as only an RLHF algorithm paper [10](#source-10)?
2. What changed in the public reporting genre between GPT-3-style model papers and the GPT-4 technical report [11](#source-11)?
3. Why did GPT-4o require voice-specific mitigations that do not appear in text-only releases [12](#source-12)?
4. What new governance objects appear when a model is trained for extended test-time reasoning [13](#source-13)?
5. Why does an open-weight model card need to evaluate modified descendants, not just the default released model [15](#source-15)?

### Source citations

The deployment-pathway lecture uses Dota 2 as an early public example of research infrastructure meeting user-visible evaluation [3](#source-3), InstructGPT as the clearest feedback-to-product bridge [10](#source-10), and GPT-4/GPT-4o/o1/gpt-oss artifacts for public risk framing [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

## Lecture 10: Researcher Trajectories And Collaboration Graph

### Learning goals

By the end of this lecture, students should be able to read OpenAI's paper history as a collaboration graph rather than a sequence of isolated model names; distinguish first-author method trajectories from infrastructure, evaluation, and leadership trajectories; and explain how repeated clusters around scaling, multimodality, RLHF, safety evaluation, and reasoning shaped the company's public research direction [4](#source-4) [5](#source-5) [7](#source-7) [8](#source-8) [9](#source-9) [10](#source-10) [11](#source-11) [13](#source-13) [14](#source-14).

### Key terms

A trajectory is the visible path of a researcher or team through public artifacts over time. A collaboration graph connects people through shared papers, contribution statements, and recurring roles. A bridge author links two technical clusters, such as pretraining and RLHF or vision-language and image generation. A role matrix is a large-system contribution structure in which public credit is assigned by function, such as pretraining, data, alignment, safety, deployment, or evaluation [10](#source-10) [11](#source-11) [13](#source-13).

### Full explanation

Claim OAI-L10-C1. OpenAI's author graph is easiest to understand as five overlapping clusters. The scaling and pretraining cluster centers on GPT-3 and GPT-4; the multimodal cluster runs through CLIP, DALL-E, DALL-E 2, Whisper, GPT-4 vision, and GPT-4o; the RLHF and alignment cluster runs from recursive summarization to InstructGPT and GPT-4 post-training; the systems and robotics cluster runs through Dactyl, Rubik's Cube, Dota 2, and GPT-4 infrastructure; and the reasoning cluster emerges around o1 and competitive programming. The same names recur across clusters, but often in different roles [1](#source-1) [2](#source-2) [3](#source-3) [4](#source-4) [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8) [9](#source-9) [10](#source-10) [11](#source-11) [13](#source-13) [14](#source-14).

```mermaid
flowchart TB
  A["Pretraining group"] --> B["GPT spine"]
  C["Multimodal group"] --> D["Vision/speech spine"]
  E["Feedback group"] --> F["RLHF spine"]
  G["Safety group"] --> H["System cards"]
  B --> H
  D --> H
  F --> H
  H --> I["Reasoning reports"]
```

Claim OAI-L10-C2. Alec Radford's public trajectory is a repeated conversion of broad data into language-steered task interfaces. GPT-3 made tasks into text continuations; CLIP made visual classifiers into prompts embedded by a text encoder; DALL-E used image-text scaling and contrastive reranking in a generation setting; and Whisper made transcription, translation, language identification, and timestamping into task-token-conditioned speech processing. The common pattern is not a single architecture, but a research taste: train on broad naturally occurring data, expose a flexible interface, and evaluate zero-shot or few-shot transfer [4](#source-4) [5](#source-5) [6](#source-6) [8](#source-8).

Claim OAI-L10-C3. Aditya Ramesh's trajectory turns vision-language representation into generation. DALL-E 1 models text and image tokens autoregressively after compressing images through a discrete VAE; DALL-E 2 makes CLIP image embeddings the intermediate target and uses diffusion to decode pixels. This is a clean bridge from CLIP as a recognition and evaluation tool to CLIP as a generative bottleneck for variation, interpolation, and text-guided modification [5](#source-5) [6](#source-6) [7](#source-7).

Claim OAI-L10-C4. Prafulla Dhariwal and Mark Chen show a model-mechanics bridge between language scaling and generative media. Dhariwal appears in GPT-3's large-model implementation context and then in DALL-E 2's diffusion-latent image generation; Chen appears in DALL-E, DALL-E 2, GPT-4 vision, and later reasoning leadership. Their public paths show that OpenAI's multimodal work was not separate from frontier-model engineering. It reused scaling infrastructure, representation learning, diffusion methods, and later fed into GPT-family vision and reasoning systems [4](#source-4) [6](#source-6) [7](#source-7) [11](#source-11) [13](#source-13) [14](#source-14).

Claim OAI-L10-C5. The RLHF cluster has a different shape. Jeff Wu, Long Ouyang, Ryan Lowe, Jan Leike, Paul Christiano, John Schulman, Sandhini Agarwal, Pamela Mishkin, and collaborators appear around recursive summarization and InstructGPT. Their trajectory moves from reward models and decomposition to instruction following, labeler workflows, API-like prompts, refusal behavior, and GPT-4 alignment. This is the cluster that made human feedback a product-relevant post-training system rather than a narrow preference-learning demonstration [9](#source-9) [10](#source-10) [11](#source-11).

Claim OAI-L10-C6. The GPT-4 contribution structure makes role specialization visible. Jakub Pachocki is tied to pretraining and optimization leadership; Nick Ryder to architecture and data; Greg Brockman to infrastructure; Wojciech Zaremba to data and human-data systems; John Schulman, Jan Leike, and Ryan Lowe to reinforcement learning and alignment; Long Ouyang to instruction-following data; Sandhini Agarwal and Gretchen Krueger to system-card and launch-safety functions; and Pamela Mishkin to evaluations such as economic impact and overreliance. This is why collaboration analysis cannot be reduced to byline order [11](#source-11).

Claim OAI-L10-C7. The robotics and game-RL authors provide continuity rather than a dead branch. Dactyl and Rubik's Cube relied on simulation, domain randomization, recurrent control, and hardware-aware evaluation; Dota 2 relied on distributed self-play and long-running training systems. Several later frontier-model roles echo those earlier systems lessons: reliable infrastructure, training-run correctness, evaluation scaffolding, data pipelines, and deployment operations become central to GPT-4 and o-series releases [1](#source-1) [2](#source-2) [3](#source-3) [11](#source-11) [13](#source-13).

Claim OAI-L10-C8. The reasoning cluster reorganizes older collaborators around a new objective. o1's system card and the competitive-programming paper make large-scale reinforcement learning, chain-of-thought reasoning, self-verification, instruction hierarchy, and Preparedness evaluation central. Jakub Pachocki, Mark Chen, Wojciech Zaremba, Jerry Tworek, Lukasz Kaiser, and related o-series contributors appear less as a single traditional paper team than as a leadership and evaluation graph around reasoning models [13](#source-13) [14](#source-14).

### Discussion 10.1

Which is the more accurate unit of history: the named model, the paper, the author, or the capability cluster? A named model makes public memory easy, but the collaboration graph shows why GPT-4 is also a pretraining-infrastructure story, a data story, a post-training story, a safety-evaluation story, and a deployment story. Likewise, DALL-E 2 is not only an image generator; it depends on the CLIP representation path and diffusion-model collaborators [5](#source-5) [7](#source-7) [10](#source-10) [11](#source-11).

### Worked examples

To trace the CLIP-to-DALL-E 2 path, begin with Radford's CLIP: natural language supplies the downstream visual task through text embeddings. Then follow Ramesh into DALL-E 1, where image generation uses large-scale text-image modeling and contrastive reranking. Finally, follow Ramesh and Dhariwal into DALL-E 2, where CLIP's image embedding becomes the latent target of a prior and diffusion decoder. The graph is a methodological lineage, not merely a coauthor list [5](#source-5) [6](#source-6) [7](#source-7).

To trace the RLHF path, begin with recursive book summarization: reward models and decomposition try to make long tasks supervisable. Then move to InstructGPT, where demonstrations, comparisons, reward models, and PPO are applied to instruction following. GPT-4 expands the same cluster into a release stack with alignment leadership, refusal behavior, expert red teaming, system-card reporting, and public residual-risk documentation [9](#source-9) [10](#source-10) [11](#source-11).

### Common mistakes

The first mistake is hero flattening: assigning a broad company trajectory to one public figure. These artifacts show recurring leadership and first authorship, but they also show large teams, contribution matrices, and cross-functional release work. The second mistake is treating safety, data, and infrastructure roles as secondary to architecture. In GPT-4 and later cards, those roles are part of the research object itself because model behavior depends on post-training, data, evaluation, and deployment systems [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13).

### Self-check questions

1. What recurring method connects GPT-3, CLIP, and Whisper in Radford's trajectory [4](#source-4) [5](#source-5) [8](#source-8)?
2. How does DALL-E 2 convert CLIP from an evaluation or representation tool into a generative bottleneck [5](#source-5) [7](#source-7)?
3. Why does GPT-4 require a role-matrix reading rather than a simple byline reading [11](#source-11)?
4. How did recursive summarization prepare the ground for InstructGPT's product-facing RLHF loop [9](#source-9) [10](#source-10)?
5. What links the older RL systems papers to o-series reasoning releases [1](#source-1) [3](#source-3) [13](#source-13) [14](#source-14)?

### Source citations

The collaboration lecture uses the selected OpenAI corpus as a map of recurring research groups: robotics and self-play [1](#source-1) [2](#source-2) [3](#source-3), language and multimodal scaling [4](#source-4) [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8), feedback research [9](#source-9) [10](#source-10), and later system-card or reasoning work [11](#source-11) [12](#source-12) [13](#source-13) [14](#source-14).

## Lecture 11: Complete Chronological Bibliography With Paper Capsules

### Learning goals

By the end of this lecture, students should be able to place the selected OpenAI sources in chronological order, summarize each paper or card in one source-backed capsule, identify what each source contributes to the course's history of capabilities, alignment, evaluation, and deployment, and explain why any "complete" bibliography remains conditional on search scope and index coverage [1](#source-1) [2](#source-2) [3](#source-3) [4](#source-4) [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8) [9](#source-9) [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [14](#source-14) [15](#source-15) [16](#source-16) [17](#source-17).

### Key terms

A paper capsule is a compact, citable summary of a source's question, method, evidence, limitations, and historical role. A selected source is part of the course's major-source set, not necessarily every OpenAI publication. Corpus coverage describes how sources were discovered and checked. Residual gaps are plausible missing items left after searching official publication indexes, research indexes, arXiv metadata, and candidate lists [16](#source-16) [17](#source-17).

### Full explanation

Claim OAI-L11-C1. This lecture's bibliography is "complete" for the fifteen selected OpenAI paper and card sources in the course registry, not for every OpenAI public artifact. It is chronological by publication date where the registry supplies dates, and it treats system or model cards as first-class sources because later OpenAI history is often documented through release cards rather than conventional reproducible technical reports [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15) [16](#source-16) [17](#source-17).

### Worked examples

**2018 - Learning Dexterous In-Hand Manipulation.** This paper asks whether a policy trained entirely in randomized simulation can transfer to a real Shadow hand manipulating a block. Its method combines PPO, asymmetric actor-critic training, recurrent control, domain randomization, synthetic vision, and a real robot platform. Its historical role is to show OpenAI's early commitment to large learned systems, where the research result lives in the interaction among simulator design, sensing, distributed rollouts, and hardware evaluation. Its limitation is that the demonstrated dexterity is specialized and system-dependent, not general physical intelligence [1](#source-1).

**2019 - Solving Rubik's Cube with a Robot Hand.** This paper extends sim-to-real robotics with automatic domain randomization. The robot does not learn the abstract cube-solving algorithm; a conventional solver provides subgoals, while a learned controller performs cube rotations and flips under varied simulated conditions. The historical contribution is the curriculum over simulation parameters, which turns transfer into an adaptive training problem. The limitation is that the demonstration still depends on modified sensing, constrained protocols, recurrent adaptation, and nontrivial failure modes [2](#source-2).

**2019 - Dota 2 with Large Scale Deep Reinforcement Learning.** This source documents OpenAI Five as a scaled self-play system rather than a single algorithmic trick. The method uses PPO-like actor-critic training, recurrent policies, distributed rollout infrastructure, league-style self-play, and restricted but still complex Dota 2 conditions. Its historical role is to make long-running RL infrastructure and human benchmark play into a public research artifact. Its limitation is that game restrictions, shaped observation/action spaces, and environment-specific engineering matter deeply to the result [3](#source-3).

**2020 - Language Models are Few-Shot Learners.** GPT-3 is the selected source that makes scale and prompting central to OpenAI's language-model direction. The paper trains a 175B-parameter autoregressive transformer and evaluates zero-shot, one-shot, and few-shot prompting across a broad benchmark portfolio. Its historical contribution is the shift from task-specific fine-tuning toward fixed-weight adaptation through context. Its limitation is that in-context learning is measured behaviorally, while mechanisms, contamination boundaries, social risks, and deployment behavior remain incompletely explained [4](#source-4).

**2021 - Zero-Shot Text-to-Image Generation.** DALL-E 1 translates the GPT-style sequence-modeling recipe into image generation. A discrete VAE compresses images into visual tokens, and a large autoregressive transformer models text and image tokens jointly. Its evidence includes human comparison and generation examples, often with contrastive reranking. The paper's historical role is to show that internet-scale text-image modeling can produce flexible image synthesis, while its limitations include lossy tokenization, best-of-many selection, weaker compositional reliability, and pre-diffusion baselines [6](#source-6).

**2021 - Learning Transferable Visual Models From Natural Language Supervision.** CLIP trains image and text encoders contrastively on 400 million image-text pairs, then uses natural-language prompts to define downstream classifiers. Its historical role is to turn language into a visual task interface: class names and prompt templates become part of the classifier. Its limitations are as important as its results: prompt and label choices affect both accuracy and harm, the evaluation suite co-evolved with development, and the model remains weak on many specialized, fine-grained, counting, and out-of-distribution tasks [5](#source-5).

**2021 - Recursively Summarizing Books with Human Feedback.** This paper turns scalable oversight into a concrete summarization experiment. Long texts are decomposed into shorter chunks, models summarize local pieces, and human feedback trains reward models and policies that compose upward into book-length summaries. Its historical role is to bridge GPT-3-era models and later RLHF assistants by making decomposition, labeler judgment, and reward modeling central. Its limitation is that fixed decompositions lose global context, errors compound, and automatic summary judgments remain unreliable for high-stakes accuracy [9](#source-9).

**2022 - Training Language Models to Follow Instructions with Human Feedback.** InstructGPT is the selected source for the product-facing RLHF turn. The paper diagnoses objective mismatch between next-token prediction and user intent, then uses supervised demonstrations, human preference comparisons, reward modeling, and PPO to make GPT-3-derived models follow instructions better. Its historical role is to make post-training a central OpenAI capability and safety pathway. Its limitation is that the feedback process reflects a particular prompt distribution, labeler population, and instruction rubric rather than universal human values [10](#source-10).

**2022 - Hierarchical Text-Conditional Image Generation with CLIP Latents.** DALL-E 2, or unCLIP, routes text-to-image generation through CLIP's image embedding space. A prior predicts a CLIP image embedding from text, and a diffusion decoder renders an image from that embedding. Its historical role is to join CLIP representation learning with diffusion-era generation, enabling variation, interpolation, and text-diff manipulations. Its limitation is the CLIP-latent bottleneck: semantic control and diversity improve, but exact text rendering, attribute binding, and fine relational detail can fail [7](#source-7).

**2022 - Robust Speech Recognition via Large-Scale Weak Supervision.** Whisper is the selected speech source. It uses a conventional encoder-decoder transformer trained on 680,000 hours of multilingual and multitask weak supervision, with task tokens for transcription, translation, language identification, no-speech handling, and timestamping. Its historical role is to show that broad weak supervision and unified formatting can produce robust zero-shot speech systems. Its limitations include dataset provenance uncertainty, language imbalance, text-normalization sensitivity, and long-form hallucination or repetition failures [8](#source-8).

**2023 - GPT-4 Technical Report.** GPT-4 is the selected frontier-model report. It presents a multimodal model with strong professional-exam, academic, coding, multilingual, and visual capabilities, but withholds many architectural and training details. Its historical role is twofold: predictable scaling from smaller runs becomes part of frontier-model engineering, and system-card-style reporting becomes part of release documentation. Its limitations include residual hallucination, jailbreakability, red-team sampling limits, calibration tradeoffs after post-training, and incomplete multilingual and societal-risk coverage [11](#source-11).

**2024 - GPT-4o System Card.** GPT-4o is the selected source for real-time omni deployment. The card describes a model that accepts text, audio, image, and video inputs and can generate text, audio, and image outputs, with low-latency spoken interaction as a major product property. Its historical role is to make modality-specific release safety central: voice identity, speaker identification, accent performance, ungrounded inference, emotional reliance, health, science, underrepresented languages, external red teaming, and Preparedness scoring all become part of the public artifact. Its limitation is that many evaluations are adapted from text or summarized internally [12](#source-12).

**2024 - OpenAI o1 System Card.** o1 is the selected reasoning-system card. It frames the model as trained with large-scale reinforcement learning for chain-of-thought reasoning and uses deliberative alignment to reason about safety policies. Its historical role is to move test-time reasoning, hidden reasoning traces, instruction hierarchy, scheming evaluations, and Preparedness Framework categories into the release record. Its limitations are checkpoint dependence, uncertainty about chain-of-thought faithfulness, lower-bound evaluations under limited scaffolding, and cases where stronger reasoning may produce more detailed dangerous advice if safeguards fail [13](#source-13).

**2025 - Competitive Programming with Large Reasoning Models.** This paper is the selected source for o-series coding and test-time compute. It compares reasoning models on CodeForces and IOI-style tasks, including specialized inference systems with many samples, generated tests, clustering, reranking, and submission allocation. Its historical role is to show that OpenAI viewed coding success as a joint product of RL-trained reasoning and inference-time search or verification. Its limitation is that ratings and solved-task claims depend heavily on contest simulation rules, sampling budgets, full-test availability, and submission assumptions [14](#source-14).

**2025 - gpt-oss-120b & gpt-oss-20b Model Card.** The gpt-oss card is the selected source for open-weight reasoning releases. It treats model formatting, tool protocols, safety behavior, adversarial fine-tuning, and downstream modification as part of the release surface. Its historical role is to show a different deployment contract: the developer must evaluate not only the default served model, but plausible modified descendants after weights are released. Its limitation is that open-weight risk analysis necessarily depends on assumptions about downstream actors, fine-tuning effort, and external safeguards [15](#source-15).

### Discussion 11.1

The bibliography shows a shift in what counts as a primary source. In 2018-2022, major OpenAI sources often look like conventional papers: problem, method, experiments, limitations. By 2023-2025, system and model cards become equally central because the public history of GPT-4, GPT-4o, o1, and gpt-oss is partly a history of release constraints, safety evaluation, product interfaces, and governance thresholds rather than full architectural disclosure [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Possible Missing Publications

Claim OAI-L11-C2. The search method combined the selected-source registry with official OpenAI publication and research sitemap snapshots, candidate metadata, and author-focused review passes. The registry's discipline is important: sources 1-15 support paper-specific technical claims, while the OpenAI publication and research sitemap snapshots support corpus coverage and missing-publication discussion rather than technical claims about model mechanisms [16](#source-16) [17](#source-17).

Claim OAI-L11-C3. The indexes checked include official publication-style pages and research-style pages, plus candidate records for official OpenAI pages, arXiv-linked papers, model or system cards, evaluation releases, and degraded blog-only entries. This method is broad enough to surface likely omissions such as OpenAI Gym, Reptile, Glow, Image GPT, Jukebox, Point-E, consistency models, SWE-bench Verified, MLE-bench, DALL-E 2 pre-training mitigations, and Voice Engine safety work, but those are not automatically elevated into the selected-major-source set unless they are read, registered, and assigned public citation numbers [16](#source-16) [17](#source-17).

Claim OAI-L11-C4. Residual gaps remain. Official sitemaps can include pages with missing dates, changed titles, launch posts rather than papers, or public pages that point to separate PDFs, repos, datasets, or arXiv records. arXiv author and affiliation searches can miss company work without clean affiliation metadata or include papers that are only affiliated-author work rather than official company publications. Product documentation, contribution pages, repositories, datasets, and evaluation harnesses can also be historically important without fitting a paper-card registry. A future bibliography pass should separate "selected course anchors" from "full OpenAI public research corpus" rather than pretending that one table can do both jobs [16](#source-16) [17](#source-17).

### Common mistakes

The first mistake is to cite system cards as if they were fully reproducible technical reports. They are primary sources for release claims, safety process, and disclosed evaluations, but they often do not publish training mixtures, parameter counts, or full experimental details. The second mistake is to drop non-paper artifacts from the history. GPT-4o, o1, and gpt-oss show that cards can be the central public source for deployment-era model behavior [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

The third mistake is to treat the selected bibliography as every relevant OpenAI publication. The selected set is a curated course spine. The official publication and research sitemap snapshots support the claim that additional OpenAI artifacts exist and should be handled in a residual-gap section, not smuggled into technical claims without registry citations [16](#source-16) [17](#source-17).

### Self-check questions

1. Which selected source first makes prompting and in-context learning the central evaluation interface [4](#source-4)?
2. Which selected source turns CLIP image embeddings into a generative latent bottleneck [7](#source-7)?
3. Why is InstructGPT a different kind of bibliography item from GPT-3 even though both descend from language modeling [4](#source-4) [10](#source-10)?
4. What makes GPT-4o and o1 system cards essential primary sources for deployment history [12](#source-12) [13](#source-13)?
5. Why should OpenAI sitemap sources be cited for discovery and residual gaps, not for paper-specific technical mechanisms [16](#source-16) [17](#source-17)?

### Source citations

The bibliography lecture is anchored in the complete selected OpenAI source set: embodied RL [1](#source-1) [2](#source-2) [3](#source-3), language and multimodal generative modeling [4](#source-4) [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8), feedback research [9](#source-9) [10](#source-10), public system and reasoning reports [11](#source-11) [12](#source-12) [13](#source-13) [14](#source-14) [15](#source-15), and discovery indexes [16](#source-16) [17](#source-17).

## Lecture 12: Synthesis: What This Company Believed About Intelligence Over Time

### Learning goals

By the end of this lecture, students should be able to state the changing assumptions about intelligence visible in OpenAI's public research record; explain how those assumptions moved from reinforcement learning and simulation, to scale and prompting, to multimodal interfaces, to human-feedback alignment, to deployment governance and reasoning; and preserve uncertainty where public sources do not reveal private beliefs, exact training details, or internal decision processes [1](#source-1) [3](#source-3) [4](#source-4) [5](#source-5) [8](#source-8) [10](#source-10) [11](#source-11) [13](#source-13) [15](#source-15).

### Key terms

A revealed belief is an inference from repeated public research choices, not a private statement of intent. Scaling is the bet that more data, compute, parameters, environment steps, or inference-time computation can unlock qualitatively broader behavior. Interface is the channel through which a general model is steered, such as prompts, labels, task tokens, policy rubrics, voice, tools, or hidden reasoning. Alignment is the attempt to make model behavior follow intended human or policy goals under deployment conditions [4](#source-4) [5](#source-5) [8](#source-8) [10](#source-10) [13](#source-13).

### Full explanation

Claim OAI-L12-C1. The earliest selected sources suggest a belief that intelligence could be built by scaling learning systems around difficult interfaces. In robotics and Dota 2, the interface was not a web prompt; it was a simulator, a robot hand, a strategic game environment, self-play, randomized dynamics, recurrent state, and hardware or match evaluation. Intelligence was treated less as hand-coded symbolic expertise and more as behavior emerging from training across broad enough variations of an environment [1](#source-1) [2](#source-2) [3](#source-3).

Claim OAI-L12-C2. GPT-3 made the belief more general and more legible: a sufficiently large next-token model could adapt to many tasks from context. This did not prove that the model understood tasks the way people do, and the paper did not explain the mechanism of in-context learning. But it did reveal a powerful operational belief: broad pretraining plus text prompts could replace many task-specific training pipelines, making the interface between user and model part of the model's intelligence [4](#source-4).

Claim OAI-L12-C3. CLIP, DALL-E, and Whisper show that OpenAI did not treat language intelligence as confined to text. CLIP uses natural language to define visual recognition tasks; DALL-E turns text into image-token generation; DALL-E 2 routes generation through CLIP latents and diffusion; Whisper turns speech processing into task-token-conditioned sequence modeling over weakly supervised audio. The implied belief is that language can be a control layer for perception, generation, and audio, but each modality imposes its own bottlenecks and failure modes [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8).

```mermaid
flowchart TB
  A["RL environments"] --> B["Scale behavior"]
  B --> C["Text context"]
  C --> D["Modality control"]
  C --> E["Feedback steering"]
  D --> F["Frontier systems"]
  E --> F
  F --> G["Reasoning and cards"]
```

Claim OAI-L12-C4. The alignment papers reveal a second belief: raw capability is not the same as useful intelligence. Recursive summarization assumes that some tasks are too long for direct human supervision and therefore need decomposition plus human feedback. InstructGPT assumes that a base model's objective is misaligned with user intent and that demonstrations, preference comparisons, reward models, and policy optimization can redirect behavior. This is a practical, operational belief in steerability through feedback, not proof that values have been solved [9](#source-9) [10](#source-10).

Claim OAI-L12-C5. GPT-4 shows the fusion of those beliefs into a frontier-model operating model. Intelligence is scaled and forecast from smaller runs; it is broad enough to appear in exams, code, multilingual tasks, and vision; it is steered through post-training; and it is released through red teaming, system-card documentation, mitigations, and residual-risk disclosure. The report's withheld details are themselves historically meaningful: by this point, public communication emphasizes capability, safety process, and limitations more than reproducible architecture [11](#source-11).

Claim OAI-L12-C6. GPT-4o adds a belief about intelligence as interaction. Low-latency speech-to-speech behavior matters because an assistant is evaluated not only by correct answers, but by timing, voice, modality, emotional salience, and product constraints. The system card's safety topics show that once intelligence is embodied in a conversational interface, risks arise from speaker identity, voice generation, affect, health contexts, language coverage, and real-world audio conditions. Interaction becomes part of the intelligence claim [12](#source-12).

Claim OAI-L12-C7. o1 and competitive programming reveal a later belief: more intelligent behavior may come from training models to spend computation at inference time. o1 is presented as reasoning through chain-of-thought before answering, while the competitive-programming paper treats sampling, generated tests, self-verification, reranking, and submission allocation as part of solving hard tasks. This does not license a simple analogy between model reasoning and human thought. It does show that OpenAI's public research direction moved from scaling pretraining alone toward scaling deliberation and verification at test time [13](#source-13) [14](#source-14).

Claim OAI-L12-C8. The gpt-oss card reveals a final belief about intelligence as a distributed ecosystem. Once an open-weight model is released, intelligence is no longer only what the developer serves through an API. It is what downstream users can fine-tune, scaffold, tool-connect, and deploy under different constraints. OpenAI's public artifact therefore treats adversarial fine-tuning, tool protocols, reasoning formats, and downstream modification as safety-relevant properties of the release [15](#source-15).

### Discussion 12.1

The strongest synthesis is not "OpenAI believed intelligence is scale" and not "OpenAI believed intelligence is RLHF." The public record suggests a compound view: intelligence emerges from scalable objectives, broad data or environments, flexible interfaces, post-training feedback, evaluation pressure, deployment constraints, and sometimes inference-time computation. The company's public sources repeatedly shift the interface through which intelligence is expressed: simulator actions, game policies, text prompts, image-text embeddings, task tokens, human preference rubrics, system messages, voice, tools, hidden reasoning, and open-weight protocols [1](#source-1) [3](#source-3) [4](#source-4) [5](#source-5) [8](#source-8) [10](#source-10) [12](#source-12) [13](#source-13) [15](#source-15).

### Worked examples

The GPT-3 to InstructGPT transition is the cleanest example of a belief revision. GPT-3 showed that scale plus prompting creates broad capability, but InstructGPT argued that this capability is not automatically aligned with user intent. The response was not to discard the base model, but to wrap it in a human-feedback training loop. The implied belief is that foundation-model intelligence is a substrate that must be shaped by task and social feedback before it becomes a useful assistant [4](#source-4) [10](#source-10).

The CLIP to DALL-E 2 transition shows another revision. CLIP demonstrated that natural language could define visual tasks through contrastive embeddings, but DALL-E 2 used the CLIP image embedding as a generative latent. The same representation that made zero-shot classification flexible also became a bottleneck that enabled variation and semantic control while losing some exact detail. OpenAI's multimodal belief was therefore not "one representation solves vision"; it was "a language-linked representation can become a reusable interface, with tradeoffs" [5](#source-5) [7](#source-7).

The GPT-4o to o1 transition shows a shift from interaction speed to deliberation depth. GPT-4o emphasizes real-time multimodal conversation and product safety for voice; o1 emphasizes slower reasoning, instruction hierarchy, chain-of-thought monitoring, and risk evaluation for more deliberate models. Both are assistant directions, but they optimize different aspects of intelligence: fluid multimodal interaction versus extended problem solving and policy reasoning [12](#source-12) [13](#source-13).

### Common mistakes

The first mistake is mind-reading the company from public papers. These sources reveal repeated research commitments, not private beliefs. The second mistake is linear triumphalism: each later source changes the frame rather than simply replacing the earlier one. Robotics, RL, scaling, multimodality, RLHF, safety cards, reasoning, and open weights remain overlapping strands. The third mistake is treating intelligence and safety as separate timelines. In OpenAI's public record after InstructGPT and GPT-4, model capability, post-training, evaluation, productization, and risk governance are intertwined [3](#source-3) [4](#source-4) [10](#source-10) [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).

### Self-check questions

1. What early belief about intelligence is visible in Dactyl, Rubik's Cube, and Dota 2 [1](#source-1) [2](#source-2) [3](#source-3)?
2. How did GPT-3 make the prompt interface central to the meaning of model capability [4](#source-4)?
3. Why does CLIP support the claim that language became a control layer for vision [5](#source-5)?
4. What belief about steerability is shared by recursive summarization and InstructGPT [9](#source-9) [10](#source-10)?
5. How do o1 and gpt-oss complicate a simple "bigger pretrained model" theory of intelligence [13](#source-13) [15](#source-15)?

### Source citations

The synthesis lecture ties together OpenAI's public evidence for embodied experimentation [1](#source-1) [2](#source-2) [3](#source-3), scalable representation learning [4](#source-4) [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8), human-feedback shaping [9](#source-9) [10](#source-10), and later evaluation-centered deployment artifacts [11](#source-11) [12](#source-12) [13](#source-13) [14](#source-14) [15](#source-15).

# Cheat Sheets

Claim OAI-CS-C1. The shortest technical summary of the OpenAI public research trajectory is: learn from simulation and self-play, scale generative models, align outputs with human feedback, connect modalities through representation learning, and formalize safety/evaluation evidence through technical reports and system cards [1](#source-1) [3](#source-3) [4](#source-4) [5](#source-5) [10](#source-10) [12](#source-12).

| Thread | Core OpenAI sources | What to remember |
| --- | --- | --- |
| Embodied and game RL | [1](#source-1), [2](#source-2), [3](#source-3) | Domain randomization, self-play, and large-scale RL made generality an engineering and evaluation problem before the language-model era. |
| Scaling language models | [4](#source-4), [11](#source-11) | GPT-3 made few-shot prompting central; GPT-4 shifted the public report toward broad benchmark and risk evaluation. |
| Feedback and instruction following | [9](#source-9), [10](#source-10) | Human feedback became a bridge from raw model capability to usefulness and preference-shaped behavior. |
| Multimodal representation | [5](#source-5), [6](#source-6), [7](#source-7), [8](#source-8) | Text became a supervisory interface for vision, image generation, and speech recognition. |
| Reasoning and system cards | [12](#source-12), [13](#source-13), [14](#source-14), [15](#source-15) | Later public artifacts emphasize evaluation, risk controls, and capability-specific measurement. |

```mermaid
flowchart TB
  P["Pretraining"] --> T["Prompting"]
  T --> F["Human feedback"]
  F --> E["Evaluation"]
  E --> R["Reasoning reports"]
  M["Multimodal"] --> E
```

# Glossary

Claim OAI-GL-C1. `Few-shot learning` in this book means prompting a language model with examples at inference time, a core GPT-3 framing rather than a guarantee of task mastery [4](#source-4).

Claim OAI-GL-C2. `RLHF` means reinforcement learning from human feedback, especially the pipeline of collecting demonstrations or comparisons, training a reward model, and optimizing a policy against that learned reward in the InstructGPT family of work [10](#source-10).

Claim OAI-GL-C3. `Contrastive language-image pretraining` means training image and text encoders so matching image-text pairs are close relative to mismatches, the key mechanism in CLIP [5](#source-5).

Claim OAI-GL-C4. `Diffusion prior over CLIP latents` refers to the DALL-E 2 design that uses CLIP latent structure as part of a hierarchical text-conditional image generation system [7](#source-7).

Claim OAI-GL-C5. `System card` means a public artifact that reports model behavior, safety work, evaluation scope, limitations, and deployment-relevant risk framing, as seen in GPT-4o and o1 [12](#source-12) [13](#source-13).

# Exam-Style Review

1. Claim OAI-EX-C1. Explain why the Dota 2 and robotic manipulation papers are useful for understanding OpenAI's later scaling culture even though they are not language-model papers [1](#source-1) [2](#source-2) [3](#source-3).
2. Claim OAI-EX-C2. Compare GPT-3 few-shot prompting with InstructGPT post-training. What problem does each method make visible, and what does each leave unresolved [4](#source-4) [10](#source-10)?
3. Claim OAI-EX-C3. Use CLIP, DALL-E, DALL-E 2, and Whisper to explain why text became a general control or supervision interface across modalities [5](#source-5) [6](#source-6) [7](#source-7) [8](#source-8).
4. Claim OAI-EX-C4. Read the GPT-4 technical report beside the GPT-4o and o1 system cards. Which claims are technical capability claims, which are safety-evaluation claims, and which should remain deployment-limited [11](#source-11) [12](#source-12) [13](#source-13)?
5. Claim OAI-EX-C5. Describe a defensible evidence boundary for `reasoning models` using the o1 system card and competitive-programming report without inferring private training recipes [13](#source-13) [14](#source-14).

# Citation Appendix

## Source 1: Learning Dexterous In-Hand Manipulation {#source-1}
Public URL: https://arxiv.org/abs/1808.00177v5

## Source 2: Solving Rubik's Cube with a Robot Hand {#source-2}
Public URL: https://arxiv.org/abs/1910.07113v1

## Source 3: Dota 2 with Large Scale Deep Reinforcement Learning {#source-3}
Public URL: https://arxiv.org/abs/1912.06680v1

## Source 4: Language Models are Few-Shot Learners {#source-4}
Public URL: https://arxiv.org/abs/2005.14165v4

## Source 5: Learning Transferable Visual Models From Natural Language Supervision {#source-5}
Public URL: https://arxiv.org/abs/2103.00020v1

## Source 6: Zero-Shot Text-to-Image Generation {#source-6}
Public URL: https://arxiv.org/abs/2102.12092v2

## Source 7: Hierarchical Text-Conditional Image Generation with CLIP Latents {#source-7}
Public URL: https://arxiv.org/abs/2204.06125v1

## Source 8: Robust Speech Recognition via Large-Scale Weak Supervision {#source-8}
Public URL: https://arxiv.org/abs/2212.04356v1

## Source 9: Recursively Summarizing Books with Human Feedback {#source-9}
Public URL: https://arxiv.org/abs/2109.10862v2

## Source 10: Training language models to follow instructions with human feedback {#source-10}
Public URL: https://arxiv.org/abs/2203.02155v1

## Source 11: GPT-4 Technical Report {#source-11}
Public URL: https://arxiv.org/abs/2303.08774v6

## Source 12: GPT-4o System Card {#source-12}
Public URL: https://arxiv.org/abs/2410.21276v1

## Source 13: OpenAI o1 System Card {#source-13}
Public URL: https://arxiv.org/abs/2412.16720v2

## Source 14: Competitive Programming with Large Reasoning Models {#source-14}
Public URL: https://arxiv.org/abs/2502.06807v2

## Source 15: gpt-oss-120b and gpt-oss-20b Model Card {#source-15}
Public URL: https://arxiv.org/abs/2508.10925v1

## Source 16: OpenAI publication sitemap snapshot {#source-16}
Public URL: https://openai.com/sitemap-publication.xml

## Source 17: OpenAI research sitemap snapshot {#source-17}
Public URL: https://openai.com/sitemap-research.xml

# Verification Appendix

Claim OAI-VA-C1. The build created a candidate bibliography, selected-source manifest, source-specific read reports, author trajectory reports, citation registry, and evidence matrix before rendering. The final prose cites public URLs; local artifact paths are intentionally confined to the verification files [16](#source-16) [17](#source-17).

Claim OAI-VA-C2. Possible missing publications remain most likely around OpenAI official HTML pages that were listed in public indexes but blocked during direct HTML retrieval. The compensating evidence is that selected technical papers and cards were preserved through arXiv PDFs or accessible public index artifacts [4](#source-4) [10](#source-10) [11](#source-11) [12](#source-12) [16](#source-16).

Claim OAI-VA-C3. Residual uncertainty is highest for internal training recipes, product deployment feedback loops, and non-public evaluation decisions. This course uses system cards and technical reports to discuss public evaluation and mitigation language, not to reconstruct private implementation details [11](#source-11) [12](#source-12) [13](#source-13) [15](#source-15).
