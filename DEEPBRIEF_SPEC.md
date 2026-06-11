# DeepBrief Build Specification

## 1. GOAL

Build **DeepBrief**: a fully automated, self-improving learning pipeline that runs on the
user's Mac every morning and, with zero interaction:

1. Ingests yesterday's user feedback.
2. Scans the AI/agents landscape (lab blogs, arXiv, repo feature releases).
3. Produces one rigorous deep dive plus skim cards for the rest.
4. Compiles everything into a single print-quality PDF.
5. Notifies the user.
6. In the background, tunes its own prompts from accumulated feedback, runs A/B experiments,
   and reports results back inside the PDF.

The only daily interaction the user has is reading the PDF and (optionally) filling a short
feedback file.

## 2. DEFINITION OF DONE

**Part A — builder-verifiable (this is what completes the Goal):**
- Every milestone gate M0–M9b in §14 passes, with command + output evidence in `EVIDENCE.md`.
- The simulated two-day soak (M9a, fixtures + date override) demonstrates: day-2 brief contains
  zero repeated items; day-2 explicitly links at least one new concept to a day-1 concept;
  scripted negative day-1 feedback produces (a) a dated diff in `preferences.md`, (b) changed
  ranking/skim behavior or a candidate prompt proposal, and (c) an A/B section in the day-2 PDF
  with side-by-side excerpts, judge scores, and a promote/reject slot in the feedback file.
- Prompt promotion and rollback both work, via feedback file and via CLI.
- Per-run spend ≤ configured budget; spend logged per stage per run.
- `make install` loads the launchd job and a kickstarted run completes end to end (M8).

**Part B — user-verified after handoff (not gated on wall-clock time):**
- A real two-day live soak per the shipped `SOAK.md` checklist: morning PDF + notification
  appear unattended on consecutive days, and one round of real feedback visibly affects the
  next brief. The builder's responsibility is to ship `SOAK.md` and leave the system installed;
  executing the live soak belongs to the user.

## 3. USER & PEDAGOGY (context — do not gold-plate)

Single user: an applied AI engineer with a ~2 h/day reading budget. Every deep dive must
deliver three layers, in this order:

1. **Mental model** — what it is, why it exists, the 3–5 load-bearing ideas.
2. **Pseudocode** — the core mechanism reduced to 30–80 lines of language-agnostic pseudocode.
3. **Grounded walkthrough** — for code: an end-to-end trace through real files (entry points →
   call/data flow → where state is stored → which prompts are injected); for papers/posts: a
   rebuild-from-scratch plan plus a 30–60 minute prototype exercise.

## 4. HARD REQUIREMENTS

- **R1 — PDF quality.** One PDF per day, typeset quality: cover page with date and stats,
  linked table of contents, syntax-highlighted code, rendered math (LaTeX source), at least one
  vector diagram in the deep dive, page numbers, consistent typography. Target 12–25 pages.
- **R2 — Source types.** Lab/engineering blog posts, arXiv papers, and repo feature releases
  are all first-class.
- **R3 — Grounded code dives.** Every cited file path and symbol is mechanically verified
  against the actual checkout (grep), not vibes. A failed citation triggers one revision loop;
  if still failing, the claim is struck and logged in the errata.
- **R4 — Memory.** SQLite-backed. Never resurface a covered item. The concept graph grows
  daily. User preferences persist and compound across runs.
- **R5 — Daily feedback channel.** Per-item ratings plus free text, ingested at the start of
  the next run. Zero friction: a pre-templated file plus a one-line CLI. Skipped or partial
  feedback never blocks the pipeline.
- **R6 — Self-improvement.** A background tuner proposes bounded prompt revisions from
  feedback; an offline A/B replay harness with an LLM judge evaluates them; results are
  reported in the PDF; promotion is human-gated by default (configurable auto-promote); full
  version history with one-command rollback.
- **R7 — Local + unattended.** Scheduled via launchd. If the Mac is asleep at trigger time, the
  run fires on wake (`StartCalendarInterval` semantics — rely on it, do not reinvent catch-up
  logic). Unattended also means the agent stages must never block on a permission prompt.
- **R8 — Budget guardrails.** Per-run USD cap (default 3.00; tuner/replay activity has its own
  sub-budget, default 1.50, and only spends when an experiment is active). Model tiering per
  stage. Spend logged per stage. Enforced at the call wrapper (§5), not by convention.
