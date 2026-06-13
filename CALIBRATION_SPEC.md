# DeepBrief Cold-Start Calibration Spec

This spec is the local completion contract for M6c. It follows the original Step 4 framework:
intake, filter, distill, mine, optimize, validate, report. The change is the optimization
target: this Goal optimizes only `profile.md`, `preferences.md`, and optionally
`sources.yaml`. The production consumer is `.agents/skills/deepbrief-daily/*`, but those skill
files are read-only for this Goal.

## EXECUTION MODEL

- Worker agents as TOML in `.codex/agents/`: `classifier`, `distiller`, `merger`, `miner`,
  `surface_reviewer`, `judge`, and `reflector`.
- Fan-out is capability-agnostic: first discover what Codex exposes for spawning subagents or
  batch work. Use native subagents if available; otherwise run bounded Codex waves. Every
  worker is idempotent: if a schema-valid output already exists, it exits cleanly.
- All classification, distillation, mining, candidate review, judging, and reflective mutation
  happens in Codex agents. No Anthropic API calls are used. Do not call legacy model
  adapters, the legacy DeepBrief engine, or prompt replay internals.
- Deterministic local code under `calibration/` may parse JSONL/JSON, count records, validate
  schemas, compute hashes, and run regex privacy checks. Judgment steps use agents.
- Optimization bookkeeping lives in `calibration/pool/` and `calibration/frontier_log.json`.
  Candidate pointer-file drafts are never accepted until reviewed by the five rubric-specific
  reviewer agents below.

## PIPELINE

1. **intake** - parse the local raw corpora.
   - ChatGPT source: `calibration/raw/chatgpt/conversations*.json`; current local supply is
     380 conversations.
   - Codex source: `calibration/raw/codex/sessions/**/rollout-*.jsonl`; current local supply
     is 567 rollouts.
   - ChatGPT parser: concatenate split exports, flatten active path from `current_node`,
     compute regenerated/edited sibling count, emit metadata header plus ordered turns.
   - Codex parser: read `session_meta`, preserve cwd/project metadata, fold
     `response_item`/`event_msg` records into turns, and use `history.jsonl` only as an
     index.
   - Spawn an intake-review agent to inspect representative parsed ChatGPT and Codex records
     and confirm user turns are preserved, tool noise is clipped, and metadata is correct.
   - Log per-source totals and date ranges. Verify gitignore coverage for raw/session/rubric
     and pool directories.

2. **filter** - score every conversation.
   - Heuristic prefilter: arxiv.org or github.com URLs; "explain", "how does", "deep dive",
     "walk me through", "from scratch", research/tooling/build prompts, DeepBrief, Codex,
     agents, evals, document AI, retrieval, sandboxing, or coding-agent work.
   - Classifier agents score survivors 0-1 for calibration relevance.
   - Recency weight: <=90 days = 1.0; 91-365 days = 0.6; >365 days = 0.3.
   - Select about 110 ChatGPT and about 30 Codex candidates for distillation, or all usable
     candidates if supply is lower. Do not use Claude traces as calibration records.

3. **distill** - produce session records.
   - Preprocess before any model call: drop event noise, clip tool outputs and large assistant
     payloads to head/tail excerpts, and keep all user turns verbatim.
   - If cleaned transcript still exceeds context, chunk by turn ranges, distill each chunk,
     then spawn a merger agent to combine chunk records. Never first-N/last-N truncate.
   - Distiller agents run `prompts/calibration_distiller.md` verbatim and write
     `calibration/sessions/<source>_<id>.json`.
   - Validator agents check schema validity, scrub quality, and richness. Drop `skip` records
     and richness < 2.
   - Keep up to 80 ChatGPT + 20 Codex records. If fewer than 20 usable Codex records survive,
     backfill from ChatGPT and mark Codex-derived repo/code preferences thin.
   - Record the 80/20 stratified train/holdout split in `calibration/split.json`.

4. **mine** - mine train records only.
   - Miner agents produce `calibration/preference_table.json`.
   - Each preference entry includes: statement, target surface (`profile.md`,
     `preferences.md`, or `sources.yaml`), weighted_support, source_session_ids, confidence,
     conflicts_with, thin flag, and rationale.
   - Encode nothing with weighted_support < 3 unless high-confidence and flagged thin.
   - Preference-level evidence must come from richness >= 3 records.
   - Repo/code deep-dive preferences need weighted_support >= 2 within Codex records; below
     that they remain thin/candidate bullets in `preferences.md`, not hard profile claims.
   - Surface conflicts explicitly; never average them away. Cap profile interest areas at 10.
   - Emit `calibration/rubrics/`: rubric clusters with anchor quotes for owner fit, evidence
     support, conflict/thin evidence, source mix, and skill-consumer alignment.

