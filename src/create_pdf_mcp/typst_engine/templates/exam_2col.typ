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

  // 2-Column body
  columns(2, gutter: 18pt)[
    #for prob in problems [
      // Shared / pre-stem passage (breakable across columns for long Korean/English reading passages)
      #if prob.at("pre_passage", default: none) != none [
        #passage_box(prob.pre_passage, breakable_box: true)
      ]

      #block(
        width: 100%,
        breakable: prob.at("is_breakable", default: false),
        inset: (bottom: eval(prob.at("solving_space", default: "1.2cm")))
      )[
        // Question number + badges
        #text(size: 11.5pt, weight: "bold")[#prob.number.]
        #topic_badge(prob.at("topic_tag", default: none))
        #h(0.3em)#to_markup(prob.stem)
        #points_badge(prob.at("points", default: none))

        // Optional Given Box (주어진 글 / 문장 삽입 / 제시문)
        #given_box_render(prob.at("given_box", default: none))

        // Optional Inline Passage (단독 문항 지문, e.g. 영어 독해 18~40번)
        #if prob.at("inline_passage", default: none) != none [
          #passage_box(prob.inline_passage, breakable_box: prob.at("is_breakable", default: false))
        ]

        // Optional Conditions Box
        #conditions_box(prob.at("conditions", default: ()))

        // Figures
        #for fig in prob.at("figures_svg", default: ()) [
          #v(0.3em)
          #align(center)[#image(bytes(fig), format: "svg")]
          #v(0.3em)
        ]

        // Bogi Box (<보 기>)
        #bogi_box(prob.at("bogi", default: ()), title: prob.at("bogi_title", default: none))

        // Choices or Subjective answer box
        #render_answer_area(prob)
      ]
    ]
  ]
}
