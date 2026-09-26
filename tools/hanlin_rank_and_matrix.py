#!/usr/bin/env python3
"""Build deterministic ranking and evidence artifacts for the Hanlin Zhu survey."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
from pathlib import Path


RELEVANCE = {
    "hz09-gsm-agent-understanding-agentic-reasoning-using": 96,
    "hz08-auditing-black-box-llm-apis-with-a-rank-based-un": 94,
    "hz20-efficient-prompt-caching-via-embedding-similarit": 90,
    "hz03-copt-contrastive-on-policy-thinking-with-continu": 88,
    "hz16-learning-personalized-alignment-for-evaluating-o": 85,
    "hz13-token-assorted-mixing-latent-and-text-tokens-for": 82,
    "hz01-discoloop-looping-discrete-embeddings-and-contin": 80,
    "hz11-reasoning-by-superposition-a-theoretical-perspec": 78,
    "hz07-emergence-of-superposition-unveiling-the-trainin": 77,
    "hz10-how-do-llms-perform-two-hop-reasoning-in-context": 76,
    "hz12-generalization-or-hallucination-understanding-ou": 75,
    "hz02-transformers-provably-learn-to-internalize-chain": 74,
    "hz05-breaking-the-reversal-curse-in-autoregressive-la": 72,
    "hz15-towards-a-theoretical-understanding-of-the-rever": 70,
    "hz14-avoiding-catastrophe-in-online-learning-by-askin": 68,
    "hz04-safe-learning-under-irreversible-dynamics-via-as": 66,
    "hz18-towards-optimal-statistical-watermarking": 64,
    "hz28-guided-dialog-policy-learning-reward-estimation": 58,
    "hz19-on-representation-complexity-of-model-based-and": 56,
    "hz21-end-to-end-story-plot-generator": 54,
    "hz22-provably-efficient-offline-goal-conditioned-rein": 52,
    "hz25-provably-efficient-reinforcement-learning-via-su": 50,
    "hz23-importance-weighted-actor-critic-for-optimal-con": 49,
    "hz24-optimal-conservative-offline-rl-with-general-fun": 48,
    "hz06-multi-objective-learning-for-diffusion-models-a": 46,
    "hz27-vector-matrix-vector-queries-for-solving-linear": 42,
    "hz26-average-case-communication-complexity-of-statist": 40,
    "hz17-starling-7b-improving-helpfulness-and-harmlessne": 30,
}


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def final_pull(report: str) -> str:
    m = re.search(r"Final synthesis should pull:\s*(.*)", report)
    return m.group(1).strip() if m else ""


def evidence_refs(report: str, limit: int = 4) -> list[str]:
    refs = []
    for match in re.finditer(r"`([^`]+:\d+(?:-\d+)?)`", report):
        ref = match.group(1)
        if ref.startswith("artifacts/") and ref not in refs:
            refs.append(ref)
        if len(refs) >= limit:
            break
    return refs


def citation_score(count: int | None, max_count: int) -> float:
    if count is None:
        return 0.0
    return 100.0 * math.log1p(count) / max(1.0, math.log1p(max_count))


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True, type=Path)
    args = ap.parse_args()
    base = args.artifact_dir
    candidates_path = base / "sources" / "candidates.jsonl"
    candidates = read_jsonl(candidates_path)
    max_cites = max([c.get("citation_count") or 0 for c in candidates] + [1])
    out = []
    for idx, c in enumerate(candidates, start=1):
        cid = c["id"]
        report_path = base / "reviews" / "subagents" / f"read-{cid}.md"
        report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        relevance = RELEVANCE.get(cid, 50)
        cites = c.get("citation_count")
        cscore = citation_score(cites, max_cites)
        priority = float(relevance)
        status = "degraded" if c.get("download_status") != "downloaded" or cid.endswith("starling-7b-improving-helpfulness-and-harmlessne") else "verified"
        item = {
            **c,
            "citation_number": idx,
            "profile_relevance": relevance,
            "citation_score": round(cscore, 2),
            "priority_score": priority,
            "citation_count_status": "available" if cites is not None else "missing",
            "verification_status": status,
            "read_report": str(report_path),
            "final_synthesis_pull": final_pull(report),
            "evidence_refs": evidence_refs(report),
            "ranked_at": now_iso(),
        }
        out.append(item)

    citation_ranked = sorted(out, key=lambda x: (x.get("citation_count") is None, -(x.get("citation_count") or -1), -x["profile_relevance"], x["id"]))
    relevance_ranked = sorted(out, key=lambda x: (-x["profile_relevance"], -(x.get("citation_count") or -1), x["id"]))
    priority_ranked = sorted(out, key=lambda x: (-x["priority_score"], -(x.get("citation_count") or -1), x["id"]))
    for i, item in enumerate(citation_ranked, 1):
        item["citation_rank"] = i
    for i, item in enumerate(relevance_ranked, 1):
        item["relevance_rank"] = i
    for i, item in enumerate(priority_ranked, 1):
        item["priority_rank"] = i

    by_id = {item["id"]: item for item in out}
    out = [by_id[c["id"]] for c in candidates]
    ranking_path = base / "sources" / "ranking.jsonl"
    ranking_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in out), encoding="utf-8")
    selected_path = base / "sources" / "selected-candidates.jsonl"
    selected_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in priority_ranked[:8]), encoding="utf-8")

    matrix = ["# Evidence Matrix\n", f"- Generated: {now_iso()}", "- Scope: one row per Hanlin Zhu publication-page paper link.", ""]
    matrix.append("| Citation | Paper | Claim / synthesis pull | Local evidence | Status |")
    matrix.append("|---:|---|---|---|---|")
    for item in priority_ranked:
        refs = "<br>".join(f"`{r}`" for r in item["evidence_refs"]) or "No extracted evidence ref"
        matrix.append(
            f"| {item['citation_number']} | {md_escape(item['title'])} | {md_escape(item['final_synthesis_pull'][:520])} | {refs} | {item['verification_status']} |"
        )
    matrix_path = base / "verification" / "evidence-matrix.md"
    matrix_path.write_text("\n".join(matrix) + "\n", encoding="utf-8")

    print(json.dumps({"ranking": str(ranking_path), "selected": str(selected_path), "matrix": str(matrix_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
