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

Do not commit secrets, virtual environments, generated PDFs, or runtime databases.
