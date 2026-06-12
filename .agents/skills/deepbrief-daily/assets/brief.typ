#set document(title: "$if(title)$$title$$else$DeepBrief$endif$")
#let ink = rgb("#171717")
#let muted = rgb("#5b6460")
#let rule = rgb("#d8e0dd")
#let panel = rgb("#f6f8f6")
#let code-bg = rgb("#eef3f0")
#let accent = rgb("#1f6f63")
#let accent-dark = rgb("#17483f")

#set page(
  paper: "us-letter",
  margin: (x: 0.74in, y: 0.76in),
  numbering: "1",
)
#set text(size: 10pt, fill: ink)
#set par(justify: false, leading: 0.66em, spacing: 0.76em)
#set heading(numbering: "1.1")
#set table(inset: 5pt, stroke: rule)

#show heading.where(level: 1): set text(size: 16pt, fill: accent-dark, weight: "bold")
#show heading.where(level: 2): set text(size: 12.4pt, fill: accent-dark, weight: "bold")
#show heading.where(level: 3): set text(size: 10.8pt, fill: accent, weight: "bold")

#show link: it => text(fill: accent-dark)[#underline(it)]

#show raw.where(block: false): it => box(
  fill: code-bg,
  inset: (x: 2.2pt, y: 0.8pt),
  radius: 2pt,
)[#text(font: "New Computer Modern Mono", size: 8.7pt, fill: accent-dark)[#it]]

#show raw.where(block: true): it => block(
  fill: code-bg,
  stroke: rule,
  inset: 8pt,
  radius: 3pt,
  width: 100%,
)[#text(font: "New Computer Modern Mono", size: 7.4pt, fill: rgb("#1e2b27"))[#it]]

#show quote: it => block(
  fill: panel,
  stroke: accent,
  inset: 8pt,
  radius: 3pt,
  width: 100%,
)[#text(fill: muted)[#it]]

#outline(title: "Contents")
#pagebreak()

$body$
