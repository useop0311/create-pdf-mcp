// Korean CSAT / Mock-Exam Common Typst Macros

#let KOREAN_SANS_FONTS = (
  "IBM Plex Sans KR",
  "Pretendard",
  "Apple SD Gothic Neo",
  "Noto Sans CJK KR",
  "Noto Sans KR",
  "NanumGothic",
  "Malgun Gothic",
  "New Computer Modern",
)

#let KOREAN_SERIF_FONTS = (
  "AppleMyungjo",
  "Noto Serif CJK KR",
  "Noto Serif KR",
  "NanumMyeongjo",
  "Batang",
  "IBM Plex Sans KR",
  "Apple SD Gothic Neo",
  "Noto Sans CJK KR",
  "New Computer Modern",
)

#let KOREAN_FONTS = KOREAN_SERIF_FONTS

#let get_korean_fonts(style) = {
  if style == "sans" {
    KOREAN_SANS_FONTS
  } else {
    KOREAN_SERIF_FONTS
  }
}

#let to_markup(val) = {
  if val == none {
    none
  } else if type(val) == str {
    eval(val, mode: "markup")
  } else {
    val
  }
}

#let points_badge(pts) = {
  if pts != none and pts > 0 [
    #h(0.4em)#text(size: 9.5pt, weight: "bold", fill: rgb("#333"))[\[#pts\점\]]
  ]
}

#let topic_badge(tag) = {
  if tag != none and tag != "" [
    #box(
      stroke: 0.5pt + rgb("#aaa"),
      radius: 2pt,
      inset: (x: 4pt, y: 2pt),
      baseline: 0pt,
      outset: 0pt,
      fill: rgb("#f8f9fa")
    )[#text(size: 7.5pt, fill: rgb("#555"))[#tag]]
    #h(0.3em)
  ]
}

#let conditions_box(items) = {
  if items != none and items.len() > 0 {
    v(0.3em)
    align(center)[
      #block(
        width: 96%,
        stroke: 0.6pt + rgb("#444"),
        radius: 0pt,
        inset: (x: 10pt, y: 7pt),
        align(left)[
          #set par(leading: 0.65em, spacing: 0.45em, justify: true)
          #for (idx, item) in items.enumerate() [
            #if idx > 0 [ #v(0.2em) ]
            #to_markup(item)
          ]
        ]
      )
    ]
    v(0.3em)
  }
}

#let given_box_render(g_data) = {
  if g_data != none {
    v(0.35em)
    let g_title = g_data.at("title", default: none)
    if g_title != none and g_title != "" {
      align(center)[
        #block(
          width: 98%,
          stroke: 0.6pt + rgb("#333"),
          radius: 0pt,
          fill: rgb("#fafbfc"),
          inset: (x: 9pt, top: 11pt, bottom: 8pt),
          outset: 0pt,
          [
            #place(top + center, dy: -16pt)[
              #box(fill: white, inset: (x: 6pt, y: 0pt))[
                #text(size: 8.8pt, weight: "bold", font: KOREAN_FONTS)[#to_markup(g_title)]
              ]
            ]
            #align(left)[
              #set par(leading: 0.65em, spacing: 0.5em, justify: true)
              #set text(size: 9.4pt)
              #to_markup(g_data.content)
            ]
          ]
        )
      ]
    } else {
      align(center)[
        #block(
          width: 98%,
          stroke: 0.6pt + rgb("#333"),
          radius: 0pt,
          fill: rgb("#fafbfc"),
          inset: (x: 9pt, y: 7.5pt),
          align(left)[
            #set par(leading: 0.65em, spacing: 0.5em, justify: true)
            #set text(size: 9.4pt)
            #to_markup(g_data.content)
          ]
        )
      ]
    }
    v(0.3em)
  }
}

