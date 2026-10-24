// Korean CSAT 2-Column Exam Template

#import "base.typ": *

#let exam_header(title, subtitle, badge) = {
  block(width: 100%, inset: (bottom: 8pt))[
    #grid(
      columns: (1fr, auto, 1fr),
      align: (left + horizon, center + horizon, right + horizon),
      [
        #if subtitle != none [
          #text(size: 11pt, weight: "bold", fill: rgb("#333"), font: KOREAN_FONTS)[#subtitle]
        ]
      ],
      [
        #text(size: 16pt, weight: "bold", font: KOREAN_FONTS)[#title]
      ],
      [
        #if badge != none [
          #box(
            stroke: 1.2pt + rgb("#111"),
            inset: (x: 8pt, y: 3pt),
            radius: 3pt
          )[
            #text(size: 10pt, weight: "bold", font: KOREAN_FONTS)[#badge]
          ]
        ]
      ]
    )
    #v(3pt)
    #line(length: 100%, stroke: 1.5pt + rgb("#111"))
    #v(1pt)
    #line(length: 100%, stroke: 0.5pt + rgb("#111"))
  ]
}

#let render_exam_2col(
  title: "수학 영역",
  subtitle: "제 2 교시",
  subject_badge: none,
  footer_text: none,
  footer_note: none,
  problems: ()
) = {
  set text(
    font: KOREAN_FONTS,
    size: 9.8pt,
    lang: "ko"
  )
  set par(leading: 0.65em, justify: true)

  set page(
    paper: "a4",
    margin: (x: 13mm, top: 14mm, bottom: 14mm),
    header: context {
      if counter(page).get().first() == 1 {
        // Page 1 header handled in body
        none
      } else {
        grid(
          columns: (1fr, auto, 1fr),
          align: (left, center, right),
          [#text(size: 8.5pt, fill: rgb("#666"), font: KOREAN_FONTS)[#title]],
          [],
          [#text(size: 8.5pt, fill: rgb("#666"), font: KOREAN_FONTS)[#subject_badge]]
        )
      }
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
          #text(size: 9pt, font: KOREAN_FONTS)[- #counter(page).get().first() -]
        ],
        [
          #if footer_note != none [
            #text(size: 7.5pt, fill: rgb("#777"), font: KOREAN_FONTS)[#footer_note]
          ]
        ]
      )
    }
  )

  // First page header
  exam_header(title, subtitle, subject_badge)
  v(0.5em)

  // 2-Column body with center vertical divider
  columns(2, gutter: 18pt)[
    #for prob in problems [
      #render_problem_item(prob, num_size: 11.5pt, default_solving_space: "1.2cm")
    ]
  ]
}
