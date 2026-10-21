// Korean CSAT / Mock-Exam Common Typst Macros

#let KOREAN_FONTS = (
  "AppleMyungjo",
  "Noto Serif CJK KR",
  "Noto Serif KR",
  "NanumMyeongjo",
  "Batang",
  "Apple SD Gothic Neo",
  "Noto Sans CJK KR",
  "Noto Sans KR",
  "NanumGothic",
  "Malgun Gothic",
  "Pretendard",
  "New Computer Modern",
  "DejaVu Serif",
)

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
        width: 95%,
        stroke: 0.6pt + rgb("#444"),
        radius: 0pt,
        inset: (x: 10pt, y: 7pt),
        align(left)[
          #set par(leading: 0.6em)
          #for item in items [
            #to_markup(item) \
          ]
        ]
      )
    ]
    v(0.3em)
  }
}

#let bogi_box(items) = {
  if items != none and items.len() > 0 {
    v(0.4em)
    align(center)[
      #block(
        width: 95%,
        stroke: 0.6pt + rgb("#222"),
        radius: 0pt,
        inset: (x: 10pt, top: 12pt, bottom: 8pt),
        outset: 0pt,
        [
          #place(top + center, dy: -17pt)[
            #box(fill: white, inset: (x: 6pt, y: 0pt))[
              #text(size: 9pt, weight: "bold")[\<보 기\>]
            ]
          ]
          #align(left)[
            #set par(leading: 0.6em)
            #for item in items [
              #to_markup(item) \
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
    v(0.4em)
    let circled = ("①", "②", "③", "④", "⑤")
    
    // Measure lengths to decide 5-col, 3+2 col, or 1-col
    let max_len = 0
    for c in choices {
      if c.len() > max_len { max_len = c.len() }
    }

    if choices.len() == 5 and max_len <= 10 {
      // 1 row of 5 columns
      grid(
        columns: (1fr, 1fr, 1fr, 1fr, 1fr),
        gutter: 4pt,
        ..choices.enumerate().map(((i, c)) => [
          #text(weight: "bold")[#circled.at(i)] #to_markup(c)
        ])
      )
    } else if choices.len() == 5 and max_len <= 22 {
      // 2 rows: 3 columns then 2 columns
      grid(
        columns: (1fr, 1fr, 1fr),
        row-gutter: 0.6em,
        ..choices.slice(0, 3).enumerate().map(((i, c)) => [
          #text(weight: "bold")[#circled.at(i)] #to_markup(c)
        ]),
        ..choices.slice(3, 5).enumerate().map(((i, c)) => [
          #text(weight: "bold")[#circled.at(i + 3)] #to_markup(c)
        ]),
        []
      )
    } else {
      // 1 column list
      stack(
        spacing: 0.5em,
        ..choices.enumerate().map(((i, c)) => [
          #text(weight: "bold")[#circled.at(i)] #to_markup(c)
        ])
      )
    }
    v(0.3em)
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
    let s_h = eval(prob.at("subjective_box_height", default: "1.1cm"))
    let s_lbl = prob.at("subjective_label", default: "정답")
    if s_type == "descriptive" {
      descriptive_answer_box(label: s_lbl, height: s_h)
    } else {
      short_answer_box(label: s_lbl, height: s_h)
    }
  }
}
