# Reusable prompt: turn a discovery report into an engineering briefing

Turn this task's domain-specific fan-out Markdown report into a concise briefing for a frontier applied AI or research engineer at OpenAI or Anthropic. The reader has five to ten minutes and has not read the underlying sources. They understand engineering, but do not know this particular work. Use the report already identified in this task; if several reports are equally plausible, ask which one.

Read the report and select its three most valuable sources for this audience. Treat its ranking and summaries as leads, not sufficient evidence. Read the complete original sources, including figures, tables, methods, and relevant linked code or notebooks needed to explain the mechanism. Verify numbers and distinguish reported results from your interpretation. If a source is inaccessible, state the specific gap rather than inventing details or implying a full read.

Deliver the briefing directly, without a plan or a round of preference questions. Aim for 600–900 words total, using fewer when sufficient. Preserve the consequential details rather than compressing everything into vague headlines.

Start with two sentences explaining what matters across this domain today. Then provide three numbered takeaways. For each:

- Give a specific, informative title and a direct primary-source link.
- Write a self-contained, conversational paragraph explaining the concrete problem, what happened before, what changed, how the approach works, the experimental or evaluation setup, the measured result, and what that result does and does not establish. Use a second short paragraph only when it materially improves comprehension.
- Explain the setup precisely enough to interpret the result: relevant model, data, task, baseline, evaluator, environment, and amount of human help. Include only the details that affect the conclusion. For evaluations, distinguish deterministic checks, model judges, and human review. For training, distinguish training examples, model size, trainable parameters, training reward, and final evaluation.
- Define unfamiliar terms at first use, with their actual referent. Say who adopted what, what code churn counts, what a successful example must satisfy, and what each percentage uses as its denominator. Distinguish percentage-point gains from relative gains and overall results from slices.
- Explain the important figures in words: what is measured, compared, and observed. Do not confuse activity with productivity, correlation with causation, proxy rewards with task success, or structural validity with factual correctness. Include the most consequential remaining failure or limitation.
- End with a concrete engineering implication grounded in the evidence. Label extrapolations as interpretation; do not turn a small demonstration into a general production claim.

Use natural prose that is easy to understand when heard once. Be concise, direct, and sharp without sacrificing the mechanism or evidence. A tiny illustrative example is welcome when it makes an abstract idea concrete; identify invented examples as illustrations. Avoid unexplained jargon, promotional language, generic advice, and repetitive headings for every component. Do not recite every chart value or configuration flag.

If this task has an editable fan-out Markdown report, put this briefing at the top and preserve its full screening audit below. Edit only that report; do not change other lanes or the main digest. Also present the complete briefing in the conversation with clickable source links.

Quality check before finishing: could the reader explain the problem, reproduce the essential logic of the setup, interpret the main number correctly, and name the unresolved limitation without opening the source? If not, fix the missing context.
