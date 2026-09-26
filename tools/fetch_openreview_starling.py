#!/usr/bin/env python3
"""Fetch Starling-7B OpenReview metadata and attachment if public endpoints allow it."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path


UA = "DeepBrief-Codex/1.0 (+OpenReview artifact audit)"


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch(url: str) -> tuple[bytes | None, str, int | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.read(), resp.geturl(), resp.status, None
    except Exception as exc:  # noqa: BLE001
        return None, url, None, f"{type(exc).__name__}: {exc}"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True, type=Path)
    args = ap.parse_args()
    base = args.artifact_dir
    cid = "hz17-starling-7b-improving-helpfulness-and-harmlessne"
    raw = base / "sources" / "raw"
    papers = base / "sources" / "papers"
    manifest = base / "sources" / "manifest.jsonl"
    raw.mkdir(parents=True, exist_ok=True)
    papers.mkdir(parents=True, exist_ok=True)

    endpoints = {
        "api2_notes_forum": "https://api2.openreview.net/notes?forum=GqDntYTTbk",
        "api_notes_forum": "https://api.openreview.net/notes?forum=GqDntYTTbk",
        "api2_note": "https://api2.openreview.net/notes?id=GqDntYTTbk",
        "attachment_pdf": "https://openreview.net/attachment?id=GqDntYTTbk&name=pdf",
        "pdf": "https://openreview.net/pdf?id=GqDntYTTbk",
    }
    records = []
    for label, url in endpoints.items():
        data, final_url, status, err = fetch(url)
        out = raw / f"{cid}-openreview-{label}.bin"
        rec = {
            "candidate_id": cid,
            "url": url,
            "final_url": final_url,
            "http_status": status,
            "artifact_type": "metadata" if "api" in label else "pdf",
            "local_path": str(out),
            "bytes": 0,
            "sha256": None,
            "fetched_at": now_iso(),
            "status": "blocked",
            "selected": True,
            "intended_use": "selected_source",
            "error": err,
        }
        if data:
            out.write_bytes(data)
            rec["bytes"] = len(data)
            rec["sha256"] = sha(data)
            if data.startswith(b"%PDF"):
                pdf_path = papers / f"{cid}.pdf"
                pdf_path.write_bytes(data)
                rec["status"] = "downloaded"
                rec["local_path"] = str(pdf_path)
            else:
                rec["status"] = "downloaded" if "api" in label else "degraded"
                if data[:1] in (b"{", b"["):
                    try:
                        pretty = json.dumps(json.loads(data.decode("utf-8")), indent=2, ensure_ascii=False)
                        json_path = raw / f"{cid}-openreview-{label}.json"
                        json_path.write_text(pretty, encoding="utf-8")
                        rec["local_path"] = str(json_path)
                        rec["bytes"] = json_path.stat().st_size
                        rec["sha256"] = sha(json_path.read_bytes())
                    except Exception:
                        pass
                else:
                    sample = data[:120].decode("utf-8", "replace")
                    rec["error"] = f"not a PDF; sample={sample!r}"
        records.append(rec)
    with manifest.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(records, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
