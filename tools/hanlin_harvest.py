#!/usr/bin/env python3
"""Harvest Hanlin Zhu publication artifacts for a Codex-native DeepBrief run.

This script is intentionally deterministic: it fetches public pages/PDFs, extracts
metadata, writes manifests, and runs no synthesis.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


USER_AGENT = "DeepBrief-Codex/1.0 (+https://hanlinzhu.com/ paper audit)"
HOME_URL = "https://hanlinzhu.com/"
PUBLICATIONS_URL = "https://hanlinzhu.com/publications/"
SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_WORKS = "https://api.openalex.org/works"
ARXIV_API = "https://export.arxiv.org/api/query"


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(text: str, max_len: int = 72) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].strip("-") or "item"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def request_bytes(url: str, timeout: int = 45) -> tuple[bytes, str, int]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/pdf,application/json,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.geturl(), resp.status


def fetch_with_retries(url: str, attempts: int = 3, delay: float = 1.0) -> tuple[bytes | None, str, int | None, str | None]:
    last_err = None
    for i in range(attempts):
        try:
            data, final_url, status = request_bytes(url)
            return data, final_url, status, None
        except Exception as exc:  # noqa: BLE001 - logged in manifest
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(delay * (i + 1))
    return None, url, None, last_err


def write_bytes(path: Path, data: bytes) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"local_path": str(path), "bytes": len(data), "sha256": sha256_bytes(data)}


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[dict] = []
        self._href: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attr = dict(attrs)
            self._href = attr.get("href")
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = html.unescape(" ".join(self._parts)).strip()
            text = re.sub(r"\s+", " ", text)
            self.anchors.append({"href": self._href, "text": text})
            self._href = None
            self._parts = []


def strip_tags(raw: str) -> str:
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", "\n", raw)
    raw = html.unescape(raw)
    raw = raw.replace("\xa0", " ")
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{2,}", "\n", raw)
    return raw.strip()


def parse_publication_blocks(page_text: str) -> list[dict]:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    try:
        start = lines.index("Publications") + 1
    except ValueError:
        start = 0
    stop = len(lines)
    for i, line in enumerate(lines):
        if i > start and line == "Follow:":
            stop = i
            break
    paper_title_re = re.compile(
        r"(DiscoLoop|Transformers Provably|CopT:|Safe Learning|Breaking the Reversal|"
        r"Multi-Objective Learning|Emergence of Superposition|Auditing Black-Box|GSM-Agent|"
        r"How Do LLMs|Reasoning by Superposition|Generalization or Hallucination|"
        r"Token Assorted|Avoiding Catastrophe|Towards a Theoretical|Learning Personalized|"
        r"Starling-7B|Towards Optimal|On Representation|Efficient Prompt|End-to-end|"
        r"Provably Efficient Offline|Importance Weighted|Optimal Conservative|"
        r"Provably Efficient Reinforcement|Average-Case|Vector-Matrix|Guided Dialog)"
    )
    blocks: list[dict] = []
    i = start
    while i < stop:
        title = lines[i]
        if not paper_title_re.match(title):
            i += 1
            continue
        j = i + 1
        body: list[str] = []
        while j < stop and not paper_title_re.match(lines[j]):
            body.append(lines[j])
            j += 1
        authors = body[0] if body else ""
        venue = " ".join(body[1:]).strip()
        blocks.append({"title": title, "authors": authors, "venue": venue})
        i = j
    return blocks


def parse_arxiv_id(url: str) -> str | None:
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/([0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?", url)
    if m:
        return m.group(1)
    m = re.search(r"arxiv:([0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?", url, re.I)
    return m.group(1) if m else None


def arxiv_api_metadata(arxiv_id: str) -> dict:
    url = f"{ARXIV_API}?id_list={urllib.parse.quote(arxiv_id)}"
    data, final_url, status, err = fetch_with_retries(url, attempts=2)
    if not data:
        return {"status": "blocked", "error": err, "url": final_url}
    try:
        root = ET.fromstring(data)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        entry = root.find("atom:entry", ns)
        if entry is None:
            return {"status": "missing", "raw": data.decode("utf-8", "replace")[:500]}
        links = []
        for link in entry.findall("atom:link", ns):
            links.append({k: v for k, v in link.attrib.items()})
        cats = [c.attrib.get("term") for c in entry.findall("atom:category", ns) if c.attrib.get("term")]
        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.findtext("atom:name", default="", namespaces=ns)
            if name:
                authors.append(name)
        return {
            "status": "downloaded",
            "source_url": final_url,
            "title": re.sub(r"\s+", " ", entry.findtext("atom:title", default="", namespaces=ns)).strip(),
            "summary": re.sub(r"\s+", " ", entry.findtext("atom:summary", default="", namespaces=ns)).strip(),
            "published": entry.findtext("atom:published", default="", namespaces=ns),
            "updated": entry.findtext("atom:updated", default="", namespaces=ns),
            "authors": authors,
            "categories": cats,
            "links": links,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "parse_error", "error": f"{type(exc).__name__}: {exc}", "source_url": final_url}


def semantic_scholar_by_title(title: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "query": title,
            "limit": 3,
            "fields": "title,authors,year,citationCount,influentialCitationCount,url,externalIds,venue,publicationVenue,openAccessPdf",
        }
    )
    data, final_url, status, err = fetch_with_retries(f"{SEMANTIC_SCHOLAR_SEARCH}?{params}", attempts=2, delay=2.0)
    if not data:
        return {"status": "blocked", "url": final_url, "error": err}
    try:
        payload = json.loads(data.decode("utf-8"))
        matches = payload.get("data") or []
        norm_title = normalize_title(title)
        best = None
        best_score = -1.0
        for match in matches:
            score = title_similarity(norm_title, normalize_title(match.get("title", "")))
            if score > best_score:
                best = match
                best_score = score
        if best and best_score >= 0.72:
            best["match_score"] = round(best_score, 3)
            best["status"] = "matched"
            return best
        return {"status": "no_confident_match", "url": final_url, "matches": matches[:3]}
    except Exception as exc:  # noqa: BLE001
        return {"status": "parse_error", "url": final_url, "error": f"{type(exc).__name__}: {exc}"}


def openalex_by_title(title: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "search": title,
            "per-page": 3,
            "mailto": "hanlinzhu-paper-audit@example.com",
        }
    )
    data, final_url, status, err = fetch_with_retries(f"{OPENALEX_WORKS}?{params}", attempts=2, delay=1.5)
    if not data:
        return {"status": "blocked", "url": final_url, "error": err}
    try:
        payload = json.loads(data.decode("utf-8"))
        matches = payload.get("results") or []
        norm_title = normalize_title(title)
        best = None
        best_score = -1.0
        for match in matches:
            score = title_similarity(norm_title, normalize_title(match.get("title", "")))
            if score > best_score:
                best = match
                best_score = score
        if best and best_score >= 0.72:
            return {
                "status": "matched",
                "match_score": round(best_score, 3),
                "id": best.get("id"),
                "doi": best.get("doi"),
                "title": best.get("title"),
                "publication_year": best.get("publication_year"),
                "cited_by_count": best.get("cited_by_count"),
                "primary_location": best.get("primary_location"),
                "open_access": best.get("open_access"),
            }
        return {"status": "no_confident_match", "url": final_url, "matches": matches[:3]}
    except Exception as exc:  # noqa: BLE001
        return {"status": "parse_error", "url": final_url, "error": f"{type(exc).__name__}: {exc}"}


def normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def title_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    aw = set(a.split())
    bw = set(b.split())
    jaccard = len(aw & bw) / max(1, len(aw | bw))
    seq = 1.0 if a == b else 0.0
    contains = 0.15 if (a in b or b in a) else 0.0
    return max(jaccard + contains, seq)


def pdf_page_count(pdf_path: Path) -> int | None:
    try:
        out = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        return int(m.group(1)) if m else None
    except Exception:
        return None


def pdf_to_text(pdf_path: Path, txt_path: Path) -> dict:
    try:
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(["pdftotext", "-layout", str(pdf_path), str(txt_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        data = txt_path.read_bytes()
        return {"status": "downloaded", "local_path": str(txt_path), "bytes": len(data), "sha256": sha256_bytes(data)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "blocked", "error": f"{type(exc).__name__}: {exc}", "local_path": str(txt_path)}


def maybe_publication_year(venue: str, metadata: dict) -> str:
    m = re.search(r"\b(20[0-9]{2})\b", venue)
    if m:
        return m.group(1)
    published = metadata.get("published") or ""
    if published:
        return published[:4]
    return ""


def download_pdf(url: str, out_path: Path) -> dict:
    data, final_url, status, err = fetch_with_retries(url, attempts=3, delay=1.5)
    if not data:
        return {"status": "blocked", "url": url, "final_url": final_url, "error": err, "local_path": str(out_path)}
    if not data.startswith(b"%PDF"):
        return {
            "status": "degraded",
            "url": url,
            "final_url": final_url,
            "error": "response was not a PDF",
            "sample": data[:80].decode("utf-8", "replace"),
            "local_path": str(out_path),
            "bytes": len(data),
        }
    rec = write_bytes(out_path, data)
    rec.update({"status": "downloaded", "url": url, "final_url": final_url})
    return rec


def build_items(pub_html: str) -> tuple[list[dict], list[dict]]:
    parser = AnchorParser()
    parser.feed(pub_html)
    anchors = parser.anchors
    text = strip_tags(pub_html)
    blocks = parse_publication_blocks(text)
    paper_anchors = []
    for anchor in anchors:
        href = urllib.parse.urljoin(PUBLICATIONS_URL, anchor["href"])
        if "arxiv.org/abs/" in href or "openreview.net/forum" in href:
            paper_anchors.append({"title": anchor["text"], "url": href})
    seen = set()
    deduped = []
    for anchor in paper_anchors:
        key = normalize_title(anchor["title"])
        if key not in seen:
            seen.add(key)
            deduped.append(anchor)
    block_by_title = {normalize_title(b["title"]): b for b in blocks}
    items = []
    for idx, anchor in enumerate(deduped, start=1):
        title_norm = normalize_title(anchor["title"])
        block = block_by_title.get(title_norm, {})
        arxiv_id = parse_arxiv_id(anchor["url"])
        source_type = "arxiv" if arxiv_id else "openreview"
        item_id = f"hz{idx:02d}-{slugify(anchor['title'], 48)}"
        items.append(
            {
                "id": item_id,
                "idx": idx,
                "title": anchor["title"],
                "url": anchor["url"],
                "source_type": source_type,
                "arxiv_id": arxiv_id,
                "authors_site": block.get("authors", ""),
                "venue_site": block.get("venue", ""),
            }
        )
    return items, anchors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    out = args.out
    sources = out / "sources"
    raw = sources / "raw"
    papers = sources / "papers"
    verification = out / "verification"
    for path in [raw, papers, verification]:
        path.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    candidates: list[dict] = []
    logs: list[str] = []

    for label, url in [("home", HOME_URL), ("publications", PUBLICATIONS_URL)]:
        data, final_url, status, err = fetch_with_retries(url)
        rec = {
            "candidate_id": f"site-{label}",
            "url": url,
            "artifact_type": "html",
            "fetched_at": now_iso(),
            "status": "downloaded" if data else "blocked",
            "selected": False,
            "intended_use": "site_crawl",
            "final_url": final_url,
            "http_status": status,
        }
        if data:
            saved = write_bytes(raw / f"{label}.html", data)
            rec.update(saved)
        else:
            rec["error"] = err
        manifest.append(rec)
        if not data and label == "publications":
            print(f"Failed to fetch publications page: {err}", file=sys.stderr)
            return 2
        if label == "publications":
            pub_html = data.decode("utf-8", "replace") if data else ""

    items, anchors = build_items(pub_html)
    (verification / "site-anchors.json").write_text(json.dumps(anchors, indent=2, ensure_ascii=False), encoding="utf-8")
    (sources / "identified-papers.json").write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

    for item in items:
        logs.append(f"{item['id']}: {item['title']}")
        arxiv_meta = {}
        if item["arxiv_id"]:
            arxiv_meta = arxiv_api_metadata(item["arxiv_id"])
            meta_path = raw / f"{item['id']}-arxiv.json"
            meta_path.write_text(json.dumps(arxiv_meta, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest.append(
                {
                    "candidate_id": item["id"],
                    "url": arxiv_meta.get("source_url", f"{ARXIV_API}?id_list={item['arxiv_id']}"),
                    "artifact_type": "metadata",
                    "local_path": str(meta_path),
                    "bytes": meta_path.stat().st_size,
                    "sha256": sha256_bytes(meta_path.read_bytes()),
                    "fetched_at": now_iso(),
                    "status": arxiv_meta.get("status", "downloaded"),
                    "selected": True,
                    "intended_use": "paper_metadata",
                }
            )
            pdf_url = f"https://arxiv.org/pdf/{item['arxiv_id']}"
        else:
            pdf_url = item["url"].replace("/forum?", "/pdf?")

        ss = semantic_scholar_by_title(item["title"])
        oa = openalex_by_title(item["title"])
        citation_path = raw / f"{item['id']}-citation-metadata.json"
        citation_path.write_text(json.dumps({"semantic_scholar": ss, "openalex": oa}, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest.append(
            {
                "candidate_id": item["id"],
                "url": "https://api.semanticscholar.org/ + https://api.openalex.org/",
                "artifact_type": "metadata",
                "local_path": str(citation_path),
                "bytes": citation_path.stat().st_size,
                "sha256": sha256_bytes(citation_path.read_bytes()),
                "fetched_at": now_iso(),
                "status": "downloaded",
                "selected": True,
                "intended_use": "citation_count",
            }
        )

        pdf_path = papers / f"{item['id']}.pdf"
        pdf_rec = download_pdf(pdf_url, pdf_path)
        manifest.append(
            {
                "candidate_id": item["id"],
                "url": pdf_url,
                "artifact_type": "pdf",
                "local_path": pdf_rec.get("local_path", str(pdf_path)),
                "bytes": pdf_rec.get("bytes", 0),
                "sha256": pdf_rec.get("sha256"),
                "fetched_at": now_iso(),
                "status": pdf_rec.get("status", "blocked"),
                "selected": True,
                "intended_use": "selected_source",
                "final_url": pdf_rec.get("final_url"),
                "error": pdf_rec.get("error"),
            }
        )
        txt_rec = {"status": "blocked"}
        page_count = None
        if pdf_rec.get("status") == "downloaded":
            page_count = pdf_page_count(pdf_path)
            txt_rec = pdf_to_text(pdf_path, papers / f"{item['id']}.txt")
            manifest.append(
                {
                    "candidate_id": item["id"],
                    "url": pdf_url,
                    "artifact_type": "full_text",
                    "local_path": txt_rec.get("local_path"),
                    "bytes": txt_rec.get("bytes", 0),
                    "sha256": txt_rec.get("sha256"),
                    "fetched_at": now_iso(),
                    "status": txt_rec.get("status"),
                    "selected": True,
                    "intended_use": "read_report",
                    "error": txt_rec.get("error"),
                }
            )

        ss_cites = ss.get("citationCount") if ss.get("status") == "matched" else None
        oa_cites = oa.get("cited_by_count") if oa.get("status") == "matched" else None
        citation_count = ss_cites if ss_cites is not None else oa_cites
        citation_source = "Semantic Scholar" if ss_cites is not None else ("OpenAlex" if oa_cites is not None else None)
        candidate = {
            "id": item["id"],
            "source_id": "hanlinzhu_publications",
            "type": "paper",
            "title": item["title"],
            "url": item["url"],
            "pdf_url": pdf_url,
            "published_at": arxiv_meta.get("published") or maybe_publication_year(item["venue_site"], arxiv_meta),
            "year": maybe_publication_year(item["venue_site"], arxiv_meta),
            "lane": "papers",
            "discovered_by": "main:hanlin_harvest",
            "dedupe_key": normalize_title(item["title"]),
            "summary": arxiv_meta.get("summary", ""),
            "authors_site": item.get("authors_site", ""),
            "authors_metadata": arxiv_meta.get("authors", []),
            "venue_site": item.get("venue_site", ""),
            "quality_signals": ["author_homepage_linked", "primary_listing", item["source_type"]],
            "author_check": "hanlin_zhu_listed_on_homepage",
            "download_status": pdf_rec.get("status"),
            "raw_artifact_paths": [p for p in [str(pdf_path) if pdf_rec.get("status") == "downloaded" else None, txt_rec.get("local_path")] if p],
            "page_count": page_count,
            "arxiv_id": item["arxiv_id"],
            "source_type": item["source_type"],
            "semantic_scholar": ss,
            "openalex": oa,
            "citation_count": citation_count,
            "citation_source": citation_source,
            "score": None,
            "rejection_reason": None,
            "verified_at": now_iso(),
        }
        candidates.append(candidate)

    candidates_path = sources / "candidates.jsonl"
    candidates_path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in candidates), encoding="utf-8")
    manifest_path = sources / "manifest.jsonl"
    manifest_path.write_text("".join(json.dumps(m, ensure_ascii=False) + "\n" for m in manifest), encoding="utf-8")
    (verification / "harvest-log.md").write_text(
        "# Harvest Log\n\n"
        f"- Fetched at: {now_iso()}\n"
        f"- Site: {PUBLICATIONS_URL}\n"
        f"- Identified paper links: {len(items)}\n"
        f"- Manifest records: {len(manifest)}\n\n"
        + "\n".join(f"- {line}" for line in logs)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"papers": len(items), "candidates": str(candidates_path), "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
