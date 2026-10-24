// Tablet/iPad 1-Problem-Per-Page Template

#import "base.typ": *

#let render_pad_1p1q(
  title: "수학 영역",
  subtitle: "패드 연습장",
  subject_badge: none,
  footer_text: none,
  footer_note: none,
  pad_note_style: none,
  problems: ()
) = {
  set text(
    font: KOREAN_FONTS,
    size: 10.5pt,
    lang: "ko"
  )
  set par(leading: 0.7em)

  set page(
    paper: "a4",
    margin: (x: 16mm, top: 14mm, bottom: 14mm),
    header: context {
      grid(
        columns: (1fr, auto, 1fr),
        align: (left, center, right),
        [#text(size: 8.5pt, fill: rgb("#666"), font: KOREAN_FONTS)[#title]],
        [#text(size: 8.5pt, weight: "bold", fill: rgb("#444"), font: KOREAN_FONTS)[#subtitle]],
        [#text(size: 8.5pt, fill: rgb("#666"), font: KOREAN_FONTS)[#subject_badge]]
      )
    },
    footer: context {
      line(length: 100%, stroke: 0.4pt + rgb("#d1d5db"))
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

  for (i, prob) in problems.enumerate() [
    #if i > 0 [ #pagebreak() ]

    // Top Question Meta
    #grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      [
        #text(size: 14pt, weight: "bold", font: KOREAN_FONTS)[문항 #prob.number]
        #h(0.4em)#topic_badge(prob.at("topic_tag", default: none))
        #points_badge(prob.at("points", default: none))
      ],
      []
    )
    #v(3pt)
    #line(length: 100%, stroke: 0.8pt + rgb("#cbd5e1"))
    #v(0.5em)

    // Question content area (Rest of the page is naturally open for handwriting/solving)
    #block(width: 100%)[
      #if prob.at("pad_pre_passage", default: none) != none [
        #passage_box(prob.pad_pre_passage, breakable_box: true)
      ]

      #to_markup(prob.stem)

      #given_box_render(prob.at("given_box", default: none))

      #if prob.at("inline_passage", default: none) != none [
        #passage_box(prob.inline_passage, breakable_box: true)
      ]

      #conditions_box(prob.at("conditions", default: ()))

      #for fig in prob.at("figures_svg", default: ()) [
        #v(0.4em)
        #align(center)[#image(bytes(fig), format: "svg")]
        #v(0.4em)
      ]

      #bogi_box(prob.at("bogi", default: ()), title: prob.at("bogi_title", default: none))

      // Choices or Subjective answer box
      #render_answer_area(prob)
    ]
  ]
}
