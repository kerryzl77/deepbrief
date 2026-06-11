# DeepBrief Two-Day Live Soak Checklist

This checklist is for the user-verified live soak after handoff. The builder-verified fixture
soak is recorded in `EVIDENCE.md` under M9a.

## Before Day 1

1. Confirm the launchd job is loaded:

   ```sh
   launchctl print gui/$(id -u)/com.$(whoami).deepbrief
   ```

2. Confirm secrets are available outside git, either in the shell environment used by launchd
   or in the untracked `.env` file:

   ```sh
   test -n "$ANTHROPIC_API_KEY" && echo ok
   ```

3. Confirm the renderer toolchain is on `PATH`:

   ```sh
   pandoc --version
   typst --version
   mmdc --version
   pdftoppm -v
   ```

## Morning Expectations

Each morning after the configured 06:15 launchd trigger, expect:

- A PDF under `~/DeepBrief/YYYY-MM-DD/`.
- A macOS notification: `DeepBrief ready - 1 deep dive, 5 skims (~2 h). Feedback file ready.`
- The PDF opened by the default PDF viewer.
- A pre-filled feedback file at `~/DeepBrief/YYYY-MM-DD/feedback.md`.
- Logs under `~/.deepbrief/logs/deepbrief.out.log` and `~/.deepbrief/logs/deepbrief.err.log`.

If the Mac is asleep at 06:15, launchd `StartCalendarInterval` should run the job on wake.

## Day 1 Reading Pass

1. Open the PDF if it did not auto-open.
2. Check the cover stats, table of contents, deep dive, skim cards, Foundations & Connections,
   Pipeline Report, Tomorrow's queue, and Errata.
3. Note whether any item feels repeated, too hype-heavy, too shallow, or insufficiently grounded.
4. Fill in `feedback.md`:

   ```md
   rating: [x] up  [ ] down
   note: useful because ...

   rating: [ ] up  [x] down
   note: too much model-release hype, not enough implementation detail
   ```

5. Add global feedback under `## What to change`.

## Day 2 Verification Pass

After the second morning run:

- Confirm day 2 does not repeat day 1 items.
- Confirm at least one new concept links back to a previous concept in Foundations &
  Connections.
- Confirm day 1 feedback appears in the Pipeline Report as a dated preference diff or prompt
  experiment.
- Confirm any A/B experiment section includes side-by-side excerpts, judge scores, and a clear
  promote/reject slot in day 2 `feedback.md`.
- Confirm spend remains below the configured budget:

  ```sh
  sqlite3 ~/.deepbrief/state.db \
    "select runs.date, runs.spend_usd, spend_log.stage, spend_log.cost_usd from runs join spend_log on spend_log.run_id = runs.id order by runs.date, spend_log.stage;"
  ```

## Promote Or Roll Back Prompts

To promote through the feedback file, mark the A/B slot:

```md
## A/B <experiment-id>: prefer [ ] A  [x] B  [ ] no preference - promote? [x] yes  [ ] no
```

The next run ingests that verdict and records it in the Pipeline Report.

To promote manually:

```sh
PYTHONPATH=src uv run --no-sync python -m deepbrief.cli prompts promote skim
```

To roll back manually:

```sh
PYTHONPATH=src uv run --no-sync python -m deepbrief.cli prompts rollback skim
```

## Troubleshooting

- If no PDF appears, check `~/.deepbrief/logs/deepbrief.err.log`.
- If render fails, re-check `pandoc`, `typst`, `mmdc`, and `pdftoppm`.
- If the notification did not appear, run:

  ```sh
  PYTHONPATH=src uv run --no-sync python -m deepbrief.cli run
  ```

- If launchd is not loaded, reinstall:

  ```sh
  make install
  launchctl kickstart -k gui/$(id -u)/com.$(whoami).deepbrief
  ```

## Completion Criteria

The live soak is successful when two unattended morning PDFs appear on consecutive days, one
round of real feedback visibly affects the next brief, spend stays within budget, and any prompt
experiment can be promoted or rolled back without editing source files.