5. **optimize** - GEPA-style pointer-surface loop in Codex agents.
   - **Pool:** current `profile.md`, `preferences.md`, and optionally `sources.yaml`, plus one
     straightforward rewrite-from-table candidate for each touched surface.
   - **Execute:** no Claude generation. Spawn evaluator agents that read the candidate
     pointer files, the mined preference table, relevant train records, and the skill consumer
     contract in `.agents/skills/deepbrief-daily/*` only as read-only context.
   - **Evaluate:** for each candidate version, spawn five reviewer agents:
     1. owner-fit reviewer,
     2. evidence-support reviewer,
     3. conflict/thin-evidence reviewer,
     4. source-mix reviewer,
     5. skill-consumer/holdout-scope reviewer.
     Each reviewer returns JSON with `rubric`, `score_0_to_5`, `pass`, `reasons`, and
     `blocking_issues`.
   - **Select:** Pareto frontier = candidates that are best on at least one rubric and have no
     blocking issue. A candidate cannot be accepted unless all five hard-pass checks pass.
   - **Mutate:** reflector agents make one targeted revision from reviewer diagnoses. Keep the
     edit scoped to pointer files. Do not edit skill files, legacy prompts, runtime code,
     renderer files, templates, or config.
   - **Stop:** at most 5 generations per touched surface, or 2 generations without frontier
     improvement.
   - **Final pick:** score frontier candidates against holdout rubric clusters only. The
     holdout never enters mining or mutation. Ties go to the shorter, clearer diff.
   - **Apply:** write accepted edits to `profile.md`, `preferences.md`, and optionally
     `sources.yaml`. Remove nothing from `sources.yaml` during cold start.
   - Write all reviewer outputs and candidate decisions to `calibration/review_summary.json`
     and all frontier decisions to `calibration/frontier_log.json`.

6. **validate + freeze**
   - Validator agents check all JSON artifacts, source-session traceability, support
     thresholds, conflict handling, and holdout fit.
   - Privacy audit every file that may be committed with regex checks plus one judge-agent
     scrub pass.
   - Confirm `git status` shows no raw/distilled/rubric/pool data staged.
   - Confirm the diff touches only allowed files.

7. **report**
   - `calibration/CALIBRATION.md` records: final corpus counts, date ranges, train/holdout
     split, preference table summary, conflicts, thin evidence, accepted/rejected candidates,
     five-reviewer scores, holdout fit, privacy audit result, and changed files.
   - Append M6c to `EVIDENCE.md` with C0-C6 evidence.

## GATES

Evidence for each gate is appended to `EVIDENCE.md` under milestone M6c.

- **C0 intake:** parsed ChatGPT and Codex records exist; intake-review agent passes;
  counts/date ranges logged; gitignore verified.
- **C1 filter:** scored candidate lists exist; selection counts logged from the 380 ChatGPT
  and 567 Codex local supplies.
- **C2 distill:** 80 ChatGPT + 20 Codex target met or shortfall/backfill logged; schema
  validation passes; `calibration/split.json` exists.
- **C3 mine:** `calibration/preference_table.json` and `calibration/rubrics/` exist; support,
  richness, repo/code thin-evidence, and conflict rules enforced.
- **C4 optimize:** `calibration/frontier_log.json` and `calibration/review_summary.json`
  show at least one candidate generation or a logged no-change decision; accepted candidate,
  if any, passed all five reviewer rubrics.
- **C5 validate + freeze:** JSON artifacts validate; holdout fit recorded; privacy audit
  clean; only allowed files changed; raw/session/rubric/pool data not staged.
- **C6 report:** `calibration/CALIBRATION.md` complete; `EVIDENCE.md` has M6c.

## CONSTRAINTS

- Touch ONLY: `calibration/`, `.codex/agents/`, `profile.md`, `preferences.md`,
  `sources.yaml`, `prompts/calibration_distiller.md`, `.gitignore`, `CALIBRATION_SPEC.md`,
  and `EVIDENCE.md`.
- Do not edit `.agents/skills/deepbrief-daily/*`; read those files only as the consumer
  contract for `profile.md`, `preferences.md`, and `sources.yaml`.
- Do not edit legacy prompt surfaces, `src/deepbrief/*`, `config.yaml`, renderer files,
  templates, or launchd files.
- Explicitly forbidden: averaging away conflicts; letting richness < 3 records shape hard
  profile claims; showing holdout data to mining or mutation agents; importing tuner.py
  replay internals; using Anthropic/Claude for candidate generation.
- Raw files stay local and uncommitted. Transcript content may enter Codex/OpenAI model
  context for processing. No session content is sent to Anthropic. Every committed artifact
  passes the scrub audit.
