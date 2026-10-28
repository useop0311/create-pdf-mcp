// 1-Column Workbook / Worksheet Template

#import "base.typ": *

#let render_workbook(
  title: "수학 영역",
  subtitle: "개념 및 유형 연습",
  subject_badge: none,
  footer_text: none,
  footer_note: none,
  font_style: "serif",
  problems: ()
) = {
  let fonts = get_korean_fonts(font_style)
  set text(
    font: fonts,
    size: 10pt,
    lang: "ko"
  )
  set par(leading: 0.65em, justify: true)

  set page(
    paper: "a4",
    margin: (x: 18mm, top: 16mm, bottom: 16mm),
    header: context {
      grid(
        columns: (1fr, auto, 1fr),
        align: (left, center, right),
        [#text(size: 8.5pt, fill: rgb("#666"), font: KOREAN_FONTS)[#title]],
        [#text(size: 9pt, weight: "bold", font: KOREAN_FONTS)[#subtitle]],
        [#text(size: 8.5pt, fill: rgb("#666"), font: KOREAN_FONTS)[#subject_badge]]
      )
    },
    footer: context {
      line(length: 100%, stroke: 0.4pt + rgb("#888"))
      v(2pt)
      grid(
        columns: (1fr, auto, 1fr),
        align: (left + horizon, center + horizon, right + horizon),
        [
          #if footer_text != none [
            #text(size: 8pt, fill: rgb("#555"), font: KOREAN_FONTS)[#footer_text]
          ]
        ],
        [
          #text(size: 8.5pt, fill: rgb("#666"), font: KOREAN_FONTS)[- #counter(page).get().first() -]
        ],
        [
          #if footer_note != none [
            #text(size: 7.5pt, fill: rgb("#777"), font: KOREAN_FONTS)[#footer_note]
          ]
        ]
      )
    }
  )

  // Header Title
  align(center)[
    #text(size: 15pt, weight: "bold", font: KOREAN_FONTS)[#title]
    #if subtitle != none [
      \ #v(2pt)#text(size: 10pt, fill: rgb("#555"), font: KOREAN_FONTS)[#subtitle]
    ]
  ]
  v(4pt)
  line(length: 100%, stroke: 1.2pt + rgb("#333"))
  v(1em)

  for prob in problems [
    #render_problem_item(prob, num_size: 12pt, default_solving_space: "2.0cm")
  ]
}
