#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


RESEARCH_MIN_CANDIDATES = 100
RESEARCH_MIN_RAW_ARTIFACTS = 20
RESEARCH_MIN_READ_REPORTS = 5
RESEARCH_MIN_FANOUT_DETAIL_REPORTS = 6
RESEARCH_MIN_SKIM_REPORT_WORDS = 350
RESEARCH_MIN_DEEP_REPORT_WORDS = 1000
RESEARCH_MIN_SKIM_REPORT_REFS = 3
RESEARCH_MIN_DEEP_REPORT_REFS = 10
MIN_SOURCE_SECTION_CITATIONS = 5
MIN_INLINE_CITATION_LINKS = 8
MIN_INLINE_TOTAL_REFS = 14
MIN_CITATION_APPENDIX_ENTRIES = 5
MIN_CITED_PARAGRAPH_RATIO = 0.55
MAX_UNSOURCED_CODE_BLOCK_LINES = 24
RESEARCH_LANE_MINIMUMS = {
    "papers": 25,
    "repos": 25,
    "company_posts": 20,
    "model_training": 10,
    "applied_product": 10,
    "discourse": 10,
}
RESEARCH_REQUIRED_FANOUT_LANES = tuple(RESEARCH_LANE_MINIMUMS.keys())
REQUIRED_HEADINGS = [
    "# Today's Deep Dive",
    "# Skim Cards",
    "# Foundations & Connections",
    "# Pipeline Report",
    "# Tomorrow's Queue",
    "# Errata",
    "# Citation Appendix",
]
DEEPDIVE_HEADINGS = [
    "## TL;DR",
    "## Mental model",
    "## Why this matters now",
    "## Mechanism trace",
    "## Evidence map",
    "## Walkthrough",
    "## Implementation notes",
    "## Try it yourself",
    "## Open questions",
    "## Sources & citations",
]
SOURCE_REF_RE = re.compile(r"`[^`\n]+:\d+(?:-\d+)?`")
CITATION_LINK_RE = re.compile(r"\[(?P<num>\d+)\]\(#(?P<prefix>source|citation)-(?P=num)\)")
CITATION_TARGET_RE = re.compile(
    r"(?:\{#(?:source|citation)-(?P<brace>\d+)\}|<a\s+id=[\"'](?:source|citation)-(?P<html>\d+)[\"']\s*></a>)",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s)>\]]+")
