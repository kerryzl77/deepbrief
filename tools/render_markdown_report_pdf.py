#!/usr/bin/env python3
"""Minimal Markdown-to-PDF renderer for locally authored DeepBrief reports."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)

    def link_repl(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        if url.startswith("#"):
            return f"<font color='#1f5f99'>{label}</font>"
        return f"<a href='{html.escape(url, quote=True)}' color='#1f5f99'>{label}</a>"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    return text


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawString(doc.leftMargin, 0.35 * inch, "Hanlin Zhu paper survey - Codex-native DeepBrief")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.35 * inch, str(canvas.getPageNumber()))
    canvas.restoreState()


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def parse_table(lines: list[str], styles, doc_width: float) -> Table:
    rows: list[list[Paragraph]] = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append([Paragraph(inline(c), styles["TableCell"]) for c in cells])
    if not rows:
        return Table([[""]])
    ncols = max(len(r) for r in rows)
    for row in rows:
        while len(row) < ncols:
            row.append(Paragraph("", styles["TableCell"]))
    widths = [doc_width / ncols] * ncols
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("LEADING", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfdff")]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def render(md_path: Path, out_path: Path) -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            spaceAfter=14,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=9,
            spaceAfter=5,
            textColor=colors.HexColor("#1f2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.0,
            spaceAfter=5,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.0,
            spaceAfter=3,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=8.5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=8,
        )
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.6 * inch,
    )
    story = []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    paragraph_buf: list[str] = []

    def flush_para() -> None:
        nonlocal paragraph_buf
        if paragraph_buf:
            story.append(Paragraph(inline(" ".join(paragraph_buf).strip()), styles["Body"]))
            paragraph_buf = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_para()
            i += 1
            continue
        if stripped == "\\pagebreak":
            flush_para()
            story.append(PageBreak())
            i += 1
            continue
        if is_table_line(stripped):
            flush_para()
            table_lines = []
            while i < len(lines) and is_table_line(lines[i].strip()):
                table_lines.append(lines[i])
                i += 1
            story.append(parse_table(table_lines, styles, doc.width))
            story.append(Spacer(1, 0.08 * inch))
            continue
        img_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if img_match:
            flush_para()
            caption, path = img_match.group(1), Path(img_match.group(2))
            if not path.is_absolute():
                path = (md_path.parent / path).resolve()
            try:
                img = Image(str(path))
                max_w = doc.width
                max_h = 2.7 * inch
                scale = min(max_w / img.imageWidth, max_h / img.imageHeight, 1.0)
                img.drawWidth = img.imageWidth * scale
                img.drawHeight = img.imageHeight * scale
                block = [img]
                if caption:
                    block.append(Paragraph(inline(caption), styles["Caption"]))
                story.append(KeepTogether(block))
            except Exception as exc:  # noqa: BLE001
                story.append(Paragraph(inline(f"[Image unavailable: {path} ({exc})]"), styles["Small"]))
            i += 1
            continue
        if stripped.startswith("# "):
            flush_para()
            story.append(Paragraph(inline(stripped[2:]), styles["TitleCenter"] if not story else styles["H1"]))
            i += 1
            continue
        if stripped.startswith("## "):
            flush_para()
            story.append(Paragraph(inline(stripped[3:]), styles["H2"]))
            i += 1
            continue
        if stripped.startswith("- "):
            flush_para()
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(ListItem(Paragraph(inline(lines[i].strip()[2:]), styles["Body"]), leftIndent=10))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=14, bulletFontSize=5))
            story.append(Spacer(1, 0.04 * inch))
            continue
        paragraph_buf.append(stripped)
        i += 1
    flush_para()
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    render(args.input, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
