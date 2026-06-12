# Source Discovery

Use this file when scouting items for a Codex-native DeepBrief.

## Source Classes

1. **Primary agent runtime and coding-agent systems**
   - OpenAI Codex, OpenAI Agents SDK, OpenAI Responses/API platform changes.
   - Anthropic Claude Code and Claude Agent SDK.
   - E2B, Modal, Browserbase, Daytona, Firecracker/VM sandboxing, container/runtime isolation, and agent execution infrastructure.
   - Cursor, Windsurf, Replit, Sourcegraph, Vercel AI SDK, LangChain/LangGraph, LlamaIndex, DSPy, and other harness/framework releases when they expose implementation mechanics.

2. **Papers**
   - arXiv `cs.CL`, `cs.AI`, `cs.SE`, `cs.DB`, `cs.DC`, `cs.OS`, and adjacent systems categories.
   - Prefer HTML when available; fall back to PDF text.
   - Favor papers with code, eval harnesses, memory/state mechanisms, sandboxing, extraction/document AI, tool use, agent orchestration, inference systems, or model-training implications.

3. **Repo feature releases and diffs**
   - `openai/codex`.
   - `openai/openai-agents-python`.
   - `anthropics/claude-code`.
   - `anthropics/claude-agent-sdk-python`.
   - `e2b-dev/E2B`.
   - LangChain/LangGraph, LlamaIndex, Braintrust, Vercel AI SDK, Browserbase, Modal, Firecrawl, Exa, Reducto, Unstructured, Contextual AI examples, and other user-requested repos.

4. **Applied AI companies and products**
   - Cognition/Devin, Decagon, Braintrust, Contextual AI, Google/DeepMind, OpenAI, Anthropic, Cursor, Sierra, Harvey, Glean, Perplexity, Reducto, Ramp, Intercom, and comparable high-signal engineering organizations.
   - Prioritize engineering posts, benchmark writeups, public changelogs, docs, talks, and papers over marketing pages.

5. **Benchmarks, evals, and document/extraction AI**
   - SWE-bench variants, tau-bench/tau2-bench, ToolSandbox, APB, LongMemEval, MCP/tool benchmarks, BrowseComp-style web-agent evals.
   - Contextual AI extraction/document benchmarks, Reducto/document AI evals, schema extraction, retrieval, reranking, and grounding systems.

6. **Model training, inference, and frontier-model operations**
   - Frontier-lab research posts, system cards when technical, inference optimization, RL/post-training, tool-use training, memory/context, multimodal agent data, and deployment mechanics.
   - Tie model-side changes to applied agent/product implications.

7. **High-signal builders and discourse**
   - Follow user-named and high-signal builders/researchers across public blogs, talks, GitHub, newsletters, podcasts, and accessible X posts.
   - Examples include people building or analyzing Codex/Claude Code-like systems, Devin-like systems, agent harnesses, eval platforms, document AI systems, model training, and inference infrastructure.
   - Treat discourse as lead generation. Verify factual claims through primary sources before citing.

## High-Recall Quotas

Screen at least 100 distinct candidates before final ranking. Use these lane targets and backfill from adjacent lanes when one is thin:

- Papers/evals/document AI: 25+.
- Repo releases, diffs, SDKs, runtimes, harnesses: 25+.
- Company/lab engineering posts and technical docs: 20+.
- Model training/inference/frontier operations: 10+.
- Applied product/company updates with technical substance: 10+.
- High-signal builder discourse leads: 10+.

Do not let OpenAI, Anthropic, Codex, or Claude Code crowd out the whole brief. They are primary resources, not the entire source universe.
Do not replace missing lane coverage with many adjacent releases from one repository or many low-signal papers from one query. If a lane is thin, record the shortfall and backfill from the closest adjacent lane with primary-source evidence.

## Monthly Discovery Subagent Requirements

When the user requests a monthly/high-recall run with explicit source-balance counts, those counts replace the daily lane targets above.

For a 1,000-source monthly run, discovery must be subagent-led:

- Spawn separate discovery subagents or waves for each major lane: papers/evals/benchmarks, repo/source-code items, company/lab engineering posts/docs, builder discourse/X/blog/newsletter/podcast leads, model-training/inference/frontier operations, and applied product/document AI workflows.
- Give each discovery subagent a numeric quota that matches the user's lane target. If the user asks for 200+ items in a lane, the lane assignment must say 200+ and the lane report must account for that target.
- Save every discovery subagent return under `reviews/fanout/` or `reviews/subagents/` before ranking. The lane report must include candidate count, source types searched, date-window method, duplicate clusters, blocked sources, and primary-source verification plan.
- A deterministic collector may normalize, dedupe, fetch, and merge candidates into `sources/candidates.jsonl`, but it cannot be the only evidence that a lane was searched when the user asked for subagents.
- If an accessible X/blog/newsletter/podcast lane cannot meet the requested count, record the exact blocker and ask before backfilling or rendering. Do not silently replace it with low-signal HN rows or adjacent GitHub issues.

Date-window coverage for monthly runs:

