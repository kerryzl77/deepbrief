# Daily Applied AI Engineering Must-Read

**September 24, 2026**  
**Primary window:** September 23, 16:02:54 UTC to September 24, 16:02:54 UTC  
**Targeted reading time:** 19 minutes

All three selections were published inside the primary 24-hour window. This issue connects two sandbox lifecycle failures with a controlled study of how a document agent chooses evidence. The common engineering question is whether the runtime still owns the data and resources an agent is using.

## Ranked top three

| Rank | Source | Area | Why read it | Targeted read |
|---:|---|---|---|---:|
| 1 | [Cloudflare Containers cross-tenant disk exposure](https://blog.cloudflare.com/containers-cross-tenant-vulnerability/) | Sandbox isolation | Shows how recycled storage leaked across Firecracker VM tenants and why the fix had to include existing snapshots | 7 min |
| 2 | [E2B template cache pinning](https://github.com/e2b-dev/runtime/commit/e940ec7ee78bb12831791038c665ec51fd7229d8) | Sandbox lifecycle | A complete diff for tying cached VM template files to live sandbox lifetimes | 6 min |
| 3 | [VLM pipelines for long-document QA](https://arxiv.org/abs/2609.29933) | Document agents | Controlled comparisons of full-document reading, image retrieval, and tool-driven evidence access | 6 min |

## 1. Cloudflare: recycled disk blocks crossed the tenant boundary

**Primary link:** [Cloudflare's incident analysis](https://blog.cloudflare.com/containers-cross-tenant-vulnerability/)

**User and operator mental model.** A customer starts a Container, which runs in its own Firecracker VM. Its writable root disk uses a shared `dm-thin` pool. Deleting one tenant's thin volume returns physical blocks to that pool; another tenant can later receive them. The vulnerability was in recycled storage initialization, beneath the VM boundary. [Cloudflare's analysis](https://blog.cloudflare.com/containers-cross-tenant-vulnerability/) describes the mechanism and says its Sandboxes product was affected through Containers.

**Why it matters.** A new tenant's first read of an unmapped region returned zeroes, making a read-only probe look safe. The researchers instead wrote **4 KiB** into a free, 64 KiB-aligned guest region. That write mapped a recycled **64 KiB** physical block; a raw disk read could expose up to **60 KiB** of prior-tenant bytes in the unwritten remainder. They could not choose a victim or host, and this did not read an active tenant disk. [Cloudflare's technical account](https://blog.cloudflare.com/containers-cross-tenant-vulnerability/) supplies the block sizes and sequence.

**What changed.** Cloudflare removed `skip_block_zeroing` so newly allocated blocks are zeroed. That did not clean blocks already mapped into running disks or cached OCI-image snapshots. It also retired running disks, drained hosts, restarted VMs, and cleared caches; the post dates final old-snapshot cleanup to September 19. The researchers later reported that their proof of concept stopped working. [Cloudflare's remediation timeline](https://blog.cloudflare.com/containers-cross-tenant-vulnerability/) distinguishes the allocator change from the cleanup.

**Key evidence.** Researchers reported residual material on **18 of 24 placements** and **20 of 22 nodes** sampled across four continents. They used ext4 directory checksums to attribute recovered blocks and reported 2,700 distinct foreign directory inodes in a separate six-placement analysis. These are source-reported observations with different denominators, not a fleetwide exposure rate. [Cloudflare's report](https://blog.cloudflare.com/containers-cross-tenant-vulnerability/) also says retained telemetry found no other activity matching the reported write/read technique.

**Engineering takeaways (inference).** Test storage reuse at the physical allocation size: place a known pattern in a retired tenant block, perform a partial write from a fresh tenant, then read the whole backing block. Audit sparse files, snapshots, image caches, and cleanup after changing zeroing policy. Treat a negative telemetry search as bounded by detector coverage and retention.

**Limitations and skepticism.** The public artifact contains no raw disk samples, reuse-test code, detector query, or independent fleet audit. "No additional activity found" does not establish that no alternative exploit occurred. The post gives no performance cost for restored zeroing. **Targeted read: 7 minutes.**

## 2. E2B: pin template files while a sandbox still needs them

**Primary link:** [E2B runtime commit `e940ec7`](https://github.com/e2b-dev/runtime/commit/e940ec7ee78bb12831791038c665ec51fd7229d8)

**User and operator mental model.** A sandbox starts or resumes from a build-keyed VM template containing snapshot and storage files. The orchestrator caches templates; eviction calls `Close`, which removes those files. Previously, a long TTL was the main protection against a live sandbox outlasting its cached template. TTL is a timer, not proof that every consumer has finished. The [commit diff](https://github.com/e2b-dev/runtime/commit/e940ec7ee78bb12831791038c665ec51fd7229d8) shows the old and new lifecycle paths.

**Why it matters and what changed.** `GetTemplatePinned` now acquires a cache entry and a per-holder pin atomically with eviction. Each sandbox contributes a reference to the **specific template instance**, and its teardown or rollback releases that reference. Eviction skips destructive close while that instance has holders. Invalidation retires an old instance so new lookups cannot use it, then closes it after the last holder exits. A normally released instance that has left the TTL cache can be re-admitted briefly. [E2B's patch](https://github.com/e2b-dev/runtime/commit/e940ec7ee78bb12831791038c665ec51fd7229d8) implements these transitions.

**Key mechanism and evidence.** The patch adds `sync.Once`-guarded release, instance-aware eviction, race-oriented tests, and metrics for resident entries, pin references, oldest pin age, and approximate mapping bytes. The tests are present in the diff; they were not executed for this digest. The commit reports no production incident timeline, startup-latency change, memory savings, or cost delta. [The complete commit](https://github.com/e2b-dev/runtime/commit/e940ec7ee78bb12831791038c665ec51fd7229d8) is the primary evidence.

**Concrete engineering takeaways (inference).** For destructively cleaned cache resources, make lookup plus lifetime acquisition atomic; count holders per resource instance rather than only per key; retire invalidated instances; and keep slow close outside the admission lock. Alert on old outstanding pins and missing release paths before adding tighter cache bounds.

**Limitations and skepticism.** Pins have no independent timeout, so a lost release can retain files indefinitely. A possible cleanup gap in a superseded-instance collision deserves a targeted test; reachability in production is unverified. The patch supplies implementation and test intent, not measured performance or passing CI evidence. **Targeted read: 6 minutes.**

## 3. Long-document QA: choose the evidence path for the reader

**Primary link:** [An Empirical Study of VLM Pipelines for Long-Document QA](https://arxiv.org/abs/2609.29933)

**Problem statement.** A long-PDF question-answering system can send the full PDF, all page images, extracted text, a small retrieved page set, or an agent's sequence of page/figure/table/search calls. The best policy may depend on document length, visual evidence, and reader model. The [paper](https://arxiv.org/abs/2609.29933) compares these choices on MMLongBench-Doc (1,082 questions) and LongDocURL (2,325 public-split questions).

**Method.** The study compares static full-document inputs, text retrieval, image-page retrieval, and a six-tool function-calling agent. The agent receives a deterministic structural catalog and can read pages, extract figures and tables, search text, and finish. Readers include Sonnet 4.5 and Qwen3.5 4B/9B/27B; a common answer extractor precedes official scoring. [Paper methods and Table 1](https://arxiv.org/pdf/2609.29933) provide the matched comparisons.

**Key evidence.** On visually varied MMLongBench-Doc, the Sonnet agent scored **0.625** at about **20k reader input tokens**, versus **0.508** at **7.6k** for the same reader with top-five ColQwen image pages. That +11.7 percentage-point paired difference has a reported 95% interval of **+8.8 to +14.8**. On the longer LongDocURL set, the Sonnet agent scored **0.659** at **21k** tokens, versus **0.644** at **7.4k** for top-five Nem-CE pages; its +1.5-point interval **crosses zero**. The strongest image retriever's mean evidence-page Hit@5 was **91.4**, versus **82.4** for the strongest text pipeline. [Paper Tables 1-2 and 16-17](https://arxiv.org/pdf/2609.29933) report the scores and intervals.

**Applicability (inference).** Start with image-page retrieval plus a strong reader when documents can be indexed and questions are evidence-local. Trial the catalog/tool agent for high-value, visually varied questions and track evidence recall, answer accuracy, total preprocessing, reader tokens, request failures, and latency separately. Test the loop's stop condition: the paper's Qwen-4B implementation often called `finish` again, increasing model work. [The paper's tool and cost analysis](https://arxiv.org/pdf/2609.29933) explains why reader-input tokens alone are an incomplete bill.

**Limitations and skepticism.** The results cover English QA on two benchmarks with particular reader versions and API behavior. They do not establish performance for summarization or extraction. Some prior agent rows use different judges, and the main token comparisons omit preprocessing and retrieval compute. The paper's tools are bundled, so tool-use rates do not identify which tool caused the gain.

**Citation gate.** Passed: coauthor Dimitrios Dimitriadis is matched by name and Amazon affiliation to an [OpenAlex author profile](https://openalex.org/A5115044944) with **1,816 citations**. A same-name profile at a different institution was excluded. See the local citation audit (local research intermediate discarded). **Targeted read: 6 minutes.**

## What I would read first

Read Cloudflare's exploit sequence and two-stage cleanup first. It gives a concrete test to add to any shared storage or sandbox host. Then inspect E2B's pin/release state machine for a complementary lifetime ownership problem.

## What I would prototype or inspect

1. Add a cross-tenant storage-reuse test with a patterned old block, a fresh tenant's partial write, and a full raw-block assertion; run it through image and snapshot cache paths.
2. Instrument template-cache holder count and oldest pin age, then fault-inject eviction, invalidation, request cancellation, and teardown races.
3. On a document-QA eval, compare top-five image pages with a bounded catalog/page/table/search agent. Report evidence Hit@5, answer quality, complete cost, latency, and failure rate by document length.

## Audit

**152 distinct candidates screened; 185 successful raw local artifacts plus 13 derived text artifacts; 3 selected sources backed by 8 selected artifacts; 0 degraded selected sources; 1 failed discovery-only RSS fetch; paper citation gate PASS; runtime gate PASS (`gpt-6-sol`, high for coordinator and all six workers).** The complete artifact directory is `/Users/liuzikai/Documents/GitHub/deepbrief/artifacts/daily-must-read/2026-09-24`.

Audit files: candidates (local research intermediate discarded), manifest (local research intermediate discarded), fanout report (local research intermediate discarded), source-read reports (local research intermediate discarded), evidence matrix (local research intermediate discarded), citation audit (local research intermediate discarded), and runtime audit (local research intermediate discarded). No PDF was rendered.
