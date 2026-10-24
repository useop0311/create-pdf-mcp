// Solutions and Quick Answer Sheet Template

#import "base.typ": *

#let render_solutions(
  title: "정답 및 해설",
  footer_text: none,
  footer_note: none,
  problems: ()
) = {
  set text(
    font: KOREAN_FONTS,
    size: 9.5pt,
    lang: "ko"
  )
  set par(leading: 0.65em)

  set page(
    paper: "a4",
    margin: (x: 16mm, top: 16mm, bottom: 16mm),
    footer: context {
      line(length: 100%, stroke: 0.4pt + rgb("#cbd5e1"))
      v(2pt)
      grid(
        columns: (1fr, auto, 1fr),
        align: (left + horizon, center + horizon, right + horizon),
        [
          #if footer_text != none [
            #text(size: 8pt, fill: rgb("#666"), font: KOREAN_FONTS)[#footer_text]
          ]
        ],
        [
          #text(size: 8.5pt, fill: rgb("#444"), font: KOREAN_FONTS)[- #counter(page).get().first() -]
        ],
        [
          #if footer_note != none [
            #text(size: 7.5pt, fill: rgb("#777"), font: KOREAN_FONTS)[#footer_note]
          ]
        ]
      )
    }
  )

  // Section 1: Quick Answer Key Table
  align(center)[
    #text(size: 14pt, weight: "bold", font: KOREAN_FONTS)[#title]
    #v(0.3em)
    #text(size: 11pt, weight: "bold", fill: rgb("#333"), font: KOREAN_FONTS)[\<빠른 정답표\>]
  ]
  v(0.5em)

  // Render Answer Table in chunks of up to 10 per row
  let graded_problems = problems.filter(p => not p.at("is_header_only", default: false))
  let chunk_size = 10
  let total = graded_problems.len()
  let num_chunks = if total > 0 { calc.ceil(total / chunk_size) } else { 0 }

  for c_idx in range(num_chunks) {
    let start_idx = c_idx * chunk_size
    let end_idx = calc.min(start_idx + chunk_size, total)
    let chunk = graded_problems.slice(start_idx, end_idx)

    align(center)[
      #table(
        columns: (auto, ..chunk.map(_ => 1fr)),
        align: center + horizon,
        fill: (col, row) => if row == 0 { rgb("#f1f5f9") } else { none },
        stroke: 0.5pt + rgb("#cbd5e1"),
        [#text(weight: "bold")[문항]], ..chunk.map(p => [#p.number]),
        [#text(weight: "bold")[정답]], ..chunk.map(p => [#text(weight: "bold", fill: rgb("#b91c1c"))[#to_markup(p.at("quick_answer", default: p.answer))]])
      )
    ]
    v(0.3em)
  }

  v(1.5em)
  line(length: 100%, stroke: 0.8pt + rgb("#94a3b8"))
  v(1em)

  // Section 2: Detailed Solutions
  align(left)[
    #text(size: 12pt, weight: "bold", font: KOREAN_FONTS)[상세 해설]
  ]
  v(0.5em)

  for prob in graded_problems [
    #block(
      width: 100%,
      stroke: (left: 2pt + rgb("#3b82f6")),
      inset: (left: 8pt, y: 6pt, bottom: 12pt)
    )[
      #grid(
        columns: (1fr, auto),
        align: (left + horizon, right + horizon),
        [
          #text(size: 11pt, weight: "bold", font: KOREAN_FONTS)[#format_sol_heading(prob.number)]
          #if prob.at("answer", default: "") != "" [
            #h(0.5em)#text(weight: "bold", fill: rgb("#b91c1c"))[[정답: #to_markup(prob.answer)]]
          ]
        ],
        []
      )
      #v(0.4em)

      #let has_parent_sol = prob.at("solution", default: none) != none and prob.at("solution", default: "") != ""
      #let sub_probs = prob.at("sub_problems", default: ())
      #let has_sub_sol = sub_probs.any(s => (s.at("solution", default: none) != none and s.at("solution", default: "") != "") or (s.at("answer", default: none) != none and s.at("answer", default: "") != ""))

      #if has_parent_sol [
        #to_markup(prob.solution)
      ]

      #for sfig in prob.at("solution_figures_svg", default: ()) [
        #v(0.4em)
        #align(center)[#image(bytes(sfig), format: "svg")]
        #v(0.3em)
      ]

      #if sub_probs.len() > 0 [
        #if has_parent_sol [ #v(0.4em) ]
        #for sub in sub_probs [
          #block(
            width: 100%,
            inset: (left: 6pt, y: 3pt),
            [
              #text(weight: "bold")[#sub.label]
              #if sub.at("answer", default: none) != none and sub.at("answer", default: "") != "" [
                #h(0.3em)#text(weight: "bold", fill: rgb("#b91c1c"))[[정답: #to_markup(sub.answer)]]
              ]
              #if sub.at("solution", default: none) != none and sub.at("solution", default: "") != "" [
                #h(0.3em)#to_markup(sub.solution)
              ]
              #for sfig in sub.at("solution_figures_svg", default: ()) [
                #v(0.3em)
                #align(center)[#image(bytes(sfig), format: "svg")]
                #v(0.2em)
              ]
            ]
          )
        ]
      ]

      #if not has_parent_sol and not has_sub_sol [
        #text(fill: rgb("#888"))[(상세 해설이 제공되지 않았습니다.)]
      ]
    ]
    #v(0.6em)
  ]
}
