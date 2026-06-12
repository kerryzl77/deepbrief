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
REQUIRED_HEADINGS = [
    "# Today's Deep Dive",
    "# Skim Cards",
    "# Foundations & Connections",
    "# Pipeline Report",
    "# Tomorrow's Queue",
    "# Errata",
]
DEEPDIVE_HEADINGS = [
    "## TL;DR",
    "## Mental model",
    "## Pseudocode",
    "## Walkthrough",
    "## What prompts are injected",
    "## Try it yourself",
    "## Open questions",
    "## Sources & citations",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render and verify a Codex-native DeepBrief Markdown file.")
    parser.add_argument("--input", required=True, help="Path to completed brief.md.")
    parser.add_argument("--out", required=True, help="Output artifact directory.")
    parser.add_argument("--template", help="Optional Typst template path.")
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

    post = post_checks(pdf_path, typst_path, diagrams, out_dir, tools)
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
    pseudocode = re.search(r"## Pseudocode\s+```[^\n]*\n(.*?)```", text, flags=re.DOTALL)
    pseudocode_lines = 0
    if pseudocode:
        pseudocode_lines = len([line for line in pseudocode.group(1).splitlines() if line.strip()])
    citations = len([line for line in section(text, "## Sources & citations").splitlines() if "http://" in line or "https://" in line or re.search(r"`[^`]+:\d+`", line)])
    visual_refs = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text)) + len(re.findall(r"```mermaid\s+", text))
    errors = []
    if missing:
        errors.append(f"missing top-level headings: {missing}")
    if missing_deep:
        errors.append(f"missing deep-dive headings: {missing_deep}")
    if not 30 <= pseudocode_lines <= 80:
        errors.append(f"pseudocode block has {pseudocode_lines} nonblank lines, expected 30-80")
    if citations < 3:
        errors.append(f"sources section has {citations} citations, expected at least 3")
    if visual_refs < 1:
        errors.append("brief must include at least one image or Mermaid diagram")
    return {
        "blocking_errors": errors,
        "pseudocode_lines": pseudocode_lines,
        "citation_count": citations,
        "visual_refs": visual_refs,
    }


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
    downloaded_artifacts = [row for row in manifest if artifact_exists(output_dir, row)]
    selected_artifacts = [row for row in downloaded_artifacts if artifact_selected(row)]
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
    evidence_path = next((path for path in evidence_paths if path.exists() and path.stat().st_size > 0), None)

    if not candidates_path.exists():
        errors.append(f"missing candidate log: {candidates_path}")
    if len(distinct_candidates) < RESEARCH_MIN_CANDIDATES:
        errors.append(
            f"candidate log has {len(distinct_candidates)} distinct candidates, expected at least {RESEARCH_MIN_CANDIDATES}"
        )
    if not manifest_path.exists():
        errors.append(f"missing raw artifact manifest: {manifest_path}")
    if len(downloaded_artifacts) < RESEARCH_MIN_RAW_ARTIFACTS:
        errors.append(
            f"manifest has {len(downloaded_artifacts)} locally saved raw artifacts, expected at least {RESEARCH_MIN_RAW_ARTIFACTS}"
        )
    if not fanout_path.exists() or fanout_path.stat().st_size == 0:
        errors.append(f"missing fanout report: {fanout_path}")
    if len(read_reports) < RESEARCH_MIN_READ_REPORTS:
        errors.append(
            f"found {len(read_reports)} per-source read reports, expected at least {RESEARCH_MIN_READ_REPORTS}"
        )
    if evidence_path is None:
        errors.append(f"missing evidence matrix: one of {[str(path) for path in evidence_paths]}")
    if not selected_artifacts:
        warnings.append("manifest has no selected-source artifact records")
    if not repo_artifacts:
        warnings.append("manifest has no repo diff/checkouts; this is acceptable only if no selected repo items are used")
    if not any((output_dir / "images").glob("*")):
        warnings.append("images/ has no downloaded source visuals; Errata should explain if no source visual was available")

    return {
        "blocking_errors": errors,
        "warnings": warnings,
        "candidate_count": len(distinct_candidates),
        "raw_artifact_count": len(downloaded_artifacts),
        "selected_artifact_count": len(selected_artifacts),
        "repo_artifact_count": len(repo_artifacts),
        "degraded_artifact_count": len(degraded_artifacts),
        "read_report_count": len(read_reports),
        "paths": {
            "candidates": str(candidates_path),
            "manifest": str(manifest_path),
            "fanout_report": str(fanout_path),
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


def section(markdown: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$", markdown, flags=re.MULTILINE)
    if not match:
        return ""
    rest = markdown[match.end() :]
    next_heading = re.search(r"^## ", rest, flags=re.MULTILINE)
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
    svg_paths: list[str] = []

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        stem = f"diagram_{count:02d}"
        mmd = diagrams_dir / f"{stem}.mmd"
        svg = diagrams_dir / f"{stem}.svg"
        mmd.write_text(match.group(1).strip() + "\n", encoding="utf-8")
        result = run_cmd(["mmdc", "-i", str(mmd), "-o", str(svg), "-b", "transparent"])
        if result["returncode"] != 0:
            raise RuntimeError(result["stderr"] or result["stdout"] or "mmdc failed")
        svg_paths.append(str(svg))
        rel = svg.relative_to(rendered.parent).as_posix()
        return f"\n![Mermaid diagram {count}]({rel}){{ width=95% }}\n"

    converted = re.sub(r"```mermaid\s*\n(.*?)```", replace, text, flags=re.DOTALL)
    rendered.write_text(converted, encoding="utf-8")
    return {"count": count, "svg_paths": svg_paths}


def post_checks(pdf_path: Path, typst_path: Path, diagrams: dict[str, Any], output_dir: Path, tools: dict[str, Any]) -> dict[str, Any]:
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    run_cmd([tools["paths"]["pdftoppm"], "-png", "-r", "144", str(pdf_path), str(pages_dir / "page")])
    pdfinfo = run_cmd([tools["paths"]["pdfinfo"], str(pdf_path)])["stdout"]
    pdffonts = run_cmd([tools["paths"]["pdffonts"], str(pdf_path)])["stdout"]
    text = run_cmd([tools["paths"]["pdftotext"], str(pdf_path), "-"])["stdout"]
    page_count = parse_pdf_pages(pdfinfo)
    page_pngs = sorted(pages_dir.glob("page-*.png"))
    typst_text = typst_path.read_text(encoding="utf-8")
    checks = {
        "pdf_nonzero": pdf_path.exists() and pdf_path.stat().st_size > 0,
        "pdf_size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
        "feedback_exists": (output_dir / "feedback.md").exists(),
        "page_count": page_count,
        "page_count_ok": 8 <= page_count <= 30,
        "rasterized_pages": len(page_pngs),
        "rasterized_all_pages": len(page_pngs) == page_count,
        "svg_count": diagrams["count"],
        "svg_files_exist": all(Path(path).exists() and Path(path).stat().st_size > 0 for path in diagrams["svg_paths"]),
        "typst_references_all_svgs": all(Path(path).name in typst_text for path in diagrams["svg_paths"]),
        "toc_outline_present": "#outline(" in typst_text,
        "math_text_present": "0.55" in text and "0.25" in text and "0.20" in text,
        "fonts_embedded": fonts_embedded(pdffonts),
    }
    checks["ok"] = all(
        [
            checks["pdf_nonzero"],
            checks["feedback_exists"],
            checks["page_count_ok"],
            checks["rasterized_all_pages"],
            checks["svg_count"] >= 1,
            checks["svg_files_exist"],
            checks["typst_references_all_svgs"],
            checks["toc_outline_present"],
            checks["math_text_present"],
            checks["fonts_embedded"],
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
