# Applied AI Engineering Must-Read: 2026-08-16

Primary window: the 24 hours ending `2026-08-16T16:01:24Z`. The two code selections fall inside that window. **Seven-day fallback:** HERMES was published on 2026-08-14 and is included because no strict-window paper cleared both the quality and citation gates. Routine Codex and Claude Code release-note coverage was excluded; the selected harness and sandbox clusters expose broader runtime contracts.

Estimated total reading time: **19 minutes**.

## Ranked top three

| Rank | Source | Area | Why it earned the slot | Read |
|---:|---|---|---|---:|
| 1 | [HarnessAgent structured output](https://github.com/vercel/ai/commit/62a9c2aed1a432c0260202c22eac336ebfe082d3) + [Claude Code union fidelity](https://github.com/vercel/ai/commit/a5ddbb0fa29d06baf3b35cd6199d699ee778b579) | Agent harness interoperability | Implements one typed output contract across multiple incompatible agent transports and makes unsupported routes fail explicitly. | 6 min |
| 2 | [Agents SDK run-scoped sandbox workdirs](https://github.com/openai/openai-agents-python/commit/cb8a2e7e7dd83a427cff9076e58356d00c4f90b2) and companion boundary patches | Sandboxed tool runtimes | Shows how path scope, approval identity, resume state, networking, and provider resources interact in a production sandbox SDK. | 6 min |
| 3 | [HERMES](https://arxiv.org/abs/2608.14055) | Document extraction agents | Provides production-scale evidence for schema-driven, field-provenance extraction across 55 ultra-long scientific volumes. | 7 min |

## 1. HarnessAgent: structured output is a cross-adapter protocol, not a parser option

**Primary links:** [structured-output commit](https://github.com/vercel/ai/commit/62a9c2aed1a432c0260202c22eac336ebfe082d3); [union-fidelity follow-up](https://github.com/vercel/ai/commit/a5ddbb0fa29d06baf3b35cd6199d699ee778b579).

**User/operator mental model.** An application declares one typed `output` contract on `HarnessAgent`. Every initial or continued turn carries that contract through the selected harness. Supported runtimes enforce it using their native schema mechanism or a required terminal tool; the harness then parses the returned JSON into `result.output`, partial output, or array-element streams. Unsupported transports reject the request instead of silently returning unconstrained text.

**Why it matters.** Codex-, Claude Code-, ACP-, Cline-, and LangChain-style agents do not share a structured-output protocol. This patch treats the mismatch as an adapter responsibility while preserving a provider-neutral application API and a second validation boundary at the result parser.

**What changed.** `HarnessAgent` gains an output generic and constructor-level output specification. A provider-independent `HarnessV1ResponseFormat` carries JSON Schema across prompt, continuation, bridge-start, and recovery state. Claude Code receives native `outputFormat`; Codex receives `outputSchema`; OpenCode receives `json_schema`; Deep Agents receives a LangChain tool strategy; Cline gets a schema-constrained completion tool; ACP requires an explicit private metadata mapping. Internal structured-output tool calls are removed from user-visible tool streams.

**Key mechanism.** The harness retains two related artifacts: serialized JSON Schema for runtime enforcement and the original AI SDK `Output` object for partial and complete parsing. Runtime-specific terminal values are normalized into ordinary JSON text events, avoiding a new finish-event variant. ACP persists response format in turn and cold-session records, while Cline includes it in agent-rebuild identity. A follow-up converter recursively preserves common `anyOf` and `oneOf` unions when Claude Code tool schemas become Zod.

**Concrete engineering takeaways.** Separate runtime enforcement from application parsing; define capability failure explicitly; hide protocol-internal completion tools; propagate schema through continuation and recovery; and test schema conversion adversarially, not only with happy-path objects.

**Limitations/skepticism.** A schema is mandatory. Pi, Codex ACP, and generic ACP without a mapping remain unsupported. The union converter maps `oneOf` to ordinary Zod union semantics, losing exactly-one-match behavior; one unsupported member can become `z.any()` and weaken the entire union. Deep Agents stores per-turn format in mutable module state, and OpenCode can wait for a terminal structured event that may never arrive. Patch tests and author-reported examples were inspected but not executed here.

**Estimated read time:** 6 minutes.

## 2. Agents SDK sandbox boundaries: a working directory is not a jail

**Primary links:** [run-scoped workdirs](https://github.com/openai/openai-agents-python/commit/cb8a2e7e7dd83a427cff9076e58356d00c4f90b2); [Docker no-network mode](https://github.com/openai/openai-agents-python/commit/2f1c83d5b78ee8a5b402ef9fd74e4be8085d2ae4); [Modal resources](https://github.com/openai/openai-agents-python/commit/3a888def33c309fc9521b8baa80f09db28f87473); [POSIX patch paths](https://github.com/openai/openai-agents-python/commit/05c789fe4d6f8196b13137983f4ec25c684e1d4b); [image-content validation](https://github.com/openai/openai-agents-python/commit/4cb461a7e3ad996f499c7e67b01e544cae4e8183).

**User/operator mental model.** A run can start inside a task directory so relative shell, image, and patch paths resolve consistently even when multiple trusted runs share one sandbox session. This is address translation, not confinement: absolute paths and the underlying workspace policy still define authority. Separately, Docker can opt into no-network mode, Modal can receive CPU/memory limits, patch paths are canonicalized before approval, and raster images require content signatures.

**Why it matters.** Sandboxed agent APIs often blur working directory, filesystem authority, provider isolation, and persisted session state. These patches make those boundaries inspectable and show which settings must survive resume versus which should be rebound from the current run.

**What changed.** `SandboxRunConfig.cwd` is normalized to POSIX form and bound to cloned capabilities per run. The directory must exist and be traversable as `run_as`. Shell uses a command-local `cd`; `view_image` and `apply_patch` anchor relative paths through the existing path policy. Docker `network_mode="none"` is persisted and checked against live container metadata on reuse. Modal CPU/memory settings survive creation and snapshot restore. Compound patches preflight all paths before mutation, and raster MIME no longer trusts extensions alone.

**Key mechanism.** No session-global `chdir` occurs, avoiding cross-run cwd races. Pending approved patch calls keep invocation identity but execute with the current resumed run's scope and tool implementation. Docker security intent is both serialized and compared with provider reality. Skills and memory remain session-root resources and are exposed as absolute paths when the run starts in a nested directory.

**Concrete engineering takeaways.** Model cwd as path translation; bind scope when materializing capabilities; canonicalize before policy and approval; preflight compound edits; resume against current authority; and persist security intent only where provider state must be reconstructed or verified.

**Limitations/skepticism.** `cwd` does not confine absolute paths and custom tools must apply scope themselves. Path preflight is not transactional rollback. Docker network tests use provider doubles rather than live egress probes, and no-network is opt-in and Docker-only. Raster validation checks signatures, not full decoding, while SVG/SVGZ remain extension-trusted compatibility exceptions. The 82 named tests were inspected but not run here.

**Estimated read time:** 6 minutes.

## 3. HERMES: document agents need typed state and field-level evidence

**Primary link:** [paper](https://arxiv.org/abs/2608.14055).

**Problem statement.** Scientific facts in long legacy corpora are distributed across prose, tables, figures, captions, appendices, and page layouts. Extraction must identify entities, bind attributes, normalize domain conventions, validate constraints, and preserve exact source evidence rather than merely generating document-level summaries.

**Method.** HERMES coordinates a Parser, Entity Recognizer, Annotator, Validator, and Tracer through typed shared context. Mathpix OCR and layout recovery preserve page coordinates; hybrid BM25/dense retrieval and reranking bound model context; schema prompts define entities and fields; deterministic rules normalize and flag invalid values; and a coarse-to-fine Tracer stores field-level text and bounding boxes. A workbench lets experts inspect evidence and edit records, with dependent attributes re-extracted after entity corrections.

**Key evidence.** **Author-reported:** across all 55 published *Treatise on Invertebrate Paleontology* volumes, HERMES produced 32,277 genus entities and 451,878 entity-by-schema records, with overall entity F1 0.90 and attribute F1 0.91. The claimed per-volume turnaround is about six times faster than one tested manual baseline. Transfer is mixed: palaeomagnetic attribute F1 is 0.79, while geochemical attribute F1 falls to 0.51 with recall 0.35. The 451,878 headline count exactly equals 32,277 x 14, so it includes schema slots whose source attribute may be empty rather than 451,878 populated facts.

**Applicability.** Keep parsed content, entities, attributes, validation state, and evidence in linked typed records rather than conversation history. Require explicit missing-value states; version deterministic domain rules separately from prompts; preserve page/bounding-box evidence; and evaluate provenance correctness independently from extraction accuracy.

**Limitations/skepticism.** There is no ablation proving that multi-agent orchestration beats a conventional staged pipeline, no standalone parser/table/tracer benchmark, and no independent provenance metric. Experts corrected prefilled model output without reported blinding or inter-annotator agreement. The efficiency comparison uses one manual volume and omits model/OCR cost. Cross-domain transfer still requires new schemas and validator rules. Code remains private pending publication, Mathpix is proprietary, and the main model requires roughly 150 GB of GPU memory in FP16.

**Citation gate.** **PASS.** Exact coauthor [James G. Ogg](https://openalex.org/A5080242076), matched to Purdue University in both sources, had 15,363 OpenAlex citations when fetched.

**Estimated read time:** 7 minutes.

## What I would read first

Read the [HarnessAgent structured-output patch](https://github.com/vercel/ai/commit/62a9c2aed1a432c0260202c22eac336ebfe082d3) first. Its separation of transport schema, runtime enforcement, normalized stream events, and final typed parsing is immediately reusable in any multi-provider agent harness.

## What I would prototype or inspect

Build a harness conformance matrix that sends the same schema through each adapter, checks continuation/recovery, rejects unsupported semantics, and measures both runtime enforcement and final parser rejection. For sandboxes, add a test that resumes a pending approved tool call under a different run scope and confirms current authority wins. For document agents, add an independent provenance eval: evidence recall, top-1 correctness, entailment, and bounding-box accuracy per extracted field.

## Audit

**1,149 candidates screened | 50 raw artifact records | 10 selected artifact records | 3 selected sources | 0 degraded sources | paper citation gate PASS | artifact directory:** `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-08-16`