#let passage_box(p_data, breakable_box: true) = {
  if p_data != none and p_data != "" {
    let p_dict = if type(p_data) == str { (content: p_data) } else { p_data }
    let header = p_dict.at("header", default: none)
    if header != none and header != "" {
      block(sticky: true, width: 100%, above: 0.6em, below: 0.35em)[
        #text(size: 9.8pt, weight: "bold", fill: rgb("#111"), font: KOREAN_FONTS)[#to_markup(header)]
      ]
    } else {
      v(0.3em)
    }

    block(
      width: 100%,
      breakable: breakable_box,
      stroke: 0.65pt + rgb("#222"),
      radius: 0pt,
      inset: (x: 9pt, y: 8pt),
      fill: white,
      [
        #let p_title = p_dict.at("title", default: none)
        #if p_title != none and p_title != "" [
          #align(center)[
            #block(below: 0.5em)[
              #text(size: 9.8pt, weight: "bold", font: KOREAN_FONTS)[#to_markup(p_title)]
            ]
          ]
        ]
        #align(left)[
          #set par(leading: 0.68em, spacing: 0.55em, justify: true)
          #set text(size: 9.4pt)
          #to_markup(p_dict.content)
        ]
        #let p_source = p_dict.at("source", default: none)
        #if p_source != none and p_source != "" [
          #v(0.35em)
          #align(right)[
            #text(size: 8.5pt, fill: rgb("#333"), font: KOREAN_FONTS)[— #to_markup(p_source)]
          ]
        ]
        #let p_notes = p_dict.at("footnotes", default: ())
        #if p_notes != none and p_notes.len() > 0 [
          #v(0.35em)
          #align(right)[
            #set par(leading: 0.45em, spacing: 0.25em)
            #for (f_idx, fn) in p_notes.enumerate() [
              #if f_idx > 0 [ \ ]
              #text(size: 8pt, fill: rgb("#444"), font: KOREAN_FONTS)[#to_markup(fn)]
            ]
          ]
        ]
      ]
    )
    v(0.45em)
  }
}

#let group_header_box(header) = {
  if header != none and header != "" {
    v(0.25em)
    block(
      width: 100%,
      stroke: (
        left: 2.5pt + rgb("#222"),
        top: 0.5pt + rgb("#aaa"),
        bottom: 0.5pt + rgb("#aaa"),
        right: 0.5pt + rgb("#aaa"),
      ),
      fill: rgb("#f8f9fa"),
      inset: (x: 8pt, y: 6pt),
      radius: 1pt,
      breakable: false,
      [
        #text(size: 9.8pt, weight: "bold", fill: rgb("#111"), font: KOREAN_FONTS)[#to_markup(header)]
      ]
    )
    v(0.3em)
  }
}

#let bogi_box(items, title: none) = {
  if items != none and items.len() > 0 {
    let b_title = if title != none and title != "" { title } else { "\\<보 기\\>" }
    v(0.4em)
    align(center)[
      #block(
        width: 96%,
        stroke: 0.6pt + rgb("#222"),
        radius: 0pt,
        inset: (x: 10pt, top: 12pt, bottom: 8pt),
        outset: 0pt,
        [
          #place(top + center, dy: -17pt)[
            #box(fill: white, inset: (x: 6pt, y: 0pt))[
              #text(size: 9pt, weight: "bold", font: KOREAN_FONTS)[#to_markup(b_title)]
            ]
          ]
          #align(left)[
            #set par(leading: 0.65em, spacing: 0.45em, justify: true)
            #for (idx, item) in items.enumerate() [
              #if idx > 0 [ #v(0.2em) ]
              #to_markup(item)
            ]
          ]
        ]
      )
    ]
    v(0.4em)
  }
}

