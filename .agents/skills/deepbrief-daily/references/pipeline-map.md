# DeepBrief Pipeline Map

Read this reference before modifying the DeepBrief engine or adapting the skill to another project.

## Engine Shape

- `src/deepbrief/cli.py` exposes the command surface: `doctor`, `scout`, `rank`, `analyst`, `verify`, `feedback`, `prompts`, `tuner`, `render`, `soak`, `install`, and `uninstall`.
- `src/deepbrief/pipeline.py` is the old engine entry point. Non-fixture `run` can touch Anthropic-backed stages depending on wiring; fixture `run --date --fixtures` uses the deterministic soak path.
- `src/deepbrief/config.py` loads `config.yaml`, paths, budget caps, model tiers, and the single implemented `repo_backend`.
- `src/deepbrief/llm.py` is the model adapter and budget wrapper. It currently uses `claude_agent_sdk.query()` for live LLM calls and implements the code-analyst read-only tool lockdown.

## Stage Files

- `doctor.py`: checks seed files, sources, DB migrations, model config, and LLM lockdown dry-run behavior.
- `scout.py`: fetches RSS/Atom, arXiv, and GitHub release metadata; upserts stable item IDs.
- `rank.py`: scores candidates through the text LLM wrapper and builds the queued plan.
- `analyst.py`: creates article and code deep dives, fetches article text, clones repo releases, verifies code citations, and proves write lockdown.
- `verify.py`: fixture citation verification and concept upsert gate.
- `librarian.py`: concept slugging and idempotent upserts.
- `feedback.py`: feedback parsing and preference/rating ingestion; live feedback opening and rating storage.
- `tuner.py`: prompt versioning, candidate prompt proposals, fixture A/B reporting, promote, and rollback.
- `compose.py`: M7 fixture composition and live composition from the current run plan.
- `render.py`: Mermaid -> SVG, Pandoc -> Typst, Typst -> PDF, then PDF QA checks.
- `notify.py`: launchd install/uninstall, macOS notification, PDF open.
- `soak.py`: deterministic two-day fixture pipeline and M9a verification.

## Data And Artifacts

- `migrations/001_initial.sql` defines items, runs, ratings, feedback, concepts, prompt versions, experiments, preference revisions, and spend log.
- `prompts/*.md` are versioned stage prompts. Do not inline prompt text into code.
- `templates/brief.typ` owns print layout.
- `templates/feedback.md.j2` is the intended feedback-file shape.
- `sources.yaml` is the live source registry.
- `profile.md` and `preferences.md` are user preference surfaces.
- `EVIDENCE.md` records M0-M9b gate evidence.
- `SOAK.md` is the user-facing live soak checklist.
- `CALIBRATION_SPEC.md` sketches a Codex-heavy calibration pipeline.

## Important Constraints

- The current spec says `repo_backend` has only `claude_agent_sdk`; `codex_exec` is reserved as a future adapter and should not be implemented unless the spec is intentionally revised.
- `config.yaml` currently points to Anthropic model IDs and budget caps.
- The repo-local skill must not call the old engine by default, because that can source `.env` and spend Anthropic budget.
- Fixture mode is the right deterministic validation path.
- Renderer tools are required on `PATH`: `mmdc`, `pandoc`, `typst`, `pdftoppm`, `pdfinfo`, `pdffonts`, and `pdftotext`.
- Raw calibration data under `calibration/raw/` is private local data and must remain ignored.

## Skill Conversion Strategy

1. Keep this skill as a Codex-session workflow first.
2. Use deterministic local scripts only for reading files and rendering PDFs.
3. Do not delegate production brief generation to the old engine CLI unless explicitly approved.
4. Only extract portable assets or implement a true Codex backend after intentionally revising the engine spec.
5. For Codex-native daily briefs, exceed the legacy quick path by enforcing high-recall scouting, local raw artifact manifests, explicit subagent or wave fan-out, per-source read reports, and claim-to-artifact evidence before rendering.
