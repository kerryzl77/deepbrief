# Source Discovery

Use this file when scouting items for a Codex-native DeepBrief.

## Source Classes

1. **Lab and engineering posts**
   - OpenAI news/blog.
   - Anthropic news/engineering.
   - Cursor blog.
   - Ramp engineering.
   - Other official engineering blogs when relevant.

2. **Papers**
   - arXiv `cs.CL`, `cs.AI`, and adjacent systems categories.
   - Prefer HTML when available; fall back to PDF text.
   - Favor papers with code, eval harnesses, memory/state mechanisms, sandboxing, or agent orchestration.

3. **Repo feature releases**
   - `openai/codex`.
   - `openai/openai-agents-python`.
   - `anthropics/claude-code`.
   - `anthropics/claude-agent-sdk-python`.
   - `e2b-dev/E2B`.
   - Other user-requested repos.

## Search And Fetch Procedure

Use the most direct available tool in the current Codex session:

- Web search for current news and official pages.
- Direct open/fetch for known URLs.
- `curl` or Python `urllib` only when network is approved and web tools are unavailable.
- `git clone --filter=blob:none` or `git fetch --tags` only for repo inspection, never to execute downloaded code.

Download all selected source material into the artifact directory when practical:

- HTML/text snapshots under `sources/`.
- Papers or extracted text under `sources/papers/`.
- Repo checkouts or exported diffs under `repos/`.
- Figures, screenshots, or generated diagrams under `images/`.
- Verification logs under `verification/`.

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
  "summary": "...",
  "why_candidate": "..."
}
```

## Ranking Rubric

Score 0-100:

- Relevance to applied AI engineering: 0-30.
- Implementation grounding: 0-25.
- Depth fit for a two-hour brief: 0-20.
- Novelty relative to prior brief memory: 0-15.
- Source quality and inspectability: 0-10.

Penalties:

- Thin model announcement without mechanics: -15 to -30.
- No accessible source text or code: -10 to -25.
- Repeated item already covered: -50 or skip.
- Marketing-only article: -20.

## Repo Inspection Rules

- Inspect the release diff or explicit PR/commit range.
- Do not analyze the entire repository unless the user explicitly asks.
- Use read-only commands: `git log`, `git show`, `git diff`, `git grep`, `rg`, `sed -n`, `find`, `ls`, `cat`, `wc`, `pwd`.
- Cite exact paths and lines.
- If line numbers move after checkout, refresh citations before rendering.

## Visual Assets

- Prefer real figures from arXiv HTML or official docs when licensing/attribution is clear.
- For repo releases, prefer generated Mermaid diagrams based on verified control/data flow.
- Save downloaded images under `images/` and cite source URLs.
- Every PDF must contain at least one visual asset.
