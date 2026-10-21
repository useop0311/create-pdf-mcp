// 1-Column Workbook / Worksheet Template

#import "base.typ": *

#let render_workbook(
  title: "수학 영역",
  subtitle: "개념 및 유형 연습",
  subject_badge: none,
  footer_text: none,
  footer_note: none,
  problems: ()
) = {
  set text(
    font: KOREAN_FONTS,
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
    #block(
      width: 100%,
      breakable: false,
      inset: (bottom: eval(prob.at("solving_space", default: "2.0cm")))
    )[
      #text(size: 12pt, weight: "bold")[#prob.number.]
      #topic_badge(prob.at("topic_tag", default: none))
      #h(0.3em)#to_markup(prob.stem)
      #points_badge(prob.at("points", default: none))

      #conditions_box(prob.at("conditions", default: ()))

      #for fig in prob.at("figures_svg", default: ()) [
        #v(0.3em)
        #align(center)[#image(bytes(fig), format: "svg")]
        #v(0.3em)
      ]

      #bogi_box(prob.at("bogi", default: ()))

      // Choices or Subjective answer box
      #render_answer_area(prob)
    ]
  ]
}
