# Codex vs Claude Code Design Summary

Inspected commits:

- OpenAI Codex: `e0cb4ede4e44a371d595520b29d0c80336b8733e`
- Claude Code snapshot: `a371abbe75ffa0d0a3c92290e2bbf56a7ef54367`

## Architecture style

Codex is crate-layered and protocol-centered. Multiple surfaces converge into a Rust session core, and extension systems are integrated through typed managers and protocol surfaces.

Claude Code is product-integrated TypeScript. Bootstrap, UI, QueryEngine, query loop, permissions, storage, and extensions are modular but live in one application graph.

## Control/event model

Codex uses typed protocol submissions and event messages around Session, ActiveTurn, RunningTask, and rollout persistence.

Claude Code uses async generators, AbortControllers, QueryEngine state, queryLoop transitions, queues, AppState tasks, and transcript append semantics.

## Extensibility model

Codex emphasizes MCP, plugins/apps/connectors, skills, dynamic tools, and command hooks with explicit trust/provenance boundaries.

Claude Code has a broader marketplace-style model: plugins can contribute commands, agents, skills, hooks, MCP servers/bundles, output styles, LSP servers, settings, and user config.

## Tool execution and edit model

Codex has ToolRouter/ToolRegistry/runtime layers and a grammar-backed apply_patch tool plus unified exec.

Claude Code uses Zod-backed Tool objects, read-only/concurrency classification, Bash-specific permission analysis, exact Edit/Write tools, and output persistence.

## Sandbox/permission posture

Codex separates approval policy, permission profiles, filesystem/network sandbox, command approvals, MCP approvals, and hook trust.

Claude Code separates settings/managed policy, permission modes/rules, workspace trust, Bash analysis, external sandbox adapter, and interactive permission UX.

## Config ergonomics

Codex config is strongly layered and typed, with project-local deny rules for risky keys. It is easier to reason about as infrastructure.

Claude Code config is more product-expressive, with user/project/local/flag/policy settings, trust staging, managed env filtering, and many feature gates. It is more ergonomic but has more precedence edges.

## Persistence/thread model

Codex uses rollout JSONL as durable replay plus SQLite indexes/stores for threads, logs, goals, memories, agent jobs, and graph state.

Claude Code uses JSONL transcripts, subagent sidechains, sidecars, task output files, caches, debug logs, and cleanup rules, without a visible central local DB in this checkout.

## Developer experience

Codex gives clearer ownership boundaries for runtime work: protocol, session, tasks, tools, config, rollout, plugins. Release and tests are also explicit.

Claude Code gives very rich product affordances in source, but this checkout lacks authoritative package, CI, and release metadata.

## Design tradeoffs

Codex trades some UX immediacy for stronger protocol/runtime separation. That helps with SDKs, app-server integration, rollback, and policy review.

Claude Code trades structural separation for integrated UX and ecosystem breadth. That helps plugins, permission UX, and task notifications, but increases cross-module coupling.

## What Codex can learn from Claude Code

- Richer plugin marketplace affordances, especially scoped enablement and plugin-contributed commands/agents/output styles.
- More explicit exact-edit UX patterns, including stale-read guards and user-facing diff presentation.
- Task notification patterns that make background work visible through normal prompt/query flows.

## What Claude Code can learn from Codex

- Stronger protocol boundary between surfaces and runtime.
- A clearer local state split between replay source and queryable indexes.
- A grammar-backed patch tool for multi-hunk edits instead of only exact replacement/full write semantics.
- More authoritative repository-level build, test, package, and release metadata.

## Residual risks

Both reports are static audits. Codex desktop internals and live sandbox behavior were not exercised. Claude Code packaging/release confidence is degraded by absent manifests and the sourcemap-derived provenance stated in the README.
