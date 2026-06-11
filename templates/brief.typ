#set document(title: "$if(title)$$title$$else$DeepBrief$endif$")
#set page(
  paper: "us-letter",
  margin: (x: 0.72in, y: 0.74in),
  numbering: "1",
)
#set text(size: 9.7pt)
#set par(justify: true, leading: 0.52em)
#set heading(numbering: "1.1")

#show raw.where(block: true): it => block(
  fill: luma(248),
  stroke: luma(210),
  inset: 6pt,
  radius: 2pt,
  width: 100%,
)[#text(size: 7.2pt)[#it]]

#outline(title: "Contents")
#pagebreak()

$body$