LONG_CODE_SOURCE_RE = re.compile(r"\b(source|derived_from)=['\"][^'\"]+['\"]")
ALLOWED_LONG_CODE_LANGS = {
    "bash",
    "diff",
    "go",
    "json",
    "javascript",
    "python",
    "rust",
    "sql",
    "text",
    "toml",
    "typescript",
    "yaml",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render and verify a Codex-native DeepBrief Markdown file.")
    parser.add_argument("--input", required=True, help="Path to completed brief.md.")
    parser.add_argument("--out", required=True, help="Output artifact directory.")
    parser.add_argument("--template", help="Optional Typst template path.")
    parser.add_argument("--min-pages", type=int, default=8, help="Minimum acceptable PDF pages; daily default is 8.")
    parser.add_argument("--max-pages", type=int, default=30, help="Maximum acceptable PDF pages; daily default is 30.")
    parser.add_argument(
        "--allow-degraded-research",
        action="store_true",
        help="Render even when high-recall research artifact gates fail. Use only after explicit user approval.",
    )
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    template = Path(args.template).expanduser().resolve() if args.template else skill_dir() / "assets" / "brief.typ"

    rendered_md = out_dir / "brief.rendered.md"
    typst_path = out_dir / "brief.typ"
    pdf_path = out_dir / "brief.pdf"
    diagrams_dir = out_dir / "diagrams"

    lint = lint_markdown(source)
    research = check_research_artifacts(out_dir)
    tools = check_tools()
    research_blocking = bool(research["blocking_errors"]) and not args.allow_degraded_research
    if lint["blocking_errors"] or tools["missing"] or research_blocking:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "lint": lint,
                    "research": research,
                    "research_degraded_allowed": args.allow_degraded_research,
                    "tools": tools,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    try:
        diagrams = render_mermaid_blocks(source, rendered_md, diagrams_dir)
    except RuntimeError as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": "mermaid",
                    "reason": str(exc),
                    "hint": "Mermaid CLI uses a headless browser; rerun with browser permissions or fix the Mermaid block.",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    pandoc = run_cmd(
        [
            tools["paths"]["pandoc"],
            "--from",
            "markdown+tex_math_dollars+pipe_tables+fenced_code_attributes",
            "--to",
            "typst",
            "--standalone",
            "--template",
            str(template),
            "--output",
            str(typst_path),
            str(rendered_md),
        ]
    )
    if pandoc["returncode"] != 0:
        print(json.dumps({"status": "failed", "stage": "pandoc", "result": pandoc}, indent=2, sort_keys=True))
        return 2

    typst_text = typst_path.read_text(encoding="utf-8")
    typst_path.write_text(typst_text.replace("#horizontalrule", '#line(length: 100%)'), encoding="utf-8")
    typst = run_cmd([tools["paths"]["typst"], "compile", typst_path.name, pdf_path.name], cwd=out_dir)
    if typst["returncode"] != 0:
        print(json.dumps({"status": "failed", "stage": "typst", "result": typst}, indent=2, sort_keys=True))
        return 2

    post = post_checks(pdf_path, typst_path, diagrams, out_dir, tools, args.min_pages, args.max_pages)
    status = "ok" if post["ok"] else "failed"
    print(
        json.dumps(
            {
                "status": status,
                "brief_md": str(source),
                "rendered_md": str(rendered_md),
                "typst": str(typst_path),
                "pdf": str(pdf_path),
                "lint": lint,
                "research": research,
                "research_degraded_allowed": args.allow_degraded_research,
                "tools": tools,
                "diagrams": diagrams,
                "post_checks": post,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if status == "ok" else 2


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def lint_markdown(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in text]
    missing_deep = [heading for heading in DEEPDIVE_HEADINGS if heading not in text]
    source_section = section(text, "## Sources & citations")
    citations = len(
        [
            line
            for line in source_section.splitlines()
            if "http://" in line or "https://" in line or CITATION_LINK_RE.search(line)
        ]
    )
    visual_refs = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text)) + len(re.findall(r"```mermaid\s+", text))
    inline = inline_evidence_metrics(text)
    appendix = citation_appendix_metrics(text)
    code_blocks = check_code_blocks(text)
    weak_visuals = weak_visual_captions(text)
    errors = []
    if missing:
        errors.append(f"missing top-level headings: {missing}")
    if missing_deep:
        errors.append(f"missing deep-dive headings: {missing_deep}")
    if re.search(r"^## Pseudocode\s*$", text, flags=re.MULTILINE):
        errors.append("old `## Pseudocode` heading is no longer accepted; use `## Mechanism trace` plus real source snippets")
    if citations < MIN_SOURCE_SECTION_CITATIONS:
        errors.append(f"sources section has {citations} citations, expected at least {MIN_SOURCE_SECTION_CITATIONS}")
    if visual_refs < 2:
        errors.append("brief must include at least one explanatory diagram and one visual asset")
    if inline["local_ref_count"] > 0:
        errors.append(
            "body exposes "
            f"{inline['local_ref_count']} internal local evidence refs; use public citation links like [1](#source-1) "
            "and keep local file:line refs in verification/evidence-matrix.*"
        )
    if inline["citation_link_count"] < MIN_INLINE_CITATION_LINKS:
        errors.append(
            f"body has {inline['citation_link_count']} public citation links, expected at least "
            f"{MIN_INLINE_CITATION_LINKS}"
        )
    if inline["total_ref_count"] < MIN_INLINE_TOTAL_REFS:
        errors.append(
            f"body has {inline['total_ref_count']} inline citation links/URLs, expected at least {MIN_INLINE_TOTAL_REFS}"
        )
    if inline["material_paragraph_count"] >= 8 and inline["cited_paragraph_ratio"] < MIN_CITED_PARAGRAPH_RATIO:
        errors.append(
            "only "
            f"{inline['cited_paragraph_ratio']:.0%} of material paragraphs have nearby evidence, "
            f"expected at least {MIN_CITED_PARAGRAPH_RATIO:.0%}"
        )
    for heading, count in inline["key_section_ref_counts"].items():
        if count == 0:
            errors.append(f"{heading} has no inline public citation links or source URLs")
    errors.extend(appendix["blocking_errors"])
    errors.extend(code_blocks["blocking_errors"])
    errors.extend(weak_visuals)
    return {
        "blocking_errors": errors,
        "citation_count": citations,
        "citation_appendix": appendix,
        "visual_refs": visual_refs,
        "inline_evidence": inline,
        "code_blocks": code_blocks["blocks"],
        "weak_visual_warnings": weak_visuals,
    }


def inline_evidence_metrics(text: str) -> dict[str, Any]:
    body = before_top_level_section(text, "# Citation Appendix")
    visible_body = strip_fenced_code(body)
    local_refs = SOURCE_REF_RE.findall(visible_body)
    citation_links = CITATION_LINK_RE.findall(visible_body)
    urls = URL_RE.findall(visible_body)
    key_sections = [
        "## Why this matters now",
        "## Mechanism trace",
        "## Evidence map",
        "## Walkthrough",
        "## Implementation notes",
    ]
    key_counts = {
        heading: len(CITATION_LINK_RE.findall(strip_fenced_code(section(text, heading))))
        + len(URL_RE.findall(strip_fenced_code(section(text, heading))))
        for heading in key_sections
    }
    paragraphs = material_paragraphs(visible_body)
    cited = [paragraph for paragraph in paragraphs if CITATION_LINK_RE.search(paragraph) or URL_RE.search(paragraph)]
    ratio = (len(cited) / len(paragraphs)) if paragraphs else 1.0
    return {
        "local_ref_count": len(local_refs),
        "citation_link_count": len(citation_links),
        "url_count": len(urls),
        "total_ref_count": len(citation_links) + len(urls),
        "material_paragraph_count": len(paragraphs),
        "cited_paragraph_count": len(cited),
        "cited_paragraph_ratio": ratio,
        "key_section_ref_counts": key_counts,
    }


def citation_appendix_metrics(text: str) -> dict[str, Any]:
    body = before_top_level_section(text, "# Citation Appendix")
    appendix = top_level_section(text, "# Citation Appendix")
    errors: list[str] = []
    used_ids = citation_ids(body)
    target_ids = citation_target_ids(appendix)
    urls = URL_RE.findall(appendix)

    if not appendix.strip():
        errors.append("missing # Citation Appendix with public title and URL entries")
    if len(target_ids) < MIN_CITATION_APPENDIX_ENTRIES:
        errors.append(
            f"citation appendix has {len(target_ids)} anchored entries, expected at least "
            f"{MIN_CITATION_APPENDIX_ENTRIES}"
        )
    if len(urls) < len(target_ids):
        errors.append(
            f"citation appendix has {len(target_ids)} anchored entries but only {len(urls)} public URLs"
        )
    missing_targets = sorted(used_ids - target_ids, key=int)
    if missing_targets:
        errors.append(f"citation links missing appendix targets: {missing_targets}")

    return {
        "blocking_errors": errors,
        "used_ids": sorted(used_ids, key=int),
        "target_ids": sorted(target_ids, key=int),
        "entry_count": len(target_ids),
        "url_count": len(urls),
    }


def citation_ids(text: str) -> set[str]:
    return {match.group("num") for match in CITATION_LINK_RE.finditer(strip_fenced_code(text))}


def citation_target_ids(text: str) -> set[str]:
    ids: set[str] = set()
    for match in CITATION_TARGET_RE.finditer(strip_fenced_code(text)):
        value = match.group("brace") or match.group("html")
        if value:
            ids.add(value)
    return ids


def strip_fenced_code(text: str) -> str:
    return re.sub(r"^```.*?^```", "", text, flags=re.DOTALL | re.MULTILINE)


def before_top_level_section(markdown: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
    return markdown[: match.start()] if match else markdown


def top_level_section(markdown: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
    if not match:
        return ""
    rest = markdown[match.end() :]
    next_heading = re.search(r"^# (?!#)", rest, flags=re.MULTILINE)
    return rest[: next_heading.start()] if next_heading else rest


def material_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            if current:
                maybe_add_paragraph(paragraphs, " ".join(current))
                current = []
            continue
        if stripped.startswith("#") or stripped.startswith("|") or re.match(r"^[-*+]\s+", stripped):
            if current:
                maybe_add_paragraph(paragraphs, " ".join(current))
                current = []
            if re.match(r"^[-*+]\s+", stripped):
                maybe_add_paragraph(paragraphs, stripped)
            continue
        current.append(stripped)
    if current:
        maybe_add_paragraph(paragraphs, " ".join(current))
    return paragraphs


def maybe_add_paragraph(paragraphs: list[str], paragraph: str) -> None:
    words = re.findall(r"\b[\w'-]+\b", paragraph)
    if len(words) >= 12:
        paragraphs.append(paragraph)


def check_code_blocks(text: str) -> dict[str, Any]:
    errors: list[str] = []
    blocks: list[dict[str, Any]] = []
    for match in re.finditer(r"^```([^\n]*)\n(.*?)^```", text, flags=re.DOTALL | re.MULTILINE):
        info = match.group(1).strip()
        body = match.group(2)
        language = info.split()[0].lower() if info else ""
        line_count = len([line for line in body.splitlines() if line.strip()])
        block = {"info": info, "language": language, "line_count": line_count}
        blocks.append(block)
        if language in {"mermaid", "tex"}:
            continue
        if line_count > MAX_UNSOURCED_CODE_BLOCK_LINES:
            if language not in ALLOWED_LONG_CODE_LANGS or not LONG_CODE_SOURCE_RE.search(info):
                errors.append(
                    "code block with "
                    f"{line_count} lines must use a real language and `source=` or `derived_from=` fence attribute"
                )
        if language in {"", "text"} and line_count > 12 and re.search(r"\b(function|class|if|else|return)\b", body):
            if not LONG_CODE_SOURCE_RE.search(info):
                errors.append("long text-like code block looks like pseudocode but lacks `source=` or `derived_from=`")
    return {"blocking_errors": errors, "blocks": blocks}


def weak_visual_captions(text: str) -> list[str]:
    errors: list[str] = []
    if re.search(r"Mermaid diagram\s+\d+", text, flags=re.I):
        errors.append("generic Mermaid diagram caption found; caption must explain the diagram's point")
    for alt, path in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text):
        alt_text = alt.strip().lower()
        if "page extracted" in alt_text and not re.search(r"annotated|cropped|callout|highlight", alt_text):
            errors.append(f"image {path!r} looks like an unannotated extracted page; crop or annotate it")
        if alt_text in {"image", "diagram", "figure", "screenshot", "mermaid diagram"}:
            errors.append(f"image {path!r} has a generic alt text/caption")
    return errors


def check_research_artifacts(output_dir: Path) -> dict[str, Any]:
    sources_dir = output_dir / "sources"
    reviews_dir = output_dir / "reviews"
    verification_dir = output_dir / "verification"
    candidates_path = sources_dir / "candidates.jsonl"
    manifest_path = sources_dir / "manifest.jsonl"
    fanout_path = reviews_dir / "fanout-report.md"
    evidence_paths = [
        verification_dir / "evidence-matrix.md",
        verification_dir / "evidence-matrix.jsonl",
    ]

    errors: list[str] = []
    warnings: list[str] = []

    candidates, candidate_errors = read_jsonl(candidates_path)
    manifest, manifest_errors = read_jsonl(manifest_path)
    errors.extend(candidate_errors)
    errors.extend(manifest_errors)

    distinct_candidates = {candidate_key(row) for row in candidates if candidate_key(row)}
    lane_candidate_keys: dict[str, set[str]] = {}
    for row in candidates:
        key = candidate_key(row)
        if not key:
            continue
        lane = str(row.get("lane", "")).strip()
        lane_candidate_keys.setdefault(lane, set()).add(key)
    lane_counts = {lane: len(keys) for lane, keys in lane_candidate_keys.items()}
    downloaded_artifacts = [row for row in manifest if artifact_exists(output_dir, row)]
    selected_manifest_rows = [row for row in manifest if artifact_selected(row)]
    selected_artifacts = [row for row in selected_manifest_rows if artifact_exists(output_dir, row)]
    selected_missing_candidate_id = [
        row for row in selected_manifest_rows if not str(row.get("candidate_id") or "").strip()
    ]
    selected_missing_artifact = [row for row in selected_manifest_rows if not artifact_exists(output_dir, row)]
    repo_artifacts = [
        row
        for row in downloaded_artifacts
        if str(row.get("artifact_type", "")).lower()
        in {"repo_diff", "repo_file", "repo_checkout", "commit", "tag", "release_diff"}
        or str(row.get("local_path", "")).startswith("repos/")
    ]
    degraded_artifacts = [
        row
        for row in manifest
        if str(row.get("status", "")).lower() in {"degraded", "blocked", "failed"}
    ]
    read_reports = sorted(
        path
        for path in reviews_dir.glob("*.md")
        if path.name != "fanout-report.md" and path.is_file() and path.stat().st_size > 0
    )
    fanout_detail_reports = sorted((reviews_dir / "fanout").glob("*.md")) + sorted(
        (reviews_dir / "subagents").glob("*.md")
    )
    fanout_detail_lanes = fanout_lanes(fanout_detail_reports)
    missing_fanout_lanes = [
        lane for lane in RESEARCH_REQUIRED_FANOUT_LANES if lane not in fanout_detail_lanes
    ]
    evidence_path = next((path for path in evidence_paths if path.exists() and path.stat().st_size > 0), None)
    selected_report_requirements = report_requirements(selected_artifacts)
    report_quality = check_read_report_quality(reviews_dir, selected_report_requirements)

    if not candidates_path.exists():
        errors.append(f"missing candidate log: {candidates_path}")
    if len(distinct_candidates) < RESEARCH_MIN_CANDIDATES:
        errors.append(
            f"candidate log has {len(distinct_candidates)} distinct candidates, expected at least {RESEARCH_MIN_CANDIDATES}"
        )
    for lane, minimum in RESEARCH_LANE_MINIMUMS.items():
        if lane_counts.get(lane, 0) < minimum:
            errors.append(f"candidate lane {lane!r} has {lane_counts.get(lane, 0)} candidates, expected at least {minimum}")
    if not manifest_path.exists():
        errors.append(f"missing raw artifact manifest: {manifest_path}")
    if len(downloaded_artifacts) < RESEARCH_MIN_RAW_ARTIFACTS:
        errors.append(
            f"manifest has {len(downloaded_artifacts)} locally saved raw artifacts, expected at least {RESEARCH_MIN_RAW_ARTIFACTS}"
        )
    if not selected_manifest_rows:
        errors.append("manifest has no selected-source artifact records")
    if selected_missing_candidate_id:
        errors.append(
            f"manifest has {len(selected_missing_candidate_id)} selected-source artifact records missing candidate_id"
        )
    if selected_missing_artifact:
        errors.append(
            f"manifest has {len(selected_missing_artifact)} selected-source artifact records without a saved local artifact"
        )
    if not fanout_path.exists() or fanout_path.stat().st_size == 0:
        errors.append(f"missing fanout report: {fanout_path}")
    if len(fanout_detail_reports) < RESEARCH_MIN_FANOUT_DETAIL_REPORTS:
        errors.append(
            "found "
            f"{len(fanout_detail_reports)} raw fanout/subagent detail reports, expected at least "
            f"{RESEARCH_MIN_FANOUT_DETAIL_REPORTS} under reviews/fanout/ or reviews/subagents/"
        )
    if missing_fanout_lanes:
        errors.append(f"missing raw fanout detail reports for lanes: {missing_fanout_lanes}")
    if len(read_reports) < RESEARCH_MIN_READ_REPORTS:
        errors.append(
            f"found {len(read_reports)} per-source read reports, expected at least {RESEARCH_MIN_READ_REPORTS}"
        )
    errors.extend(report_quality["blocking_errors"])
    if evidence_path is None:
        errors.append(f"missing evidence matrix: one of {[str(path) for path in evidence_paths]}")
    if not repo_artifacts:
        warnings.append("manifest has no repo diff/checkouts; this is acceptable only if no selected repo items are used")
    if not any((output_dir / "images").glob("*")):
        warnings.append("images/ has no downloaded source visuals; Errata should explain if no source visual was available")

    return {
        "blocking_errors": errors,
        "warnings": warnings,
        "candidate_count": len(distinct_candidates),
        "raw_artifact_count": len(downloaded_artifacts),
        "selected_manifest_count": len(selected_manifest_rows),
        "selected_artifact_count": len(selected_artifacts),
        "selected_missing_candidate_id_count": len(selected_missing_candidate_id),
        "selected_missing_artifact_count": len(selected_missing_artifact),
        "repo_artifact_count": len(repo_artifacts),
        "degraded_artifact_count": len(degraded_artifacts),
        "read_report_count": len(read_reports),
        "fanout_detail_report_count": len(fanout_detail_reports),
        "fanout_detail_lanes": sorted(fanout_detail_lanes),
        "missing_fanout_lanes": missing_fanout_lanes,
        "lane_counts": dict(sorted(lane_counts.items())),
        "lane_minimums": RESEARCH_LANE_MINIMUMS,
        "read_report_quality": report_quality["reports"],
        "paths": {
            "candidates": str(candidates_path),
            "manifest": str(manifest_path),
            "fanout_report": str(fanout_path),
            "fanout_detail_reports": [str(path) for path in fanout_detail_reports],
            "evidence_matrix": str(evidence_path) if evidence_path else None,
            "read_reports": [str(path) for path in read_reports],
        },
    }


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{index} is not valid JSON: {exc.msg}")
            continue
        if not isinstance(parsed, dict):
            errors.append(f"{path}:{index} is not a JSON object")
            continue
        rows.append(parsed)
    return rows, errors


def candidate_key(row: dict[str, Any]) -> str:
    for key in ("id", "dedupe_key", "url", "title"):
        value = row.get(key)
        if value:
            return str(value)
    return ""


def artifact_exists(output_dir: Path, row: dict[str, Any]) -> bool:
    local_path = row.get("local_path")
    if not local_path:
        return False
    path = Path(str(local_path)).expanduser()
    if not path.is_absolute():
        path = output_dir / path
    try:
        if path.is_file():
            return path.stat().st_size > 0
        if path.is_dir():
            return any(child.is_file() and child.stat().st_size > 0 for child in path.rglob("*"))
        return False
    except OSError:
        return False


def artifact_selected(row: dict[str, Any]) -> bool:
    intended_use = str(row.get("intended_use", "")).lower()
    return bool(row.get("selected")) or intended_use in {
        "selected_source",
        "deep_dive",
        "skim",
        "verification",
        "visual",
    }


def fanout_lanes(paths: list[Path]) -> set[str]:
    lanes: set[str] = set()
    aliases = {
        "paper": "papers",
        "papers": "papers",
        "evals": "papers",
        "repo": "repos",
        "repos": "repos",
        "release": "repos",
        "releases": "repos",
        "company": "company_posts",
        "company_posts": "company_posts",
        "engineering_posts": "company_posts",
        "model": "model_training",
        "model_training": "model_training",
        "inference": "model_training",
        "applied": "applied_product",
        "applied_product": "applied_product",
        "document_ai": "applied_product",
        "discourse": "discourse",
        "builder_discourse": "discourse",
        "builders": "discourse",
    }
    for path in paths:
        normalized = normalize_report_id(path.stem)
        text = path.read_text(encoding="utf-8", errors="ignore")[:2000].lower()
        haystack = f"{normalized} {text}"
        for token, lane in aliases.items():
            if re.search(rf"(^|[^a-z0-9]){re.escape(token)}([^a-z0-9]|$)", haystack):
                lanes.add(lane)
    return lanes


def report_requirements(selected_artifacts: list[dict[str, Any]]) -> dict[str, str]:
    requirements: dict[str, str] = {}
    for row in selected_artifacts:
        candidate_id = str(row.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        intended_use = str(row.get("intended_use", "")).lower()
        current = requirements.get(candidate_id, "skim")
        if intended_use == "deep_dive":
            requirements[candidate_id] = "deep_dive"
        elif current != "deep_dive" and intended_use in {"skim", "selected_source", "verification", "visual"}:
            requirements[candidate_id] = "skim"
    return requirements


def check_read_report_quality(reviews_dir: Path, requirements: dict[str, str]) -> dict[str, Any]:
    errors: list[str] = []
    reports: dict[str, Any] = {}
    for candidate_id, kind in sorted(requirements.items()):
        path = find_read_report(reviews_dir, candidate_id)
        if path is None:
            errors.append(f"missing read report for selected source {candidate_id!r}")
            reports[candidate_id] = {"kind": kind, "path": None, "word_count": 0, "evidence_ref_count": 0}
            continue
        text = path.read_text(encoding="utf-8")
        word_count = len(re.findall(r"\b[\w'-]+\b", text))
        evidence_ref_count = len(re.findall(r"`[^`]+:\d+`", text))
        min_words = RESEARCH_MIN_DEEP_REPORT_WORDS if kind == "deep_dive" else RESEARCH_MIN_SKIM_REPORT_WORDS
        min_refs = RESEARCH_MIN_DEEP_REPORT_REFS if kind == "deep_dive" else RESEARCH_MIN_SKIM_REPORT_REFS
        report = {
            "kind": kind,
            "path": str(path),
            "word_count": word_count,
            "evidence_ref_count": evidence_ref_count,
        }
        reports[candidate_id] = report
        if word_count < min_words:
            errors.append(
                f"read report for {candidate_id!r} has {word_count} words, expected at least {min_words} for {kind}"
            )
        if evidence_ref_count < min_refs:
            errors.append(
                f"read report for {candidate_id!r} has {evidence_ref_count} local evidence refs, expected at least {min_refs}"
            )
        if kind == "deep_dive" and not re.search(r"figure|table|file inventory|artifact inventory", text, re.I):
            errors.append(
                f"deep-dive read report for {candidate_id!r} must include figure/table or file/artifact inventory"
            )
    return {"blocking_errors": errors, "reports": reports}


def find_read_report(reviews_dir: Path, candidate_id: str) -> Path | None:
    exact = reviews_dir / f"{candidate_id}.md"
    if exact.exists() and exact.is_file():
        return exact
    normalized = normalize_report_id(candidate_id)
    for path in reviews_dir.glob("*.md"):
        if path.name == "fanout-report.md":
            continue
        if normalize_report_id(path.stem) == normalized:
            return path
    return None


def normalize_report_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def section(markdown: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
    if not match:
        return ""
    level = len(heading) - len(heading.lstrip("#"))
    rest = markdown[match.end() :]
    next_heading = re.search(rf"^#{{1,{level}}} ", rest, flags=re.MULTILINE)
    return rest[: next_heading.start()] if next_heading else rest


def check_tools() -> dict[str, Any]:
    required = ["mmdc", "pandoc", "typst", "pdftoppm", "pdfinfo", "pdffonts", "pdftotext"]
    paths = {tool: shutil.which(tool) for tool in required}
    missing = [tool for tool, path in paths.items() if path is None]
    return {"missing": missing, "paths": paths}


def render_mermaid_blocks(source: Path, rendered: Path, diagrams_dir: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    diagram_paths: list[str] = []
    diagram_reports: list[dict[str, Any]] = []
    config = write_mermaid_config(diagrams_dir)

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        stem = f"diagram_{count:02d}"
        mmd = diagrams_dir / f"{stem}.mmd"
        diagram = diagrams_dir / f"{stem}.png"
        source_text = match.group(1).strip()
        quality = inspect_mermaid_source(source_text)
        diagram_reports.append({"path": str(mmd), **quality})
        if quality["blocking_errors"]:
            raise RuntimeError(f"Mermaid diagram {count} is too weak: {quality['blocking_errors']}")
        mmd.write_text(source_text + "\n", encoding="utf-8")
        result = run_cmd(
            [
                "mmdc",
                "-i",
                str(mmd),
                "-o",
                str(diagram),
                "-b",
                "white",
                "-t",
                "neutral",
                "-c",
                str(config),
            ]
        )
        if result["returncode"] != 0:
            raise RuntimeError(result["stderr"] or result["stdout"] or "mmdc failed")
        diagram_paths.append(str(diagram))
        rel = diagram.relative_to(rendered.parent).as_posix()
        return f"\n![DeepBrief mechanism diagram {count}]({rel}){{ width=95% }}\n"

    converted = re.sub(r"```mermaid\s*\n(.*?)```", replace, text, flags=re.DOTALL)
    converted = normalize_source_code_fences(converted)
    rendered.write_text(converted, encoding="utf-8")
    return {"count": count, "diagram_paths": diagram_paths, "reports": diagram_reports}


def normalize_source_code_fences(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        language = match.group(1)
        attrs = match.group(2).strip()
        return f"```{{.{language} {attrs}}}"

    return re.sub(
        r"^```([A-Za-z0-9_+-]+)\s+((?:(?:source|derived_from)=['\"][^'\"]+['\"]\s*)+)$",
        replace,
        text,
        flags=re.MULTILINE,
    )


def write_mermaid_config(diagrams_dir: Path) -> Path:
    config = diagrams_dir / "mermaid-config.json"
    config.write_text(
        json.dumps(
            {
                "theme": "neutral",
                "flowchart": {"htmlLabels": False, "curve": "basis"},
                "themeVariables": {
                    "background": "#ffffff",
                    "primaryColor": "#f4f8f6",
                    "primaryTextColor": "#111827",
                    "primaryBorderColor": "#2f6f63",
                    "lineColor": "#4b5563",
                    "secondaryColor": "#fff6e5",
                    "tertiaryColor": "#eef2ff",
                    "fontFamily": "Arial, sans-serif",
                    "fontSize": "16px",
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return config


def inspect_mermaid_source(source_text: str) -> dict[str, Any]:
    edges = len(re.findall(r"[-.=]+>|--", source_text))
    labels = len(re.findall(r"\[[^\]]{3,}\]|\([^)]{3,}\)|\{[^}]{3,}\}", source_text))
    errors: list[str] = []
    if edges < 3:
        errors.append(f"has {edges} edges, expected at least 3")
    if labels < 4:
        errors.append(f"has {labels} labeled nodes, expected at least 4")
    if "Mermaid diagram" in source_text:
        errors.append("contains generic Mermaid wording instead of meaningful labels")
    return {"edge_count": edges, "label_count": labels, "blocking_errors": errors}


def post_checks(
    pdf_path: Path,
    typst_path: Path,
    diagrams: dict[str, Any],
    output_dir: Path,
    tools: dict[str, Any],
    min_pages: int,
    max_pages: int,
) -> dict[str, Any]:
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    for stale_png in pages_dir.glob("page-*.png"):
        stale_png.unlink()
    run_cmd([tools["paths"]["pdftoppm"], "-png", "-r", "144", str(pdf_path), str(pages_dir / "page")])
    pdfinfo = run_cmd([tools["paths"]["pdfinfo"], str(pdf_path)])["stdout"]
    pdffonts = run_cmd([tools["paths"]["pdffonts"], str(pdf_path)])["stdout"]
    text = run_cmd([tools["paths"]["pdftotext"], str(pdf_path), "-"])["stdout"]
    page_count = parse_pdf_pages(pdfinfo)
    page_pngs = sorted(pages_dir.glob("page-*.png"))
    typst_text = typst_path.read_text(encoding="utf-8")
    diagram_paths = diagrams.get("diagram_paths", diagrams.get("svg_paths", []))
    diagram_errors = [
        error
        for report in diagrams.get("reports", [])
        for error in report.get("blocking_errors", [])
    ]
    generic_diagram_caption = bool(re.search(r"Mermaid diagram\s+\d+", text, flags=re.I))
    expected_headings_present = all(
        heading.replace("## ", "") in text for heading in ["## Mechanism trace", "## Evidence map", "## Implementation notes"]
    )
    checks = {
        "pdf_nonzero": pdf_path.exists() and pdf_path.stat().st_size > 0,
        "pdf_size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
        "feedback_exists": (output_dir / "feedback.md").exists(),
        "page_count": page_count,
        "page_count_target": {"min": min_pages, "max": max_pages},
        "page_count_ok": min_pages <= page_count <= max_pages,
        "rasterized_pages": len(page_pngs),
        "rasterized_all_pages": len(page_pngs) == page_count,
        "diagram_count": diagrams["count"],
        "diagram_files_exist": all(Path(path).exists() and Path(path).stat().st_size > 0 for path in diagram_paths),
        "typst_references_all_diagrams": all(Path(path).name in typst_text for path in diagram_paths),
        "toc_outline_present": "#outline(" in typst_text,
        "math_text_present": "0.55" in text and "0.25" in text and "0.20" in text,
        "fonts_embedded": fonts_embedded(pdffonts),
        "generic_diagram_caption_absent": not generic_diagram_caption,
        "diagram_quality_ok": not diagram_errors,
        "diagram_quality_errors": diagram_errors,
        "new_deep_dive_headings_present": expected_headings_present,
    }
    checks["ok"] = all(
        [
            checks["pdf_nonzero"],
            checks["feedback_exists"],
            checks["page_count_ok"],
            checks["rasterized_all_pages"],
            checks["diagram_count"] >= 1,
            checks["diagram_files_exist"],
            checks["typst_references_all_diagrams"],
            checks["toc_outline_present"],
            checks["math_text_present"],
            checks["fonts_embedded"],
            checks["generic_diagram_caption_absent"],
            checks["diagram_quality_ok"],
            checks["new_deep_dive_headings_present"],
        ]
    )
    return checks


def parse_pdf_pages(pdfinfo: str) -> int:
    match = re.search(r"^Pages:\s+(\d+)$", pdfinfo, flags=re.MULTILINE)
    return int(match.group(1)) if match else 0


def fonts_embedded(pdffonts: str) -> bool:
    rows = [line for line in pdffonts.splitlines()[2:] if line.strip()]
    return bool(rows) and all(" yes " in f" {row} " for row in rows)


def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    env = {**os.environ}
    env.setdefault("PUPPETEER_CACHE_DIR", str(Path.cwd() / ".cache" / "puppeteer"))
    completed = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
