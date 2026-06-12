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
  "summary": "...",
  "why_candidate": "...",
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
