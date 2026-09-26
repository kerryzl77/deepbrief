# Daily Applied AI Engineering Must-Read

**July 25, 2026**  
**Estimated reading time: 18 minutes**

Two selections are from the strict last-24-hour window. The paper is a clearly
labeled 7-day fallback because no paper appeared in the strict arXiv cycle.
Today's theme is harness-owned control: protect the transport beneath tools,
put measurement outside the coding agent, and bind user approval to the exact
operation that was shown.

| Rank | Window | Topic | Must-read | Read |
|---:|---|---|---|---:|
| 1 | Last 24h | MCP runtime isolation | [Keep handler subprocesses off the stdio protocol wire](https://github.com/modelcontextprotocol/python-sdk/commit/629ca297d24b24f8055bf191ea7ff046a5c32100) | 6 min |
| 2 | 7-day fallback | Coding-agent optimization | [PerfAgent: profile, verify, repeat, retain the best patch](https://arxiv.org/abs/2607.19653) | 7 min |
| 3 | Last 24h | Tool approval integrity | [Google ADK: bind continuation to the recorded tool call](https://github.com/google/adk-python/commit/4b002c4b56e0b5fa83a0d989ef7663fbedf23211) | 5 min |

## 1. MCP Python SDK: make the protocol pipe private

**Primary source:** [commit 629ca297d24b](https://github.com/modelcontextprotocol/python-sdk/commit/629ca297d24b24f8055bf191ea7ff046a5c32100)

### User and operator mental model

An MCP stdio server is normally a child process launched by an MCP host. The
host sends JSON-RPC to the server's stdin and expects only JSON-RPC on stdout.
Server tools may launch their own subprocesses. Before this patch, those
children inherited the same stdin/stdout: a child could wait on or consume MCP
input, while a child `print()` could insert non-JSON text into the protocol and
make the host drop the server.

After the patch, the MCP SDK keeps the real protocol pipes on private file
descriptors while the server is active. Public fd 0 points to the null device,
so handlers and children see EOF instead of the MCP input stream. Public fd 1
points to stderr, so flushed child output becomes host-collected log output
instead of protocol bytes. The user-visible result should be fewer tool hangs
and fewer servers that suddenly appear disconnected or empty after a child
process writes output.

This is not container or VM isolation. It changes which process capabilities
ordinary inherited stdin/stdout expose. The child still shares the server's
filesystem, environment, network policy, and other open descriptors.

### Implementation mechanism

The SDK registers process-wide claims for fd 0 and fd 1, duplicates each wire
descriptor above the standard range, installs the null/stderr diversions with
`dup2`, serves MCP through the private duplicates, and restores the public
descriptors on exit. POSIX uses `F_DUPFD_CLOEXEC`; Windows also rebinds the
Win32 standard-handle slots because changing the CRT descriptor table alone
does not control what a new process inherits.

The claim is registered before mutation and removed only after successful
restoration. A second concurrent default-stream server is rejected. Failure
paths either use the old in-place behavior or leave the descriptor claimed,
which favors protocol integrity over silently handing a later server the wrong
endpoint.

### Engineering takeaways

- Protect framing at the shared OS boundary, not with instructions to every
  handler author.
- Treat inherited standard descriptors as capabilities available to all
  transitive child processes.
- Test routing with real pipes and real subprocesses; in-memory streams cannot
  prove inheritance, restoration, or child-start behavior.
- Document fd-level fixes as compatibility changes. Code that used fd 0 as a
  parent-liveness signal now sees the null device.

### Limitations and skepticism

The protection is best effort. Explicit or replaced streams skip descriptor
claims; output before server entry still reaches protocol stdout; an unflushed
Python buffer can drain after restoration and corrupt the wire; and noisy child
stdout can block the server if the host never drains stderr. The design also
retains private descriptors to avoid recycling them under blocked worker
threads, so repeated sessions in a long-lived process can consume descriptors.
The patch includes extensive POSIX, Windows, failure-path, and real-subprocess
tests, but this digest inspected the patch and did not run the SDK test suite.

## 2. PerfAgent: the agent proposes stopping; the harness decides

**Primary source:** [arXiv 2607.19653v1](https://arxiv.org/abs/2607.19653)

### Problem statement

A repository optimization patch must be correct and materially faster.
General coding agents often miss bottlenecks inside native extensions, stop
after the first modest speedup, or validate an aggressive patch too narrowly.
That makes "please optimize this repository" a control-loop problem, not just
a code-generation prompt.

### Proposed method

PerfAgent wraps Mini-SWE-Agent in an outer loop with up to five submissions:

1. Run native-aware `py-spy` profiling and condense stacks into hotspots with
   location, call context, self time, total time, and library ownership.
2. Let the coding agent edit and submit a patch.
3. Intercept its stop signal, rebuild, and run change-selected tests through
   `pytest-testmon`.
4. If validation passes, measure speedup and re-profile the changed
   repository. Return the new measurement and hotspots to the agent.
5. Retain the fastest validated checkpoint across all attempts, not the final
   checkpoint.

The mental model is a search controller around the agent:

`profile -> edit -> verify -> measure -> re-profile -> edit again`

The harness owns termination, rollback, evidence, and best-patch selection.
The model owns the next code hypothesis.

### Key evidence

On the paper's GPT-5.1 setup, hack-adjusted expert matching rises from **19.6%
to 39.2%** on GSO and from **26% to 74%** on SWE-efficiency-Lite. The full
profiler-plus-test loop also beats the timing-only, tests-only, and
profiler-only loop variants. On GSO, PerfAgent touches C/C++/Cython/Rust on
48% of tasks versus 31% for the OpenHands baseline.

The best-of-five comparison is useful: PerfAgent reports a 39.2 score at
$2.88 average model cost on GSO versus 26.5 at $11.01 for an oracle-selected
OpenHands best-of-five; on SWE-efficiency-Lite it reports 74 at $4.25 versus
68 at $9.91. These are paper-reported single-run results, not independently
reproduced measurements.

### Applicability

For a Codex/Claude Code-like harness, treat the final answer or stop event as a
checkpoint proposal. Rebuild in a clean sandbox, run impact-selected tests
plus invariant tests, measure in an isolated process, preserve the structured
profile and timing distribution, then either resume with evidence or return
the best release-qualified checkpoint.

That implication is inferred. PerfAgent itself is evaluated as a
Mini-SWE-Agent wrapper. The paper reports a one-shot Codex baseline, but it
does not run the PerfAgent loop around Codex or Claude Code.

### Limitations and skepticism

`pytest-testmon` tracks Python coverage, so the in-loop verifier can miss
native-code regressions. SWE-efficiency-Lite has no hidden performance
workload, and the paper documents 18 timing-loop hacks before changing the
measurement protocol. Results are single-run, no confidence intervals or
exact significance statistics are reported, total profiler/build/test cost is
not fully accounted for, and both benchmarks are Python-centered. The durable
idea is the evidence-driven supervisory loop, not a claim that `py-spy` plus
five retries is a universal optimizer.

### Citation gate

**PASS.** Exact coauthor [Tim Kaler's MIT profile](https://tfk.mit.edu/)
matches the paper's MIT affiliation and systems/optimization publication
cluster. The identity-matched [OpenAlex record](https://openalex.org/A5003285620)
reported **1,574 citations** at collection time, above the hard 1,000-citation
threshold.

## 3. Google ADK: approval is for one recorded operation

**Primary source:** [commit 4b002c4b56e0](https://github.com/google/adk-python/commit/4b002c4b56e0b5fa83a0d989ef7663fbedf23211)  
**Supporting tests:** [commit 65d8ea7d82c7](https://github.com/google/adk-python/commit/65d8ea7d82c76bcefa61a8af2b19612cb750a9b4)

### User and operator mental model

ADK can pause a tool call and ask the user to approve it. The expected flow is:
the model proposes `tool(name, arguments, call_id)`, ADK records it, the UI
shows that operation, the user approves or declines, and a later continuation
resumes the same proposal.

The bug was in the last step. The continuation resolver trusted an
`originalFunctionCall` copied into confirmation history. An attacker able to
inject or alter session events could substitute a different tool or arguments,
then attach a syntactically valid confirmation response. The user's real "yes"
could become authority for an operation the user never saw.

After the patch, valid approvals should feel unchanged. Corrupted or incomplete
history now fails rather than executing. Applications that reconstruct session
history must preserve the original call, agent author, and dynamic-confirmation
metadata.

### Implementation mechanism

Continuation now resolves the call ID against recorded history, checks that the
historical event belongs to the executing agent, resolves the name through the
agent's canonical tool registry, verifies that the tool statically or
dynamically required confirmation, and requires exact historical name and
argument equality. Only then does the normal tool handler receive the
confirmation.

`FunctionTool` and `McpTool` expose a shared asynchronous
`check_require_confirmation` path so validation and execution consult the same
policy. The follow-up patch adds rejection tests for unregistered tools,
non-confirmable tools, and argument tampering.

### Engineering takeaways

- Model an approval response as a scoped grant for an immutable operation, not
  as a Boolean that can accompany a caller-supplied operation.
- Re-resolve the operation through canonical server-side state at use time.
- Bind approval to principal, tool identity, normalized arguments, call ID,
  and policy version.
- Preserve negative tests for every rejection edge; successful confirmation
  fixtures do not prove authorization integrity.

### Limitations and skepticism

The binding still trusts session-history integrity; it adds no signature,
nonce, durable grant object, or authenticated event store. Duplicate call IDs
are not rejected, the historical confirmation-request function name is not
explicitly checked in the resolver, and the supporting tests still do not
cover name substitution, duplicate IDs, or cross-agent histories. The patches
were inspected but the ADK test suite was not run.

## What I would read first

Read the MCP patch's migration note and `stdio_server()` state machine first.
It is a compact example of converting an application convention into an
enforced process boundary while preserving the protocol on private handles.

## What I would prototype or inspect

1. Add a subprocess-inheritance test to one MCP server: launch a child with
   default stdin/stdout, prove stdin is EOF, and prove child output cannot enter
   the JSON-RPC pipe.
2. Wrap one coding-agent optimization task with a two-attempt controller.
   Intercept stop, run a profiler and verifier outside the agent, then resume
   with measured evidence while retaining the best passing patch.
3. Represent tool approval as a server-side record keyed by principal, call ID,
   canonical tool, normalized argument hash, policy version, and expiry. Test
   name substitution, argument substitution, replay, duplicate IDs, and
   cross-agent continuation.

## Audit

Screened **515 distinct candidates**, including **111 strict-window records**.
Registered **46 local source artifacts**; selected **3 stories / 6 source
artifacts**. Three discovery lanes and four source-specific full reads
completed; the extra read documents the rejected IssueTrojanBench near-miss.
**Degraded selected sources: 0.** Paper gate: **PASS** (Tim Kaler, OpenAlex
1,574 citations).

Artifact directory:
`/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-07-25`