#let choices_grid(choices) = {
  if choices != none and choices.len() > 0 {
    v(0.35em)
    let circled = ("①", "②", "③", "④", "⑤")
    
    // Measure visible character length (clusters) to decide 5-col, 3+2 col, or 1-col
    let max_len = 0
    for c in choices {
      let cleaned = c.replace("#underline[", "").replace("]", "")
      let clen = cleaned.clusters().len()
      if clen > max_len { max_len = clen }
    }

    if choices.len() == 5 and max_len <= 8 {
      // 1 row of 5 columns
      grid(
        columns: (1fr, 1fr, 1fr, 1fr, 1fr),
        gutter: 4pt,
        ..choices.enumerate().map(((i, c)) => [
          #text(weight: "bold")[#circled.at(i)] #to_markup(c)
        ])
      )
    } else if choices.len() == 5 and max_len <= 16 {
      // 2 rows: 3 columns then 2 columns
      grid(
        columns: (1fr, 1fr, 1fr),
        row-gutter: 0.55em,
        column-gutter: 4pt,
        ..choices.slice(0, 3).enumerate().map(((i, c)) => [
          #text(weight: "bold")[#circled.at(i)] #to_markup(c)
        ]),
        ..choices.slice(3, 5).enumerate().map(((i, c)) => [
          #text(weight: "bold")[#circled.at(i + 3)] #to_markup(c)
        ]),
        []
      )
    } else {
      // 1 column list with hanging alignment via 2-column grid (number, text)
      grid(
        columns: (auto, 1fr),
        column-gutter: 0.4em,
        row-gutter: 0.48em,
        align: (left + top, left + top),
        ..choices.enumerate().map(((i, c)) => (
          [#text(weight: "bold")[#circled.at(calc.min(i, 4))]],
          [#set par(leading: 0.6em, justify: true); #to_markup(c)]
        )).flatten()
      )
    }
    v(0.25em)
  }
}

#let short_answer_box(label: "정답", width: 4.5cm, height: 1.1cm) = {
  v(0.4em)
  align(right)[
    #box(
      stroke: 0.8pt + rgb("#333"),
      inset: (x: 8pt, y: 4pt),
      radius: 2pt,
      width: width,
      height: height,
    )[
      #align(left + horizon)[
        #text(size: 9.5pt, font: KOREAN_FONTS)[#label:\ ]
      ]
    ]
  ]
  v(0.3em)
}

#let descriptive_answer_box(label: "풀이 과정 및 정답", height: 4.5cm) = {
  v(0.5em)
  block(
    width: 100%,
    height: height,
    stroke: 0.8pt + rgb("#444"),
    radius: 3pt,
    fill: rgb("#fafbfc"),
    inset: (x: 10pt, top: 7pt, bottom: 7pt),
    [
      #align(left + top)[
        #text(size: 8.5pt, weight: "bold", fill: rgb("#555"), font: KOREAN_FONTS)[\[#label\]]
      ]
    ]
  )
  v(0.4em)
}

#let render_answer_area(prob) = {
  if prob.at("choices", default: ()).len() > 0 {
    choices_grid(prob.choices)
  } else {
    let s_type = prob.at("subjective_type", default: "short_answer")
    if s_type != "none" {
      let s_h = eval(prob.at("subjective_box_height", default: "1.1cm"))
      let s_lbl = prob.at("subjective_label", default: "정답")
      if s_type == "descriptive" {
        descriptive_answer_box(label: s_lbl, height: s_h)
      } else {
        short_answer_box(label: s_lbl, height: s_h)
      }
    }
  }
}

#let format_prob_num(num) = {
  let s = str(num)
  if s.starts-with("[") or s.ends-with(".") or s.ends-with(")") or s.ends-with("]") {
    s
  } else {
    s + "."
  }
}

#let format_sol_heading(num) = {
  let s = str(num)
  if s.ends-with("번") or s.ends-with("]") {
    [#s 문항 해설]
  } else {
    [#s 번 문항 해설]
  }
}

#let render_sub_problem(sub) = {
  block(
    width: 100%,
    breakable: false,
    inset: (left: 0.6em, top: 0.35em, bottom: eval(sub.at("solving_space", default: "0.4cm")))
  )[
    #text(size: 9.8pt, weight: "bold")[#sub.label]
    #topic_badge(sub.at("topic_tag", default: none))
    #h(0.25em)#to_markup(sub.stem)
    #points_badge(sub.at("points", default: none))

    #given_box_render(sub.at("given_box", default: none))

    #if sub.at("inline_passage", default: none) != none [
      #passage_box(sub.inline_passage, breakable_box: true)
    ]
    #if sub.at("passage", default: none) != none and sub.at("inline_passage", default: none) == none [
      #passage_box(sub.passage, breakable_box: true)
    ]

    #conditions_box(sub.at("conditions", default: ()))

    #for fig in sub.at("figures_svg", default: ()) [
      #v(0.3em)
      #align(center)[#image(bytes(fig), format: "svg")]
      #v(0.3em)
    ]

    #bogi_box(sub.at("bogi", default: ()), title: sub.at("bogi_title", default: none))

    #render_answer_area(sub)
  ]
}

