# DeepBrief

This repository is initialized for the DeepBrief build goal.

The controlling implementation spec is [`DEEPBRIEF_SPEC.md`](DEEPBRIEF_SPEC.md). Start a new Codex thread from this repository and paste Part 1 of the DeepBrief brief into `/goal`.

## Environment

DeepBrief uses Python 3.12 managed by `uv`.

Initial setup:

```sh
uv python install 3.12
uv venv --python 3.12
uv sync
```

Current placeholder sanity check before M0:

```sh
uv sync --no-editable
uv run --no-sync deepbrief
```

On this Mac, `/usr/bin/make` is currently blocked until the Xcode license is accepted:

```sh
sudo xcodebuild -license
```

Secrets must be supplied through the environment or an untracked `.env` file:

```sh
ANTHROPIC_API_KEY=...
GITHUB_TOKEN=... # optional
```

Do not commit secrets, virtual environments, working PDFs, or runtime databases. Final PDFs under `results/` are versioned.


## Shared results and two-device workflow

Completed reports are indexed in [results/README.md](results/README.md). Treat the
Git remote as the shared source for code, `preferences.md`, and final results.
Keep a separate clone on each Mac, outside folders managed by another sync service.

Before working on either device, commit or stash local edits and run
`git pull --ff-only`. After completing work, commit the intended files and run
`git push`. If the histories diverge, reconcile the changes before pushing;
do not force-push over work from the other device.

Git transfers committed files only. Local `.env`, virtual environments, caches,
runtime databases, and ignored working artifacts stay device-specific. Install
the environment independently on each Mac. Promote completed reports and their
required images into `results/` before deleting temporary research material.