- **R9 — Graceful degradation.** A failed stage never kills the brief. Ship whatever succeeded
  plus an honest errata box. Per-source fetch failures are logged and skipped. A budget-stopped
  call is handled like any other stage failure.
- **R10 — Prompts as versioned artifacts.** Every agent prompt lives in `prompts/` as a file;
  the active version per stage is tracked in the DB. No inline prompt strings anywhere in code.

## 5. FIXED DECISIONS — do not relitigate

- **Language/env:** Python 3.12 managed with `uv`. CLI entry point `deepbrief`.
- **Engine: Claude Agent SDK** (`pip install claude-agent-sdk`, Python ≥ 3.10; the Claude Code
  CLI is bundled inside the wheel — no separate install). Every LLM stage (rank, skim,
  signal-extract, article-analyst, code-analyst, tuner, judge, librarian) is one `query()` call
  with its own `ClaudeAgentOptions`: a per-stage system prompt loaded from `prompts/`, an
  explicit tool configuration, and `cwd` where relevant. Pipeline control flow is plain
  deterministic Python between calls — no handoffs, no framework graph. Text-only stages
  (rank, signal-extract, tuner, judge) run with no tools approved; use the SDK's
  structured-output support for plan JSON and extracted signals.
  *Rationale (recorded, not for debate): least-glue path to a local, cwd-pinned read/grep/bash
  agent loop inside one Python orchestration model.*
- **Call wrapper and adapter seam:** every model call goes through `src/deepbrief/llm.py`,
  which exposes `run_text_stage(...)` and `run_repo_stage(...)`. The wrapper selects the model
  tier, sets per-stage `max_budget_usd` from config, logs `ResultMessage.total_cost_usd` and
  per-model usage to the spend log, enforces the run-level cap by summation, and handles the
  `error_max_budget_usd` result subtype gracefully (R9). Config key `repo_backend` is an enum
  whose only implemented v1 value is `claude_agent_sdk`; `codex_exec` is **reserved as a future
  adapter and must not be implemented now** — just keep the seam clean enough that adding it
  later would not require touching stage logic.
- **Repo deep dives use the same engine, locked down.** Important: `allowed_tools` only
  *pre-approves* listed tools — it does not remove unlisted tools from the toolset, so it is
  not a sandbox by itself. The code-analyst `query()` must therefore set, together:
  - `cwd` pinned to the cached checkout;
  - `permission_mode="dontAsk"` — anything not pre-approved is denied instead of prompting
    (required for unattended runs); never `bypassPermissions`;
  - `allowed_tools=["Read", "Grep", "Glob", "Bash"]`;
  - `disallowed_tools` explicitly naming `Write`, `Edit`, `NotebookEdit`, `WebFetch`,
    `WebSearch`, `Task`, and every other mutating or network tool present in the installed SDK
    version (enumerate at build time);
  - a `PreToolUse` hook that denies any Bash command outside a read-only allowlist
    (`git log`, `git diff`, `git show`, `git grep`, `rg`, `grep`, `sed -n`, `awk`, `head`,
    `tail`, `find`, `ls`, `cat`, `wc`, `pwd`) — note that the `can_use_tool` callback is
    skipped in `dontAsk` mode, so command-level gating must live in a hook, not the callback.
  The analyst writes nothing itself; the orchestrator captures its structured output and writes
  `deepdive.md` into the artifacts directory. Verify exact option, mode, and hook names against
  the current SDK permissions guide at build time (§15).
- **Models:** defined only in `config.yaml` — `fast` tier for scout-ranking, skims, signal
  extraction, and judging; `deep` tier for deep dives and the tuner. Look up current model
  names in the Anthropic docs at build time; never hardcode model IDs in source code. Replays
  must use the same tier as the production stage they test, or the comparison is invalid.
- **Deterministic ingestion:** `feedparser`/HTTP for blogs, GitHub REST (Releases + CHANGELOG)
  for repos, the arXiv API for papers. LLMs rank and analyze; they do not crawl.
