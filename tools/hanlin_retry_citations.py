#!/usr/bin/env python3
"""Retry citation metadata for Hanlin Zhu paper audit.

Reads candidates.jsonl and updates only citation-related fields. Uses public APIs
slowly to reduce rate-limit failures. No synthesis is performed here.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = "DeepBrief-Codex/1.0 (+citation audit)"
S2_BY_ID = "https://api.semanticscholar.org/graph/v1/paper/"
S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_WORKS = "https://api.openalex.org/works"


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_json(url: str, attempts: int = 2, delay: float = 5.0) -> dict:
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=35) as resp:
                return {"ok": True, "url": resp.geturl(), "status_code": resp.status, "json": json.loads(resp.read().decode("utf-8"))}
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(delay * (i + 1))
    return {"ok": False, "url": url, "error": last}


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", title.lower())).strip()


def title_similarity(a: str, b: str) -> float:
    aw, bw = set(a.split()), set(b.split())
    if not aw or not bw:
        return 0.0
    score = len(aw & bw) / len(aw | bw)
    if a in b or b in a:
        score += 0.15
    if a == b:
        score = 1.0
    return score


def s2_lookup(candidate: dict) -> dict:
    fields = "title,authors,year,citationCount,influentialCitationCount,url,externalIds,venue,publicationVenue,openAccessPdf"
    if candidate.get("arxiv_id"):
        url = S2_BY_ID + urllib.parse.quote(f"arXiv:{candidate['arxiv_id']}") + "?" + urllib.parse.urlencode({"fields": fields})
        result = fetch_json(url, attempts=2)
        if result["ok"]:
            data = result["json"]
            if data.get("title"):
                data["status"] = "matched"
                data["match_method"] = "arxiv_id"
                return data
        direct_fail = result
    else:
        direct_fail = {"ok": False, "error": "no arxiv id"}

    params = urllib.parse.urlencode({"query": candidate["title"], "limit": 5, "fields": fields})
    result = fetch_json(f"{S2_SEARCH}?{params}", attempts=2)
    if not result["ok"]:
        return {"status": "blocked", "direct_fail": direct_fail, "search_fail": result}
    norm = normalize_title(candidate["title"])
    best = None
    best_score = -1.0
    for match in result["json"].get("data", []):
        score = title_similarity(norm, normalize_title(match.get("title", "")))
        if score > best_score:
            best, best_score = match, score
    if best and best_score >= 0.72:
        best["status"] = "matched"
        best["match_method"] = "title_search"
        best["match_score"] = round(best_score, 3)
        return best
    return {"status": "no_confident_match", "matches": result["json"].get("data", [])[:5]}


def openalex_lookup(candidate: dict) -> dict:
    # Search title; OpenAlex often has older conference papers even when S2 throttles.
    params = urllib.parse.urlencode({"search": candidate["title"], "per-page": 5, "mailto": "hanlinzhu-paper-audit@example.com"})
    result = fetch_json(f"{OPENALEX_WORKS}?{params}", attempts=2, delay=2)
    if not result["ok"]:
        return {"status": "blocked", "error": result.get("error"), "url": result.get("url")}
    norm = normalize_title(candidate["title"])
    best = None
    best_score = -1.0
    for match in result["json"].get("results", []):
        score = title_similarity(norm, normalize_title(match.get("title", "")))
        if score > best_score:
            best, best_score = match, score
    if best and best_score >= 0.72:
        return {
            "status": "matched",
            "match_method": "title_search",
            "match_score": round(best_score, 3),
            "id": best.get("id"),
            "doi": best.get("doi"),
            "title": best.get("title"),
            "publication_year": best.get("publication_year"),
            "cited_by_count": best.get("cited_by_count"),
            "primary_location": best.get("primary_location"),
            "open_access": best.get("open_access"),
        }
    return {"status": "no_confident_match", "matches": result["json"].get("results", [])[:5]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True, type=Path)
    ap.add_argument("--delay", type=float, default=4.0)
    args = ap.parse_args()
    artifact = args.artifact_dir
    candidates_path = artifact / "sources" / "candidates.jsonl"
    raw_dir = artifact / "sources" / "raw"
    candidates = [json.loads(line) for line in candidates_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for i, candidate in enumerate(candidates, start=1):
        print(f"[{i}/{len(candidates)}] {candidate['id']}", flush=True)
        s2 = s2_lookup(candidate)
        time.sleep(args.delay)
        oa = openalex_lookup(candidate)
        citation_path = raw_dir / f"{candidate['id']}-citation-metadata.json"
        citation_path.write_text(json.dumps({"semantic_scholar": s2, "openalex": oa, "retried_at": now_iso()}, indent=2, ensure_ascii=False), encoding="utf-8")
        s2_cites = s2.get("citationCount") if s2.get("status") == "matched" else None
        oa_cites = oa.get("cited_by_count") if oa.get("status") == "matched" else None
        candidate["semantic_scholar"] = s2
        candidate["openalex"] = oa
        candidate["citation_count"] = s2_cites if s2_cites is not None else oa_cites
        candidate["citation_source"] = "Semantic Scholar" if s2_cites is not None else ("OpenAlex" if oa_cites is not None else None)
        candidate["citation_checked_at"] = now_iso()
        time.sleep(args.delay)
    candidates_path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in candidates), encoding="utf-8")
    print(f"updated {candidates_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