- Slice every date-bounded query by week. One query per week of the window is the default; a single whole-window query both times out on paginated sources (arXiv) and collapses coverage onto the most recent items.
- Record `published_at` for every candidate so week coverage is verifiable; the renderer warns when a lane's candidates span fewer than 3 ISO weeks of a monthly window.
- Per-feed soft cap: take at most 15 candidates from any single `source_id`. After a high-value cluster's first members, additional items from the same feed need distinct implementation evidence to justify a slot.
- If a lane cannot cover a week (outage, auth wall, no relevant items), say so explicitly in the lane report instead of letting the gap pass silently.

## Search And Fetch Procedure

Use the most direct available tool in the current Codex session:

- Web search for current news and official pages.
- Direct open/fetch for known URLs.
- `curl` or Python `urllib` only when network is approved and web tools are unavailable.
- `git clone --filter=blob:none` or `git fetch --tags` only for repo inspection, never to execute downloaded code.

Download raw source material into the artifact directory before synthesis:

- Candidate records under `sources/candidates.jsonl`.
- Raw artifact records under `sources/manifest.jsonl`.
- HTML/text snapshots under `sources/raw/` or `sources/`.
- Papers or extracted text under `sources/papers/`.
- Repo checkouts or exported diffs under `repos/`.
- Figures, screenshots, or generated diagrams under `images/`.
- Verification logs under `verification/`.

The run must save at least 20 raw artifacts before synthesis. A compact note file is not a raw artifact. Raw artifacts include full HTML, PDF, extracted full text, release-note HTML/Markdown, changelog fragments, repo diffs, relevant source files, figure images, screenshots, and metadata JSON.

When network is restricted, ask for scoped approval or use user-provided/local files. Do not call the legacy DeepBrief CLI to work around restrictions.

## Candidate Record

Track each candidate with:

```json
{
  "id": "source_slug_or_hash",
  "source_id": "openai_news | arxiv_agents | repo_owner_repo | ...",
  "type": "article | paper | repo_release",
  "title": "...",
  "url": "...",
  "published_at": "...",
  "lane": "papers | repos | company_posts | model_training | applied_product | discourse",
  "discovered_by": "main | subagent:<name> | wave:<n>",
  "dedupe_key": "...",
  "dedupe_cluster": "...",
  "summary": "...",
  "why_candidate": "...",
  "quality_signals": ["primary_source", "repo_available", "credible_author_or_org", "recent", "implementation_detail"],
  "author_check": "verified_org | known_builder | paper_authors_checked | unknown",
  "download_status": "downloaded | pending | degraded | blocked | skipped",
  "raw_artifact_paths": ["sources/raw/example.html"],
  "score": null,
  "rejection_reason": null,
  "verified_at": null
}
```

## Artifact Manifest Record

Track each raw artifact in `sources/manifest.jsonl`:

```json
{
  "candidate_id": "source_slug_or_hash",
  "url": "https://...",
  "artifact_type": "html | pdf | full_text | release_notes | repo_diff | repo_file | figure | screenshot | metadata",
  "local_path": "sources/raw/source_slug.html",
  "bytes": 12345,
  "sha256": "...",
  "fetched_at": "YYYY-MM-DDTHH:MM:SSZ",
  "status": "downloaded | degraded | blocked",
  "selected": false,
  "intended_use": "candidate_screen | selected_source | deep_dive | verification | visual"
}
```

## Ranking Rubric

Score 0-100:

- Relevance to applied AI engineering: 0-30.
- Implementation grounding and source inspectability: 0-25.
- Depth fit for a two-hour brief: 0-20.
- Novelty relative to prior brief memory: 0-15.
- Source quality and inspectability: 0-10.

Penalties:

- Thin model announcement without mechanics: -15 to -30.
- No accessible source text or code: -10 to -25.
- Repeated item already covered: -50 or skip.
- Marketing-only article: -20.
- Discourse-only claim without primary-source backing: -20 or use as lead only.
- Paper with no credible author/source signal, no code/data, and no obvious applied mechanism: -15 to -35.
- Feed padding from the same repo, blog, or arXiv query after the first high-value cluster member: -10 to -30 unless each item has distinct implementation evidence.

For papers, check at least one of arXiv metadata, project page, repository, Semantic Scholar-style citation/author signals when available, or an institutional/author homepage. Favor papers that provide code, datasets, benchmarks, reproducible eval harnesses, or direct product implications. Do not select a random dissertation or low-signal preprint only because it is recent.

## Repo Inspection Rules

- Inspect the release diff or explicit PR/commit range first.
- Expand to repository-level context only when needed to understand entry points, state, prompts, data flow, sandbox behavior, or runtime mechanics.
- Use read-only commands: `git log`, `git show`, `git diff`, `git grep`, `rg`, `sed -n`, `find`, `ls`, `cat`, `wc`, `pwd`.
- Cite exact paths and lines.
- If line numbers move after checkout, refresh citations before rendering.
- Never execute downloaded repository code, install dependencies in downloaded repos, or write into downloaded repos.

## Visual Assets

- Prefer real figures from arXiv HTML or official docs when licensing/attribution is clear.
- For repo releases, prefer generated Mermaid diagrams based on verified control/data flow plus screenshots or source figures when available.
- Save downloaded images under `images/` and cite source URLs.
- Every PDF must contain at least one visual asset.
- Mermaid satisfies the diagram requirement but does not count as a downloaded source figure. If no source visual is available or permitted, document why in Errata.
- Do not use an unreadable full PDF page as the primary visual. Crop to the relevant figure/table or add an annotation/callout in the caption that explains why the reader should inspect it.
