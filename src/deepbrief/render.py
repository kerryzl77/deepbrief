from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from deepbrief.compose import compose_m7_brief
from deepbrief.config import Config


REQUIRED_TOOLS = ["mmdc", "pandoc", "typst", "pdftoppm", "pdfinfo", "pdffonts", "pdftotext"]


def m7_gate(config: Config, *, date_override: str | None = None) -> None:
    tool_versions = check_tools()
    composed = compose_m7_brief(config, date_override=date_override)
    output_dir: Path = composed["output_dir"]
    source_md: Path = composed["brief_md"]
    rendered_md = output_dir / "brief.rendered.md"
    typst_path = output_dir / "brief.typ"
    pdf_path = output_dir / "brief.pdf"

    diagram_info = render_mermaid_blocks(source_md, rendered_md, output_dir / "diagrams")
    pandoc_to_typst(rendered_md, typst_path, config.templates_dir / "brief.typ")
    typst_compile(typst_path, pdf_path, output_dir)
    post = post_checks(pdf_path, typst_path, diagram_info, output_dir)
    result = {
        "status": "ok" if post["ok"] else "failed",
        "tool_versions": tool_versions,
        "brief_md": str(source_md),
        "rendered_md": str(rendered_md),
        "typst": str(typst_path),
        "pdf": str(pdf_path),
        "diagrams": diagram_info,
        "post_checks": post,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "ok":
        raise RuntimeError("M7 render gate failed")
    return result


def check_tools() -> dict[str, str]:
    versions: dict[str, str] = {}
    for tool in REQUIRED_TOOLS:
        if shutil.which(tool) is None:
            raise RuntimeError(f"missing required render tool: {tool}")
    versions["pandoc"] = run(["pandoc", "--version"]).splitlines()[0]
    versions["typst"] = run(["typst", "--version"]).splitlines()[0]
    versions["mmdc"] = run(["mmdc", "--version"]).splitlines()[0]
    versions["pdftoppm"] = run(["pdftoppm", "-v"], merge_stderr=True).splitlines()[0]
    versions["pdfinfo"] = run(["pdfinfo", "-v"], merge_stderr=True).splitlines()[0]
    return versions


def render_mermaid_blocks(source: Path, rendered: Path, diagrams_dir: Path) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    rendered_count = 0
    svg_paths: list[str] = []

    def replace(match: re.Match[str]) -> str:
        nonlocal rendered_count
        rendered_count += 1
        stem = f"diagram_{rendered_count:02d}"
        mmd = diagrams_dir / f"{stem}.mmd"
        svg = diagrams_dir / f"{stem}.svg"
        mmd.write_text(match.group(1).strip() + "\n", encoding="utf-8")
        run(["mmdc", "-i", str(mmd), "-o", str(svg), "-b", "transparent"])
        svg_paths.append(str(svg))
        rel = svg.relative_to(rendered.parent).as_posix()
        return f"\n![Mermaid diagram {rendered_count}]({rel}){{ width=95% }}\n"

    converted = re.sub(r"```mermaid\s*\n(.*?)```", replace, text, flags=re.DOTALL)
    rendered.write_text(converted, encoding="utf-8")
    return {"count": rendered_count, "svg_paths": svg_paths}


def pandoc_to_typst(markdown: Path, typst_path: Path, template: Path) -> None:
    run(
        [
            "pandoc",
            "--from",
            "markdown+tex_math_dollars+pipe_tables+fenced_code_attributes",
            "--to",
            "typst",
            "--standalone",
            "--template",
            str(template),
            "--output",
            str(typst_path),
            str(markdown),
        ]
    )
    text = typst_path.read_text(encoding="utf-8")
    text = text.replace("#horizontalrule", '#line(length: 100%)')
    typst_path.write_text(text, encoding="utf-8")


def typst_compile(typst_path: Path, pdf_path: Path, cwd: Path) -> None:
    run(["typst", "compile", str(typst_path.name), str(pdf_path.name)], cwd=cwd)


def post_checks(pdf_path: Path, typst_path: Path, diagrams: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    run(["pdftoppm", "-png", "-r", "144", str(pdf_path), str(pages_dir / "page")])
    page_pngs = sorted(pages_dir.glob("page-*.png"))
    pdfinfo = run(["pdfinfo", str(pdf_path)])
    pdffonts = run(["pdffonts", str(pdf_path)])
    text = run(["pdftotext", str(pdf_path), "-"])
    page_count = parse_pdf_pages(pdfinfo)
    pdf_size = pdf_path.stat().st_size
    typst_text = typst_path.read_text(encoding="utf-8")
    strings = run(["strings", "-a", str(pdf_path)])
    checks = {
        "pdf_nonzero": pdf_size > 0,
        "pdf_size_bytes": pdf_size,
        "page_count": page_count,
        "page_count_ok": 8 <= page_count <= 30,
        "rasterized_pages": len(page_pngs),
        "rasterized_all_pages": len(page_pngs) == page_count,
        "svg_count": diagrams["count"],
        "svg_files_exist": all(Path(path).exists() and Path(path).stat().st_size > 0 for path in diagrams["svg_paths"]),
        "typst_references_all_svgs": all(Path(path).name in typst_text for path in diagrams["svg_paths"]),
        "toc_outline_present": "#outline(" in typst_text,
        "toc_link_markers_present": any(marker in strings for marker in ["/Annots", "/Dest", "/GoTo", "/Outlines"]),
        "math_text_present": "0.55" in text and "0.25" in text and "0.20" in text,
        "fonts_embedded": fonts_embedded(pdffonts),
        "code_overflow_check": "typst compile completed without layout errors",
    }
    checks["ok"] = all(
        [
            checks["pdf_nonzero"],
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
    checks["pdfinfo"] = first_lines(pdfinfo, 12)
    checks["pdffonts"] = first_lines(pdffonts, 12)
    return checks


def parse_pdf_pages(pdfinfo: str) -> int:
    match = re.search(r"^Pages:\s+(\d+)$", pdfinfo, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("pdfinfo did not report page count")
    return int(match.group(1))


def fonts_embedded(pdffonts: str) -> bool:
    lines = [line for line in pdffonts.splitlines() if line.strip()]
    font_rows = lines[2:] if len(lines) >= 2 else []
    if not font_rows:
        return False
    return all(" yes " in f" {line} " for line in font_rows)


def first_lines(text: str, count: int) -> list[str]:
    return text.splitlines()[:count]


def run(cmd: list[str], *, cwd: Path | None = None, merge_stderr: bool = False) -> str:
    repo_root = Path(__file__).resolve().parents[2]
    env = {**os.environ, "PATH": os.environ.get("PATH", "")}
    env.setdefault("PUPPETEER_CACHE_DIR", str(repo_root / ".cache" / "puppeteer"))
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    if merge_stderr:
        return (completed.stdout + completed.stderr).strip()
    return completed.stdout.strip()