#let render_problem_item(prob, num_size: 11.5pt, default_solving_space: "1.2cm") = {
  let is_hdr_only = prob.at("is_header_only", default: false)
  let sol_space = eval(prob.at("solving_space", default: default_solving_space))
  let subs = prob.at("sub_problems", default: ())

  // 1. Pre-passage (세트 공통 지문, 국어/영어 [1~3] 등)
  if prob.at("pre_passage", default: none) != none {
    passage_box(prob.pre_passage, breakable_box: true)
  }

  // 2. Standalone Group Header Box ([4~8번] 빈칸에 들어갈 알맞은 문장을 고르시오 등)
  if prob.at("group_header", default: none) != none {
    group_header_box(prob.group_header)
  }
  if prob.at("group_passage", default: none) != none {
    passage_box(prob.group_passage, breakable_box: true)
  }
  if prob.at("group_conditions", default: ()).len() > 0 {
    conditions_box(prob.group_conditions)
  }
  for gfig in prob.at("group_figures_svg", default: ()) [
    #v(0.3em)
    #align(center)[#image(bytes(gfig), format: "svg")]
    #v(0.3em)
  ]
  if prob.at("group_bogi", default: ()).len() > 0 {
    bogi_box(prob.group_bogi)
  }

  if is_hdr_only {
    return
  }

  if subs.len() == 0 {
    block(
      width: 100%,
      breakable: prob.at("is_breakable", default: false),
      inset: (bottom: sol_space)
    )[
      // Question number + badges
      #text(size: num_size, weight: "bold")[#format_prob_num(prob.number)]
      #topic_badge(prob.at("topic_tag", default: none))
      #h(0.3em)#to_markup(prob.stem)
      #points_badge(prob.at("points", default: none))

      // Optional Given Box (주어진 글 / 문장 삽입 / 제시문)
      #given_box_render(prob.at("given_box", default: none))

      // Optional Inline Passage (단독 문항 지문, e.g. 영어 독해 18~40번)
      #if prob.at("inline_passage", default: none) != none [
        #passage_box(prob.inline_passage, breakable_box: prob.at("is_breakable", default: false))
      ]

      // Optional Passage (단독/추가 지문)
      #if prob.at("passage", default: none) != none and prob.at("inline_passage", default: none) == none [
        #passage_box(prob.passage, breakable_box: prob.at("is_breakable", default: false))
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
  } else {
    // Multi-part problem (새끼문제들)
    block(width: 100%, breakable: false)[
      #text(size: num_size, weight: "bold")[#format_prob_num(prob.number)]
      #topic_badge(prob.at("topic_tag", default: none))
      #h(0.3em)#to_markup(prob.stem)
      #points_badge(prob.at("points", default: none))

      #given_box_render(prob.at("given_box", default: none))

      #if prob.at("inline_passage", default: none) != none [
        #passage_box(prob.inline_passage, breakable_box: true)
      ]
      #if prob.at("passage", default: none) != none and prob.at("inline_passage", default: none) == none [
        #passage_box(prob.passage, breakable_box: true)
      ]

      #conditions_box(prob.at("conditions", default: ()))

      #for fig in prob.at("figures_svg", default: ()) [
        #v(0.3em)
        #align(center)[#image(bytes(fig), format: "svg")]
        #v(0.3em)
      ]

      #bogi_box(prob.at("bogi", default: ()), title: prob.at("bogi_title", default: none))

      #render_sub_problem(subs.at(0))
    ]
    for sub in subs.slice(1) [
      #render_sub_problem(sub)
    ]
    if prob.at("choices", default: ()).len() > 0 [
      #choices_grid(prob.choices)
    ]
    v(sol_space)
  }
}
