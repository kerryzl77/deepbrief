# DeepBrief Self-Improvement Target Prompt

Use this prompt in a fresh Codex window. It is proposal-only by default.

```text
Treat this as a long-running DeepBrief self-improvement objective, not a production brief run and not a one-turn question.

Objective:
Design and evaluate a conservative GEPA-like self-improvement loop for the DeepBrief daily skill at `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily`, using prior Codex traces as red/green evidence. Produce a reviewable proposal and exact candidate patch artifacts. Do not modify durable skill files unless the user explicitly asks you to apply changes after reviewing the proposal.

Default mode is proposal-only. If, in this fresh session, the user explicitly asks to apply the selected fix and open a PR, switch to application/PR mode: implement only the approved fix, run the frozen validation checks, create a focused branch, commit only the approved files, push to the configured remote, open a PR, and include both the PR link and the final proposed-fix summary. Do not include raw trace files or ignored calibration caches in any commit.

If Codex goal mode or goal tools are available in this session, set the goal to the objective above. If not, simulate the goal loop with a visible checklist. Continue until all acceptance criteria are met, or stop only for a concrete blocker.

Non-overridable boundaries:
- Preserve the current Codex-native execution boundary in `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/SKILL.md`.
- Do not run `deepbrief`, `python -m deepbrief.cli`, legacy Make targets, Anthropic/Claude-backed pipeline stages, or `claude_agent_sdk`.
- Do not import `deepbrief.*`, `deepbrief.llm`, or provider SDK paths to make the production pipeline run.
- Do not read `.env`, provider keys, or secrets.
- Do not edit renderer, template, or gate-threshold files to make validation pass, including `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/scripts/render_brief.py` and `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/assets/brief.typ`.
- Do not weaken existing hard subagent, composition, evidence, source-discovery, render-QA, or forbidden-command guardrails.
- Do not claim guaranteed general improvement. You may only claim monotonic improvement on the fixed scorecard and traces actually evaluated.
- Do not read, copy, stage, commit, or rely on repo-local raw trace caches under `/Users/liuzikai/Documents/GitHub/deepbrief/calibration/raw/codex/sessions/`. If that directory exists, report it as ignored local cache only. The authoritative raw trace inputs are the external absolute `/Users/liuzikai/.codex/sessions/...` paths listed below.

Required first reads:
1. `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/SKILL.md`
2. `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/references/codex-native-workflow.md`
3. `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/references/source-discovery.md`
4. `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/references/brief-contract.md`
5. `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/references/pipeline-map.md`
6. `/Users/liuzikai/Documents/GitHub/deepbrief/profile.md`
7. `/Users/liuzikai/Documents/GitHub/deepbrief/preferences.md`
8. `/Users/liuzikai/Desktop/deepbrief_trace_audit.md`
9. `/Users/liuzikai/Desktop/deepbrief_child_traces.csv`

Fixed parent trace set:
Raw Codex session JSONL files are intentionally external evidence inputs and must not be copied into `/Users/liuzikai/Documents/GitHub/deepbrief`. Use these absolute paths directly.
Ignore any similarly named JSONL cache under `/Users/liuzikai/Documents/GitHub/deepbrief/calibration/raw/codex/sessions/`; it is not an authoritative input for this run and must not be staged or committed.

- Train red: `/Users/liuzikai/.codex/sessions/2026/06/11/rollout-2026-06-11T18-00-08-019eb957-ee9d-75e2-b548-8c58e77dc112.jsonl`
- Train red: `/Users/liuzikai/.codex/sessions/2026/06/11/rollout-2026-06-11T19-12-02-019eb999-c350-7460-94d5-a8053f4b765c.jsonl`
- Train green: `/Users/liuzikai/.codex/sessions/2026/06/11/rollout-2026-06-11T20-24-37-019eb9dc-38c2-75e3-a08e-e4c80cceeb1c.jsonl`
- Dev green: `/Users/liuzikai/.codex/sessions/2026/06/13/rollout-2026-06-13T01-22-02-019ec012-dd06-71f2-9739-5eb81ef5dc91.jsonl`
- Dev green: `/Users/liuzikai/.codex/sessions/2026/06/13/rollout-2026-06-13T15-01-08-019ec300-c65b-7223-825e-3d0ecf8469b3.jsonl`
- Holdout green with caution: `/Users/liuzikai/.codex/sessions/2026/06/11/rollout-2026-06-11T23-53-14-019eba9b-3765-75d3-9000-19ac206c48f5.jsonl`

Surviving holdout artifact:
- `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/sixmonth-agent-search-2025-12-12_2026-06-12/brief.pdf`
- `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/sixmonth-agent-search-2025-12-12_2026-06-12/reviews/fanout-report.md`

Use subagents if available and explicitly record each subagent ID, role, input, and output. Spawn distinct lanes for:
- Trace evaluator: reconstruct red/green behavior from parent and child traces.
- Prompt candidate proposer: propose bounded skill/reference changes.
- Guardrail reviewer: check no existing hard guardrail is weakened.
- Semantic judge: score non-machine-verifiable dimensions by running 3 independent judge passes or spawning 3 semantic judge subagents.
- Red-team reviewer: look for overfitting, shortcut behavior, and privacy/security regressions.
If subagents are unavailable, stop before final recommendation and report the missing capability.

Evaluation split and expected behavior:
- `019eb957-ee9d-75e2-b548-8c58e77dc112` is red. A correct future skill should reject or flag this run as shallow even though a PDF rendered.
- `019eb999-c350-7460-94d5-a8053f4b765c` is red. A correct future skill must not count scripted read-workers as source-specific subagents.
- `019eb9dc-38c2-75e3-a08e-e4c80cceeb1c` is train green. Preserve its real source-read fanout and research-gate behavior.
- `019ec012-dd06-71f2-9739-5eb81ef5dc91` and `019ec300-c65b-7223-825e-3d0ecf8469b3` are dev green. Preserve trace-level gates while noting renderer/image-path fragility.
- `019eba9b-3765-75d3-9000-19ac206c48f5` is holdout. Do not inspect holdout details until candidate changes and train/dev scoring rules are frozen.

Pre-candidate freeze:
- Use train traces only for failure reconstruction and candidate proposal.
- Use train/dev traces for candidate selection.
- Before generating candidates, freeze and write `scoring_rules.json`, `trace_expectations.json`, and `baseline_scorecard.json`.
- Freeze the eval schema, trace expectations, judge prompts, judge calibration examples, thresholds, aggregation rule, scalar loss formula, iteration budget, and stop rules before proposing any candidate changes.
- For each candidate change, record `source_trace_id`. A change proposed from one trace must be evaluated against every non-source train/dev trace before it is eligible.

Pre-holdout freeze:
- Do not inspect holdout until `scoring_rules.json`, `trace_expectations.json`, `baseline_scorecard.json`, `candidate_patch.diff`, and `selection_report.md` are frozen and written.
- Holdout may be evaluated once only after candidate selection is complete.

Objective gates:
Hard gates are binary pass/fail and dominate all scores. Any hard-gate failure rejects the candidate regardless of semantic score.
The final-response contract and artifact durability gates apply to evaluated production-brief traces, not to the self-improvement session's final answer.

- Legacy boundary: no legacy DeepBrief/Claude command, import, SDK, or secret read.
- Discovery fanout: discovery subagents exist when requested/high-recall.
- Source-read fanout: one actual source-read child trace per selected deep-read artifact when required; scripted `read-workers` never count.
- Gate discipline: block synthesis/render if required research gates are missing and no explicit degraded-run approval exists.
- Candidate/artifact minimums: monthly/high-recall traces meet required candidate and raw artifact thresholds.
- Evidence discipline: material claims connect to local artifact evidence and public citations.
- Composition provenance: final prose is authored from reports/syntheses, not script-generated templates.
- Renderer discipline: `status: ok` is necessary but insufficient; require visual/citation/text sanity checks.
- Final response contract: final answer reports PDF path, Markdown path, feedback path, candidate log, manifest, fanout report, evidence matrix, selected counts, and residual risks.
- Artifact durability: final artifacts must not live only under `/tmp`; final PDF path must exist after the final answer.
- Raw trace source discipline: authoritative trace reads use `/Users/liuzikai/.codex/sessions/...` only; repo-local raw trace caches are ignored and never staged.

Required deterministic tests:
- `T001_forbidden_boundary_scan`: PASS if no candidate or evaluated trace uses forbidden legacy commands/imports/secrets; FAIL on any forbidden command, import, SDK path, `.env`, provider key, or secret access.
- `T002_holdout_seal_check`: PASS if holdout content is not read before pre-holdout freeze artifacts exist; FAIL if holdout details influence eval rules, candidates, or selection before freeze.
- `T003_required_artifact_check`: PASS if all required eval artifacts are written or explicitly marked unavailable with reason; FAIL if any required artifact is missing without explanation.
- `T004_red_expected_failure_check`: PASS if each red trace fails for its expected reason; FAIL if a red trace passes, fails for an unrelated reason, or is not evaluated.
- `T005_green_invariant_preservation_check`: PASS if every green/dev invariant remains preserved; FAIL on any green/dev regression or unevaluated invariant.
- `T006_source_read_fanout_check`: PASS if real source-read child traces are counted and scripted read-workers are excluded; FAIL on substituted, inferred, or scripted fanout accounting.
- `T007_gate_discipline_check`: PASS if missing research/render gates block or require explicit degraded approval; FAIL if synthesis/render proceeds silently after a required gate is missing.
- `T008_candidate_patch_guardrail_check`: PASS if the candidate does not weaken hard guardrails or edit renderer/template/threshold shortcuts; FAIL on any weakening or shortcut.
- `T009_change_to_regression_test_mapping_check`: PASS if every candidate change has `change_id`, `source_trace_id`, `target_failure_id`, `expected_behavior_delta`, `risk`, `mapped_test_id`, and `rollback_condition`; FAIL if any field or named regression test is missing.
- `T010_final_response_contract_check`: PASS if evaluated production-brief traces report required final paths/counts/risks when observable; FAIL on omitted required final-delivery fields in those traces.
- `T011_raw_trace_source_check`: PASS if all raw trace reads use the listed `/Users/liuzikai/.codex/sessions/...` paths and no `calibration/raw/codex/sessions` file is staged, copied, or treated as authoritative; FAIL on any repo-local raw trace dependency or attempted commit.

Green/dev preservation invariants:
- Green traces must not newly violate the legacy boundary.
- Green traces must preserve real discovery/source-read fanout classification from `/Users/liuzikai/Desktop/deepbrief_child_traces.csv`.
- Green traces must preserve gate ordering: discovery before ranking, raw artifacts before read reports, read reports before synthesis, evidence/citation checks before render.
- Green traces must preserve final artifact/reporting contracts that were observable in their parent traces.
- Dev traces may keep known renderer/image-path fragility as a recorded risk, but candidate changes must not make that fragility worse or treat render success as sufficient QA.

Semantic judges run only after hard gates pass. Use frozen 1-5 rubrics with 1/3/5 calibration examples written before judging starts. Passing threshold is median >= 4 for each dimension and no judge score below 3.

Semantic judge dimensions:
- Contract fidelity.
- Fanout integrity.
- Research depth.
- Evidence quality.
- Composition quality and no repeated boilerplate.
- Reader fit against `/Users/liuzikai/Documents/GitHub/deepbrief/profile.md` and `/Users/liuzikai/Documents/GitHub/deepbrief/preferences.md`.
- Final utility and honesty about residual risks.

Judge disagreement rule:
- Use at least 3 independent judges when subagents are available.
- A dimension is stable only if at least 2 of 3 judges pass it and `max(score) - min(score) <= 1`.
- Any critical-veto finding blocks promotion.
- Unstable dimensions require user adjudication or candidate rejection.

Candidate generation protocol:
- Before generating candidates, freeze the eval schema, trace expectations, scoring formula, judge prompts, thresholds, and iteration budget.
- Treat the skill as a structured agent program, not a single prompt.
- Prefer the smallest bounded clause or reference-file addition that fixes a labeled failure.
- Recommended durable shape: a new reference file at `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/references/self-improvement-loop.md` plus a short routing hook in `/Users/liuzikai/Documents/GitHub/deepbrief/.agents/skills/deepbrief-daily/SKILL.md`.
- Keep production brief behavior unchanged unless the user explicitly approves application.
- Use GEPA-style reflection only over saved trajectories, failures, scores, and actionable side information.
- Use SkillOpt-style bounded edits: add, delete, or replace small clauses; maintain rejected-edit memory.
- Evaluate candidate interactions combinatorially when multiple clauses are proposed. Prefer the smallest set with the same score.

Iteration budget:
- `max_rounds`: 3
- `max_candidate_edits_per_round`: 5
- `max_total_candidate_sets`: 12
- `patience`: stop after 1 round with no train/dev loss improvement.
- Stop immediately on any guardrail weakening or green/dev regression.

Selection threshold:
- A candidate is eligible only if all hard gates pass.
- All green/dev invariants must be preserved.
- At least one targeted red failure must be fixed for the expected reason.
- Every edit must map to a named regression test.
- Semantic dimensions must pass the disagreement rule.

Scalar loss:
Log scalar loss for all candidates; only hard-gate-passing candidates are eligible for selection.
`loss = 1000 * hard_gate_failures + 300 * red_expected_failure_misses + 300 * green_regressions + 100 * missing_required_artifacts + 50 * unmapped_candidate_edits + 25 * final_contract_omissions + semantic_penalty`

Required fields for every proposed change:
- `change_id`
- `source_trace_id`
- `target_failure_id`
- `expected_behavior_delta`
- `risk`
- `mapped_test_id`
- `rollback_condition`

Reject any change that is generic, aesthetic, not tied to a trace failure, not covered by a named regression test, or useful only by weakening a hard guardrail.

Required artifacts to write under `/Users/liuzikai/Documents/GitHub/deepbrief/calibration/runs/deepbrief-daily-gepa-<timestamp>/`:
- `trace_inventory.json`
- `scoring_rules.json`
- `trace_expectations.json`
- `baseline_scorecard.json`
- `objective_results.jsonl`
- `red_green_matrix.md`
- `semantic_judgments.md`
- `candidate_patch.diff`
- `selection_report.md`
- `holdout_report.md`
- `manual_approval_log.md`
- `rejected_edits.md`
- `final_recommendation.md`

Acceptance criteria:
- All required absolute-path inputs were read or explicitly marked missing.
- Eval schema, trace expectations, judge prompts, thresholds, scalar loss, and iteration budget were frozen before candidate generation.
- The train red traces fail for the right reasons.
- The train/dev green traces preserve their passing objective behaviors.
- Holdout is evaluated only once after the candidate, scoring rules, baseline scorecard, and selection report are frozen.
- No hard guardrail is weakened.
- No renderer/template/gate-threshold shortcut is proposed.
- Every proposed change maps to at least one observed failure mode and one regression test.
- Candidate selection follows the scalar loss and selection threshold above.
- Judge disagreements are reported as uncertainty, not smoothed away.
- The final recommendation states exactly what is proven, what is not proven, and what needs user approval before application.
- If application/PR mode was explicitly requested, the final recommendation also includes the focused branch name, commit hash, PR link, validation results, files changed, and final proposed-fix summary.

Final output:
Return a concise executive summary, the exact candidate patch or proposal, the score matrix, the holdout result, rejected alternatives, and residual risks. Do not apply the patch unless the user explicitly asked for application in this fresh session. If application/PR mode was requested, return the actual fix summary, commit, PR link, validation evidence, and any residual risk.
```

Research anchors used to design this prompt:
- GEPA: https://arxiv.org/abs/2507.19457 and https://gepa-ai.github.io/gepa/guides/
- GEPA implementation: https://github.com/gepa-ai/gepa
- MIPRO: https://arxiv.org/abs/2406.11695
- VISTA critique of reflective prompt optimization: https://arxiv.org/abs/2603.18388
- SkillOpt: https://arxiv.org/abs/2605.23904
- Reflexion: https://arxiv.org/abs/2303.11366
- TextGrad: https://arxiv.org/abs/2406.07496
- AFlow: https://arxiv.org/abs/2410.10762
- G-Eval: https://arxiv.org/abs/2303.16634
- MT-Bench LLM-as-judge: https://arxiv.org/abs/2306.05685
- RubricEval: https://arxiv.org/abs/2603.25133
- PROMPTEVALS: https://arxiv.org/abs/2504.14738
- LLM judge reliability: https://arxiv.org/abs/2606.13685
- Codex manual: https://developers.openai.com/codex/codex-manual.md
- Codex subagents: https://developers.openai.com/codex/subagents
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code goals: https://code.claude.com/docs/en/goal
- Dive into Claude Code / OpenClaw: https://arxiv.org/abs/2604.14228
 
