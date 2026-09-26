# Daily Applied AI Engineering Must-Read

**July 21, 2026**  
**Estimated reading time: 18 minutes**

Two sources cleared the strict 24-hour bar. One paper from the 7-day fallback
window was added after a full-text read and an exact-author citation check. No
item repeats routine Codex or Claude Code release-note coverage.

| Rank | Window | Topic | Must-read | Read |
|---:|---|---|---|---:|
| 1 | Last 24h | Sandbox runtime | [E2B: resume from a still-local memory snapshot while dedup continues](https://github.com/e2b-dev/infra/commit/77f25a0de4f5cf6d375349d0afada5bc28109db9) | 6 min |
| 2 | Last 24h | Agent tool transport | [Vercel AI SDK: route Codex host tools through one deterministic CLI relay](https://github.com/vercel/ai/commit/b2f553b994c099308877c6611c9981d18beb8408) | 5 min |
| 3 | 7-day fallback | Repository agents / evals | [DREA: separate repository exploration from vulnerability judgment](https://arxiv.org/abs/2607.13439v1) | 7 min |

## 1. E2B: warm resume no longer waits for memory dedup

**Primary source:** [e2b-dev/infra commit 77f25a0de4f5](https://github.com/e2b-dev/infra/commit/77f25a0de4f5cf6d375349d0afada5bc28109db9)

### User and operator mental model

E2B runs isolated, machine-like sandboxes for agent workloads. Pausing one is
not just saving a Docker image or a writable disk. The runtime captures VM and
device state, a filesystem diff, and memory state. Memory is represented as an
existing base snapshot plus the pages dirtied since that base.

After memory capture, E2B deduplicates and compacts those dirty pages into the
durable object that can be uploaded and resumed on another node. Before this
change, a user who resumed the same sandbox on the same node while that work
was still running could wait for dedup even though the required bytes were
already present in a Linux `memfd` on that node.

With the default-off feature enabled, the experience becomes: pause captures
memory, the local sandbox becomes resumable immediately, and dedup/upload keep
running in the background. The durable snapshot format and uploaded bytes do
not change. This fast path applies only while the origin node still owns the
captured memory; another node still needs the durable representation.

### Implementation mechanism

1. The pause path builds a **provisional local header**. Clean pages still map
   to the durable parent; dirty pages map to a fresh synthetic build ID and to
   their original guest-memory offsets in the still-mapped `memfd`.
2. A `MemfdIdentitySource` makes that synthetic build ID readable only through
   the origin node's local diff store. It has no uploadable path and is not a
   persistent snapshot artifact.
3. Dedup compare builds the real header and a packed-offset index. During
   drain, the cache can translate those packed offsets back to absolute
   `memfd` offsets, so reads remain available before compaction finishes.
4. A compare-and-swap replaces the provisional header with the durable header.
   Temporary store pins and a 30-second grace period prevent the shared
   `memfd` from being reclaimed under active readers; new reads then use the
   compacted cache.
5. Persistence, peer-to-peer serving, and re-pause boundaries wait for the
   durable header. Scheduling uses a non-blocking check and temporarily omits
   memory-affinity metadata rather than leaking the synthetic build ID.

The author reports a forced 15-second dedup stall falling from about **14.9 s**
of resume blocking to about **0.5 s**, versus a roughly **0.66 s** control. This
is a targeted dev-node experiment, not a production latency distribution.

### Engineering takeaways

- Treat a local fast representation and a durable portable representation as
  separate capabilities. A versioned identity can select both the data source
  and its offset interpretation atomically.
- Keep provisional state out of persistence, placement, and peer-serving
  interfaces. Those are correctness boundaries, not serialization details.
- Model handover ownership explicitly: readers, cache pins, swap completion,
  timeout cleanup, and retry behavior all need tests.

### Limitations and skepticism

The path is same-node only and default-off. The patch has strong unit coverage
for offset translation, concurrent reads, header swapping, pinning, and durable
boundaries, but no focused end-to-end `AddSnapshot` handover fixture and no
controlled cross-node test. A read that straddles provisional release relies
on userfaultfd retry, and a missing swap signal can retain guest-sized memory
for up to 30 seconds.

## 2. Vercel AI SDK: Codex host tools use one CLI relay

**Primary source:** [vercel/ai commit b2f553b994c0](https://github.com/vercel/ai/commit/b2f553b994c099308877c6611c9981d18beb8408)

### User and builder mental model

`@ai-sdk/harness-codex` lets an application run a Codex agent behind Vercel's
shared harness protocol. A **host tool** is supplied and executed by that
application, such as `get_weather`; it is different from a tool already owned
and executed by Codex or an MCP provider.

The adapter previously exposed the same host capability through two routes:
an MCP stdio server and an existing harness CLI relay. Under Codex
`--experimental-json`, the patch says some versions did not expose those MCP
tools to the model, while others exposed tool names but lost normal arguments.
That creates an end-to-end failure even when the MCP handshake itself appears
healthy.

After this patch, a Codex agent is guided to invoke a per-session CLI shim. The
shim calls an authorized loopback relay; the relay emits a harness tool call,
waits for the application to execute it, and returns the result to Codex as
command output. Provider-native MCP tools remain MCP tools, but they no longer
compete for ownership of application host tools.

### Implementation mechanism

The bridge keeps its existing prompt guidance, shim writer, command filter,
and loopback relay. It deletes the `harness-tools` MCP server, removes its MCP
configuration and special event-authorization branch, and prunes the MCP/Zod
dependency surface. Every remaining Codex `mcp_tool_call` is now classified as
provider-executed; host-tool lifecycle events come from the relay path.

The focused regression test verifies that a turn with host tools supplies no
`mcp_servers` configuration. Packaging tests verify that the deleted MCP asset
and bootstrap argument are gone. The relay binds to `127.0.0.1` on an ephemeral
port, but the unchanged authorization and exact command-filter logic are not
visible in this diff.

### Engineering takeaways

- Define one owner and one transport for each tool capability. A successful
  discovery handshake does not prove that the model sees schemas or that call
  arguments survive the full path.
- Test tool integrations at semantic boundaries: visible schema, argument
  fidelity, execution ownership, result correlation, cancellation, and event
  presentation.
- Prompt guidance is routing assistance, not a security boundary. Enforcement
  still belongs in relay authorization and command filtering.

### Limitations and skepticism

This is explicitly a workaround for upstream Codex MCP behavior. The model
must still follow prompt guidance and execute the shim; host tools are not
model-native structured calls in this design. The new test proves MCP absence,
not a full tool round trip with malformed arguments, timeouts, replay, or
duplicate-event checks. Also, commit prose mentions an SDK pin to `0.142.5`,
while the actual dependency diff retains `0.144.5`; this digest treats the
version claim as unresolved rather than verified.

## 3. DREA: decouple repository search from security judgment

**Primary source:** [arXiv 2607.13439v1](https://arxiv.org/abs/2607.13439v1)  
**Window:** 7-day fallback, published July 15

### Problem statement

Function-only vulnerability classifiers miss evidence that lives elsewhere in
a repository: authorization scope, sanitizers, configurations, callers, and
cross-file data flow. Fixed caller/callee retrieval is also too rigid because
the evidence needed depends on the current vulnerability hypothesis.

### Proposed method

DREA separates two roles:

- A strong **Planner** sees the target function, forms a vulnerability
  hypothesis, requests the next evidence needed to test it, revises the
  hypothesis, and produces the final `VULNERABLE` or `BENIGN` decision.
- A lightweight local **Explorer** receives each request, navigates the full
  repository using read-only `ls`, `glob`, `grep`, and `read_file`, then returns
  structured repository context, exact code evidence, and security findings.

The Planner never ingests the Explorer's entire raw trajectory. This is the
important systems idea: keep high-volume repository navigation behind a typed,
compressed evidence boundary while reserving final judgment for the stronger
model. The evaluation starts from a known target function; it does not perform
repository-wide vulnerability discovery or repair.

### Key supporting evidence

RepoPairBench contains 100 manually validated Python vulnerability/fix pairs,
or 200 instances, across 48 CWE categories. Pair-Correctness requires both the
vulnerable and patched member of a pair to be classified correctly.

- DeepSeek-V3.2: **42%** Pair-Correctness with DREA vs **19%** function-only.
- GLM-4.7: **34%** vs **26%**.
- GPT-5.2: **30%** vs **21%**.

For DeepSeek, a single agent with the same read-only tools consumed 442K paid
API tokens per sample, reached 24% Pair-Correctness, and had 64% false-positive
rate. DREA used 88K paid Planner tokens and reached 42%, which supports a typed
role boundary more than simply granting the strong model unrestricted tools.

Across DREA configurations, more than 93% of tokens are handled by the local
Explorer. The paper's claimed **16-48x** cost reduction is only the reciprocal
of paid-API token share against a hypothetical all-API design. It excludes the
A800 GPU, latency, throughput, and energy cost of processing roughly
0.34-1.56 million total tokens per sample.

The most important evaluation warning is **Lucky Hits**: a correct vulnerable
label whose explanation does not match the documented mechanism. Lucky-Hit
rates among true positives are 55.0% for DeepSeek, 45.8% for GLM, and 32.1% for
GPT. DeepSeek's 80% recall therefore contains only 36 of 100 vulnerable samples
with both a correct label and a rationale judged consistent with the real
mechanism.

### Applicability to this reader

- Put repository exploration behind a typed evidence contract with exact
  file/line provenance instead of copying tool transcripts into the planner.
- Keep the high-volume scout read-only; grant mutation and execution only after
  the planning layer names the defect and supporting evidence.
- Evaluate causal explanation separately from outcome. For coding agents, the
  analogue of a Lucky Hit is a patch that passes a narrow test for the wrong
  reason.

### Limitations and skepticism

The benchmark is 100 Python pairs, gives the detector the target function, and
excludes many multi-file/add-delete repair shapes. There are no repeated runs,
confidence intervals, or latency figures. DREA still has 28-45% false-positive
rates. The role-separation ablation changes both architecture and Explorer
model, so it does not isolate architecture alone. The rationale judge receives
the CVE, CWE, commit message, and fix diff; its score is agreement with known
evidence, not independent causal proof.

### Citation gate

**PASS.** Corresponding author Guozhu Meng was matched by exact name and the
paper's IIE/CAS/UCAS affiliations to
[OpenAlex author A5017417068](https://openalex.org/A5017417068), which reports
**2,733 citations** and ORCID `0000-0001-6388-2571`. The complete query and
disambiguation audit are saved locally. This exceeds the hard 1,000-citation
individual-author threshold.

## What I would read first

Read the E2B patch first. The reusable idea is not "use a memfd"; it is how to
bridge an immediately available local representation into a durable portable
representation without letting provisional identity cross persistence or
placement boundaries.

## What I would prototype or inspect

1. Add a focused E2B-style handover test to any snapshot/cache system: create a
   reader before the representation swap, release provisional state during the
   read, and prove retry reaches the durable source without byte ambiguity.
2. For every host-tool adapter, run one end-to-end conformance test through the
   real provider CLI: schema visibility, nested arguments, empty values,
   cancellation, result correlation, and exactly-once event ownership.
3. Try DREA's Planner/Explorer contract on repository debugging, but score the
   evidence chain and root-cause explanation separately from the final patch or
   test result.

## Audit

Screened **467 distinct candidates**: 153 in the strict 24-hour window and 122
strict-window substantive/actionable records. Preserved **38 raw/evidence
artifacts**; selected **3 sources / 7 source artifacts**. All three selected
sources received full-artifact subagent reads. **Degraded selected sources: 0.**
Paper gate: **PASS** (Guozhu Meng, OpenAlex 2,733 citations). Live paper APIs
were blocked during collection, so the 7-day paper pool was recovered from the
previous day's screened corpus before DREA's HTML, PDF, full text, and author
evidence were downloaded and verified for this run.

Artifact directory: `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-07-21`