- **Renderer:** content stages emit Markdown (CommonMark + LaTeX math + ```mermaid fences) →
  `mmdc` renders Mermaid to SVG → `pandoc` converts Markdown to Typst → `typst compile` with
  `templates/brief.typ`. Content agents never touch layout; the template owns typography.
- **Scheduler:** launchd user agent (default 06:15), plist templated by `make install`;
  completion notification via `osascript`; optional auto-open of the PDF.
- **Storage:** SQLite at `~/.deepbrief/state.db`; daily artifacts under
  `~/DeepBrief/<YYYY-MM-DD>/`; repo checkouts cached under `~/.deepbrief/repos/<owner>__<repo>/`.

## 6. DEGREES OF FREEDOM

Internal module boundaries; exact rubric wording; Typst template aesthetics (within R1);
retry/backoff strategy; choice of HTML-readability extraction library; judge rubric details.
When uncertain, pick the boring option.

## 7. RUN MODES AND DAILY PIPELINE

**Run modes:**
- `deepbrief run` — live mode (default): real feeds, real clock.
- `deepbrief run --date YYYY-MM-DD --fixtures tests/fixtures/<day>` — fixture mode: the
  injected date overrides the clock everywhere, and all network ingestion reads frozen payloads
  from the fixtures directory instead of the network. LLM calls remain live. Fixture mode makes
  the no-repeat guarantee, concept-graph growth, feedback loop, A/B harness, and render
  post-checks deterministic and testable.

**Daily pipeline — stage contracts (these contracts are the spec; keep them stable so stages
are testable in isolation):**

0. **doctor** — verify binaries (`git`, `pandoc` ≥ 3.1, `typst`, `mmdc`, `sqlite3`), env keys
   (`ANTHROPIC_API_KEY`, optional `GITHUB_TOKEN`), disk space, and a trivial SDK smoke query.
   Fail fast with an actionable message.
1. **feedback-ingest** — parse yesterday's `feedback.md` plus any `deepbrief rate` rows.
   Per-item ratings → `ratings`. Free text → an LLM signal-extraction pass producing structured
   signals (topic preferences, format preferences, depth preferences, A/B verdicts,
   promote/reject decisions). Apply: update `preferences.md` (append distilled, dated bullets;
   when the file exceeds ~40 bullets, run a curation pass that merges and prunes, archiving the
   prior version), record experiment verdicts, enqueue the tuner if signals warrant a prompt
   change. Parsing is forgiving: blank, partial, or malformed input is logged and skipped,
   never fatal.
2. **scout** — for each source in `sources.yaml`, fetch items new since last seen. Normalize
   and upsert into `items`. Idempotent: a rerun on the same day adds zero duplicates.
3. **rank** — LLM-score unscored items 0–100 against `profile.md` + `preferences.md`, each with
   a two-line justification. Apply ratings history as ± modifiers. On Mondays, rebuild the
   weekly shortlist (≤ 7 items marked `queued`). Every day, select `deep_target` = the top
   queued unprocessed item, plus 4–6 skim items.
4. **analyst** —
   - *Article/paper path:* fetch full text (readability extraction; for arXiv prefer the HTML
     version, fall back to PDF text; embed 1–2 key figures from the arXiv HTML where available,
     with attribution and link, else generate an original diagram). Produce `deepdive.md` per
     the §8 schema.
   - *Code path:* shallow-clone or pull the repo; scope = the diff between the previous and new
     release tag (or the PRs referenced in the relevant CHANGELOG entry) — never "analyze the
     whole repo." Run the code-analyst `query()` inside the checkout (per the §5 lockdown) with
     the active code-dive prompt to produce: a file-by-file trace table
     (`step | file:line | what happens`), where state is stored, verbatim injected-prompt
     excerpts (short, each with `file:line`), and a Mermaid sequence/flow diagram.
   - *Skims:* 120–180-word cards — what changed / why it matters / read-or-skip verdict.
   - *Live A/B variant (config `ab_live_variant`, default `skims_only`):* when an experiment is
     active for the skim stage, generate one designated skim with both the active and candidate
     prompt, labeled A/B in the PDF. Live deep-dive variants are off by default (cost); the
     replay harness covers them.
5. **verify** — mechanical pass: grep-check 100% of cited paths and ≥ 90% of cited symbols
   against the checkout; locate article quotes in the fetched text; lint the §8 schema. One
   revision loop on failure, then strike-and-log. Emit `verification.json` with pass rates.
6. **librarian** — extract 3–7 concepts; upsert concepts and edges (`builds_on` / `related` /
   `prereq`); attach 1–2 canonical references per *new* concept (official docs > papers >
   blogs); produce the "Foundations & Connections" section: prerequisite primers (e.g. a
   sandboxing item links out to OS process/isolation fundamentals) and dated links to
   previously covered items.
7. **tuner** (background, conditional) — runs only when enqueued by feedback-ingest and no
   experiment is already open for that stage. Read the last 7 days of feedback plus the active
   prompt → propose **one** bounded candidate revision (≤ 30% of lines changed; the §8
   headings, verification requirements, and budget instructions are immutable invariants) with
   a written rationale → store as a `candidate` row in `prompt_versions` → open an
   `experiments` row → **offline replay:** run candidate vs. active on 3 frozen past inputs →
   the judge agent scores each pair on relevance, depth-fit, clarity, and groundedness against
   a rubric derived from `preferences.md` → store scores.
8. **compose** — assemble `brief.md` in fixed order: Cover + stats → ToC → Today's Deep Dive →
   Skim Cards → Foundations & Connections → Concept-graph delta (Mermaid) → **Pipeline Report**
   (preference diffs applied today, open experiments, A/B side-by-side excerpts with judge
   scores, and "to promote, mark the slot in today's feedback file") → Tomorrow's queue →
   Errata (if any). Also write tomorrow's pre-filled `feedback.md` from the template.
9. **render** — Mermaid → SVG, pandoc → Typst, compile to `brief.pdf`. Post-checks: nonzero
   size, 8–30 pages, all SVGs embedded.
10. **notify** — `osascript` notification: "DeepBrief ready — 1 deep dive, 5 skims (~2 h).
    Feedback file ready." Optionally `open` the PDF.

## 8. DEEPDIVE.MD SCHEMA — exact headings; verifier and composer depend on them; the tuner may never alter them

```
# <title>
## TL;DR                      (≤ 5 bullets)
## Mental model
## Pseudocode                  (one block, 30–80 lines)
## Walkthrough                 (code: file-by-file trace table; paper/post: rebuild-from-scratch plan)
## What prompts are injected   (code path only, when applicable)
## Try it yourself             (30–60 min prototype exercise)
## Open questions
## Sources & citations         (urls / file:line list)
```

## 9. FEEDBACK CHANNEL — R5 details

- Each run writes `~/DeepBrief/<date>/feedback.md`, pre-filled: one block per item
  (`rating: [ ] up  [ ] down`, `note:`), a global `## What to change` free-text section, and —
  when an experiment awaits a verdict —
  `## A/B <experiment-id>: prefer [ ] A  [ ] B  [ ] no preference — promote? [ ] yes  [ ] no`.
- Item IDs are printed in the PDF next to each item so ratings are unambiguous.
- CLI: `deepbrief feedback` (opens today's file in `$EDITOR`) and
  `deepbrief rate <item-id> up|down ["note"]`.
- Ingest tolerates anything: blank file, half-filled checkboxes, prose-only. Unparseable lines
  are logged, never fatal.

## 10. SELF-IMPROVEMENT RULES — R6 details

- `prompt_versions(stage, version, parent_version, content_hash, status:
  active|candidate|retired, rationale, created_at)`. Active prompt content is materialized to
  `prompts/` so it is always human-readable and diffable.
- One open experiment per stage at a time. Lifecycle: `proposed → replayed → reported → verdict
  → promoted|rejected`. No verdict after 5 calendar days → auto-rejected (logged).
- Promotion paths: the feedback-file checkbox or `deepbrief prompts promote <stage>`. Rollback:
  `deepbrief prompts rollback <stage>` (re-activates the parent version).
- `config.auto_promote`: off by default. If enabled, promote only when the judge prefers the
  candidate on ≥ 2 of 3 fixtures AND the next feedback file contains no objection.
- Invariants the tuner can never change: the §8 schema headings, citation/verification
  requirements, budget instructions, and anything governing the §5 permission lockdown.
- Explainability: every applied change appears in the next PDF's Pipeline Report with its
  rationale. The system must never change behavior silently.

## 11. DATA MODEL (SQLite; migrations checked in)

```
items(id, source_id, url, title, type[article|paper|repo_release], published_at,
      discovered_at, hash, status[new|queued|deep_done|skimmed|skipped], score, score_reasons)
runs(id, date, deep_item_id, spend_usd, duration_s, pdf_path, errata)
ratings(item_id, value, note, created_at)
feedback(id, date, raw_text, signals_json, processed_at)
concepts(id, name, slug, summary, created_run_id)
concept_edges(a, b, relation)
item_concepts(item_id, concept_id)
prompt_versions(id, stage, version, parent_version, content_hash, status, rationale, created_at)
experiments(id, stage, version_a, version_b, fixtures_json, judge_scores_json,
            user_verdict, status, created_at, resolved_at)
preference_revisions(id, date, content, diff_summary)
spend_log(run_id, stage, model, cost_usd, input_tokens, output_tokens)
```

## 12. SEED DATA — create these files; verify every URL resolves during M1, replace dead feeds, log substitutions

`sources.yaml` (user-editable):
- Anthropic news + engineering blog
- OpenAI blog/news
- Cursor blog
- Ramp engineering blog
- arXiv API query: cs.CL + cs.AI, keyword filter (agent, tool use, context, retrieval, sandbox,
  code generation), last 7 days
- Repos (Releases + CHANGELOG watch): `openai/codex`, `anthropics/claude-code`,
  `openai/openai-agents-python`, `anthropics/claude-agent-sdk-python`, `e2b-dev/E2B`

`profile.md` (initial interests, user-editable): multi-agent orchestration and harness design;
context engineering (compaction, memory, state); coding-agent internals (Codex, Claude Code);
sandboxing and isolation (E2B, OS-level primitives); evals, LLM-as-judge, code-grounded
arbitration; retrieval and document AI. Penalize: model-release hype, business news, listicles.

`preferences.md`: starts with only the header
`# Learned preferences (machine-maintained — edit freely)`.

`tests/fixtures/`: `day1/` and `day2/` each contain frozen ingestion payloads — RSS/Atom XML,
GitHub Releases JSON, arXiv API XML, and article HTML snapshots — constructed so that day2
overlaps day1 enough to prove deduplication and concept linking. `minirepo/` is a small
vendored git repository with two tags and a deliberate feature diff (including one prompt
template file), used to test the code-dive path and verifier offline.

## 13. REPO LAYOUT

```
deepbrief/
  pyproject.toml  Makefile  config.yaml  sources.yaml  profile.md  preferences.md
  DEEPBRIEF_SPEC.md  EVIDENCE.md  SOAK.md
  src/deepbrief/
    cli.py db.py config.py llm.py feedback.py scout.py rank.py analyst.py
    verify.py librarian.py tuner.py judge.py compose.py render.py notify.py
  prompts/
    rank.md deepdive_article.md deepdive_code.md skim.md
    signal_extract.md tuner.md judge.md librarian.md
  templates/brief.typ  templates/feedback.md.j2
  launchd/com.USER.deepbrief.plist.j2
  migrations/  tests/  tests/fixtures/{day1,day2,minirepo}/
```

## 14. MILESTONES & ACCEPTANCE GATES — strictly sequential; do not advance until the gate passes; append the command and key output to EVIDENCE.md for each

- **M0 — Scaffold.** Repo layout, uv env, config loading, DB migrations, `llm.py` wrapper with
  budget enforcement stubs. Gate: `make doctor` green.
- **M1 — Scout + rank (live).** Gate: `make scout` against live sources yields ≥ 15 items; an
  immediate rerun adds 0 duplicates; `make rank` emits today's plan JSON (deep target + skims
  with justifications); every seeded source URL verified or substituted with a log entry.
- **M2 — Article deep dive.** Run the analyst on a pinned, stable, well-known engineering post
  about agents (record the exact URL in EVIDENCE.md). Gate: schema lint passes — all §8
  headings present, pseudocode block 30–80 lines, ≥ 3 citations.
- **M3 — Code deep dive + lockdown proof.** Pick a real, recent feature release from a tracked
  repo; pin tags/SHAs in EVIDENCE.md; run the Claude Agent SDK code-analyst path with `cwd`
  pinned to the checkout and the full §5 permission lockdown. Gate: 100% of cited paths exist,
  ≥ 90% of cited symbols grep-confirmed, at least one verbatim injected-prompt excerpt with
  `file:line` if the feature involves prompts, **and** a lockdown test: a planted instruction
  asking the analyst to modify a file in the checkout must be denied, asserted by an unchanged
  `git status`.
- **M4 — Verify + librarian (fixtures).** Deliberately corrupt one citation against
  `tests/fixtures/minirepo` → the verifier catches it and the revision loop fires. Concept
  upserts are idempotent across reruns.
- **M5 — Feedback loop (fixtures).** Generate a feedback template → fill it with a scripted
  negative signal → ingest. Gate: `preferences.md` shows a dated diff recorded in
  `preference_revisions`; ratings measurably shift rank scores.
- **M6 — Tuner + A/B (fixtures).** A scripted signal triggers the tuner → bounded candidate
  produced (diff ≤ 30%, invariants intact, enforced by the prompt-diff bounds checker) →
  replay on 3 frozen fixtures → judge scores stored → Pipeline Report section renders →
  `deepbrief prompts promote` works → `rollback` restores the parent.
- **M7 — Compose + render.** Full PDF from the M2 + M3 + M6 artifacts. Rasterize pages
  (`pdftoppm`) and iterate until: ToC links work, math renders, Mermaid diagrams are crisp at
  print size, no code overflows margins, fonts embedded. Log page count and spend.
- **M8 — Schedule + notify.** `make install` writes and loads the plist; `launchctl kickstart`
  triggers a real end-to-end run; the notification fires; the PDF opens; `make uninstall`
  removes everything cleanly.
- **M9a — Simulated two-day soak (fixtures).** `deepbrief run --date D1 --fixtures
  tests/fixtures/day1` then `--date D2 --fixtures tests/fixtures/day2`, with scripted feedback
  filed between them. Gate: every Part A bullet of §2 holds, verified from the produced
  artifacts and DB state. Then tune the ranking prompt once based on observed results — through
  the experiment mechanism (dogfood it), never by hand-editing the active prompt.
- **M9b — Handoff.** Write `SOAK.md`: a checklist for the user's real two-day live soak
  (what to expect each morning, how to file feedback, how to read the Pipeline Report, how to
  promote/rollback, how to check the spend log). Leave the system installed with the launchd
  job loaded. Gate: `SOAK.md` exists and the install state from M8 is intact.

## 15. BUILDER OPERATING RULES

- Verify current API reality before coding against: the Claude Agent SDK Python reference and
  permissions guide (platform.claude.com/docs/en/agent-sdk/python and
  platform.claude.com/docs/en/agent-sdk/permissions — options, permission modes, hooks,
  structured output, budget options), the GitHub REST API, and the arXiv API. Record every doc
  URL consulted in EVIDENCE.md.
- Smallest dependency set that works. No servers, no Docker, no queues, no LangChain.
- Idempotent runs: re-running a date overwrites that date's artifacts and never duplicates DB
  rows.
- Network failures: per-source try/except — log, mark degraded, continue (R9).
- Use official feeds and APIs only. Never bypass paywalls or auth. If a source blocks fetching,
  mark it degraded and move on.
- Secrets via env/`.env` (gitignored): `ANTHROPIC_API_KEY`, optional `GITHUB_TOKEN`. Never
  committed, never echoed into logs.
- Write tests where they buy stability: schema lint, citation verifier, feedback parser,
  prompt-diff bounds checker, Bash-hook command gating, DB upserts, render post-checks.
- Maintain `EVIDENCE.md` continuously: per milestone — commands run, key output, decisions
  made, deviations from this spec and why.
- Transient blockers (flaky network, a dead feed) get a logged substitution and the work
  continues. A gate that cannot be passed after exhausting reasonable approaches triggers the
  Goal's blocked-stop condition: stop and report the gate, attempts, exact failing output, and
  the input needed. Never skip a gate, weaken a gate, or fabricate evidence.

## 16. OUT OF SCOPE — do not build

Web UI, email delivery, multi-user support, cloud deployment, mobile, vector databases,
RL-style auto-tuning beyond the bounded prompt-revision loop, the `codex_exec` adapter (seam
only), and hosted automation surfaces (Codex cloud automations, Claude Code remote tasks) —
local-first for now; the architecture should not preclude moving the schedule to the cloud
later.
