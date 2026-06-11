# Code Deep Dive Prompt

Analyze only the release diff or explicit scope provided by the orchestrator, not the whole
repository.

Produce `deepdive.md` using exactly the headings from `DEEPBRIEF_SPEC.md` section 8. For the
walkthrough, include a file-by-file trace table with `step | file:line | what happens`, where
state is stored, short injected-prompt excerpts with `file:line` when prompts are involved,
and one Mermaid sequence or flow diagram.

Use only read-only repository inspection. Do not write files, edit files, fetch network
resources, spawn subagents, or ask for permissions.

Immutable requirements: keep the section 8 headings unchanged, preserve citation and
verification requirements, preserve the code-analyst permission lockdown, and respect all
budget instructions.
