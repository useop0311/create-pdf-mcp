// Concept Book Base Macros and Theme Definitions
#import "base.typ": *

#let MATH_FONTS = (
  "New Computer Modern Math",
  "IBM Plex Sans KR",
  "Pretendard",
  "Apple SD Gothic Neo",
  "Noto Sans CJK KR",
  "Noto Sans KR",
  "AppleMyungjo",
  "Noto Serif CJK KR",
)

#let THEMES = (
  blue: (
    primary: rgb("#1d4ed8"),
    primary_dark: rgb("#1e40af"),
    accent: rgb("#eff6ff"),
    border: rgb("#93c5fd"),
    badge_bg: rgb("#dbeafe"),
    badge_fg: rgb("#1e40af"),
    highlight: rgb("#fef08a"),
    quote_bar: rgb("#3b82f6"),
  ),
  emerald: (
    primary: rgb("#047857"),
    primary_dark: rgb("#065f46"),
    accent: rgb("#ecfdf5"),
    border: rgb("#6ee7b7"),
    badge_bg: rgb("#d1fae5"),
    badge_fg: rgb("#065f46"),
    highlight: rgb("#fef08a"),
    quote_bar: rgb("#10b981"),
  ),
  amber: (
    primary: rgb("#b45309"),
    primary_dark: rgb("#92400e"),
    accent: rgb("#fffbeb"),
    border: rgb("#fcd34d"),
    badge_bg: rgb("#fef3c7"),
    badge_fg: rgb("#92400e"),
    highlight: rgb("#fde68a"),
    quote_bar: rgb("#f59e0b"),
  ),
  purple: (
    primary: rgb("#6d28d9"),
    primary_dark: rgb("#5b21b6"),
    accent: rgb("#f5f3ff"),
    border: rgb("#c4b5fd"),
    badge_bg: rgb("#ede9fe"),
    badge_fg: rgb("#5b21b6"),
    highlight: rgb("#fef08a"),
    quote_bar: rgb("#8b5cf6"),
  ),
  mono: (
    primary: rgb("#18181b"),
    primary_dark: rgb("#09090b"),
    accent: rgb("#f4f4f5"),
    border: rgb("#a1a1aa"),
    badge_bg: rgb("#e4e4e7"),
    badge_fg: rgb("#18181b"),
    highlight: rgb("#e4e4e7"),
    quote_bar: rgb("#71717a"),
  ),
)

#let get_theme(theme_name) = {
  if theme_name in THEMES {
    THEMES.at(theme_name)
  } else {
    THEMES.blue
  }
}

#let get_density_config(density) = {
  if density == "compact" {
    (
      body_size: 9.2pt,
      leading: 0.60em,
      par_spacing: 0.45em,
      margin_x: 15mm,
      margin_y: 12mm,
      section_gap: 0.8em,
      block_gap: 0.3em,
      callout_inset_y: 5.5pt,
      table_inset_y: 4.5pt,
      fig_scale: 82%,
    )
  } else if density == "cozy" {
    (
      body_size: 9.6pt,
      leading: 0.66em,
      par_spacing: 0.52em,
      margin_x: 16mm,
      margin_y: 13.5mm,
      section_gap: 1.0em,
      block_gap: 0.38em,
      callout_inset_y: 6.5pt,
      table_inset_y: 5.2pt,
      fig_scale: 90%,
    )
  } else {
    (
      body_size: 10pt,
      leading: 0.74em,
      par_spacing: 0.62em,
      margin_x: 18mm,
      margin_y: 15.5mm,
      section_gap: 1.3em,
      block_gap: 0.45em,
      callout_inset_y: 7.5pt,
      table_inset_y: 6pt,
      fig_scale: 100%,
    )
  }
}

#let concept_highlight(theme: "blue", body) = {
  let th = get_theme(theme)
  box(
    fill: th.highlight,
    inset: (x: 2.5pt, y: 0pt),
    outset: (y: 1.8pt),
    radius: 2pt,
  )[#body]
}

#let concept_subheading(level: 2, theme: "blue", body) = {
  let th = get_theme(theme)
  if level <= 1 {
    block(
      width: 100%,
      sticky: true,
      breakable: false,
      above: 0.85em,
      below: 0.4em,
      fill: th.accent,
      stroke: (left: 4pt + th.primary),
      inset: (x: 9pt, y: 5.5pt),
      radius: (right: 3pt),
      [#text(size: 12.2pt, weight: "bold", fill: th.primary_dark)[#body]]
    )
  } else if level == 2 {
    block(
      width: 100%,
      sticky: true,
      breakable: false,
      above: 0.75em,
      below: 0.35em,
      stroke: (left: 3.5pt + th.primary),
      inset: (left: 7pt, top: 2pt, bottom: 2pt),
      [#text(size: 10.8pt, weight: "bold", fill: th.primary_dark)[#body]]
    )
  } else if level == 3 {
    block(
      width: 100%,
      sticky: true,
      breakable: false,
      above: 0.6em,
      below: 0.28em,
      inset: (left: 1pt),
      [#text(size: 10pt, weight: "bold", fill: th.primary)[▸] #h(2pt)#text(size: 10pt, weight: "bold", fill: rgb("#1e293b"))[#body]]
    )
  } else {
    block(
      width: 100%,
      sticky: true,
      breakable: false,
      above: 0.45em,
      below: 0.22em,
      inset: (left: 3pt),
      [#text(size: 9.5pt, weight: "bold", fill: rgb("#334155"))[• #body]]
    )
  }
}

#let concept_quote(theme: "blue", body) = {
  let th = get_theme(theme)
  block(
    width: 100%,
    breakable: false,
    above: 0.4em,
    below: 0.4em,
    stroke: (left: 2.5pt + th.quote_bar),
    inset: (left: 8pt, y: 4pt),
    fill: rgb("#f8fafc"),
    [#text(size: 9.2pt, fill: rgb("#475569"))[#body]]
  )
}

#let concept_code_block(lang: "text", code: "", theme: "blue") = {
  block(
    width: 100%,
    breakable: false,
    above: 0.4em,
    below: 0.4em,
    fill: rgb("#f1f5f9"),
    stroke: 0.5pt + rgb("#cbd5e1"),
    inset: (x: 10pt, y: 7pt),
    radius: 3pt,
    [
      #if lang != "text" and lang != "" [
        #align(right)[#text(size: 7.5pt, fill: rgb("#64748b"), weight: "bold")[#lang]]
        #v(-0.4em)
      ]
      #raw(code, lang: lang, block: true)
    ]
  )
}

#let callout_box(kind: "concept", title: none, theme: "blue", body) = {
  let th = get_theme(theme)

  // Configure appearance based on kind with crisp geometric vector badges
  let box_bg = th.accent
  let box_border = th.border
  let bar_stroke = th.primary
  let badge_symbol = "◆"
  let title_fill = th.primary_dark

  if kind == "formula" {
    box_bg = white
    box_border = th.primary
    bar_stroke = th.primary_dark
    badge_symbol = "■"
    title_fill = th.primary_dark
  } else if kind == "warning" {
    box_bg = rgb("#fff7ed")
    box_border = rgb("#fdba74")
    bar_stroke = rgb("#ea580c")
    badge_symbol = "▲"
    title_fill = rgb("#c2410c")
  } else if kind == "tip" {
    box_bg = rgb("#f0fdf4")
    box_border = rgb("#86efac")
    bar_stroke = rgb("#16a34a")
    badge_symbol = "★"
    title_fill = rgb("#15803d")
  } else if kind == "passage" or kind == "grammar" {
    box_bg = rgb("#f8fafc")
    box_border = rgb("#cbd5e1")
    bar_stroke = th.primary
    badge_symbol = "▣"
    title_fill = th.primary_dark
  } else if kind == "summary" {
    box_bg = th.accent
    box_border = th.border
    bar_stroke = th.primary
    badge_symbol = "●"
    title_fill = th.primary_dark
  }

  block(
    width: 100%,
    breakable: false,
    above: 0.45em,
    below: 0.45em,
    stroke: (
      left: 3.5pt + bar_stroke,
      top: 0.6pt + box_border,
      right: 0.6pt + box_border,
      bottom: 0.6pt + box_border,
    ),
    fill: box_bg,
    inset: (x: 9pt, top: 6.5pt, bottom: 6.5pt),
    radius: 2pt,
    [
      #if title != none [
        #block(below: 0.4em, sticky: true)[
          #text(size: 9.4pt, weight: "bold", fill: bar_stroke)[#badge_symbol]
          #h(3pt)
          #text(size: 9.5pt, weight: "bold", fill: title_fill)[#title]
        ]
      ]
      #set par(leading: 0.66em, spacing: 0.45em, justify: true)
      #set text(size: 9.3pt)
      #body
    ]
  )
}

#let concept_table(columns: (), aligns: (), headers: (), rows: (), theme: "blue") = {
  let th = get_theme(theme)
  let col_count = headers.len()
  let col_def = if columns.len() > 0 { columns } else { (1fr,) * col_count }

  block(
    width: 100%,
    breakable: false,
    above: 0.45em,
    below: 0.45em,
    table(
      columns: col_def,
      align: (col, row) => {
        if row == 0 { center + horizon }
        else if aligns.len() > col {
          let a = aligns.at(col)
          let a_val = if type(a) == str { eval(a) } else { a }
          a_val + horizon
        }
        else { left + horizon }
      },
      stroke: 0.5pt + rgb("#cbd5e1"),
      fill: (col, row) => {
        if row == 0 { th.accent }
        else if calc.even(row) { rgb("#f8fafc") }
        else { white }
      },
      inset: (x: 6.5pt, y: 5.5pt),
      // Headers
      ..headers.map(h => text(size: 9pt, weight: "bold", fill: th.primary_dark)[#h]),
      // Rows
      ..rows.flatten().map(cell => text(size: 8.8pt)[#cell])
    )
  )
}

#let section_header_banner(
  badge: none,
  title: "",
  subtitle: none,
  objectives: (),
  theme: "blue",
) = {
  let th = get_theme(theme)
  block(
    width: 100%,
    sticky: true,
    breakable: false,
    above: 0.6em,
    below: 0.55em,
    inset: (bottom: 4pt),
  )[
    #if badge != none [
      #box(
        fill: th.badge_bg,
        inset: (x: 6.5pt, y: 2.5pt),
        radius: 2.5pt,
      )[#text(size: 8.2pt, weight: "bold", fill: th.badge_fg)[#badge]]
      #v(2pt)
    ]
    #text(size: 13.8pt, weight: "bold", fill: rgb("#0f172a"))[#title]
    #if subtitle != none and subtitle != "" [
      #v(1pt)
      #text(size: 9.2pt, fill: rgb("#475569"))[#subtitle]
    ]
    #if objectives != none and objectives.len() > 0 [
      #v(3pt)
      #block(
        width: 100%,
        fill: rgb("#f8fafc"),
        stroke: 0.5pt + rgb("#e2e8f0"),
        inset: (x: 8pt, y: 4.5pt),
        radius: 2pt,
        [
          #text(size: 8pt, weight: "bold", fill: th.primary)[학습 목표]
          #h(0.5em)
          #for obj in objectives [
            #text(size: 8pt, fill: rgb("#334155"))[☑ #obj #h(0.8em)]
          ]
        ]
      )
    ]
    #v(3pt)
    #line(length: 100%, stroke: 1.1pt + th.primary)
  ]
}

#let render_concept_example(
  ex,
  theme: "blue",
  solution_mode: "inline",
) = {
  let th = get_theme(theme)
  let lbl = ex.at("label", default: "개념 확인 예제")
  let pts = ex.at("points", default: none)
  let tag = ex.at("topic_tag", default: none)

  block(
    width: 100%,
    breakable: false,
    above: 0.5em,
    below: 0.45em,
    stroke: 0.8pt + th.border,
    fill: rgb("#fcfdfe"),
    radius: 3pt,
    inset: (x: 9pt, top: 7pt, bottom: 7pt),
    [
      #grid(
        columns: (auto, 1fr),
        align: (left + horizon, right + horizon),
        [
          #box(fill: th.primary, inset: (x: 6pt, y: 2pt), radius: 2pt)[
            #text(size: 8.3pt, weight: "bold", fill: white)[#lbl]
          ]
          #if tag != none [
            #h(0.4em)#text(size: 8pt, fill: rgb("#64748b"))[\[#tag\]]
          ]
          #if pts != none [
            #h(0.3em)#text(size: 8.3pt, weight: "bold", fill: th.primary)[\[#pts\점\]]
          ]
        ],
        []
      )
      #v(0.3em)
      #text(size: 9.4pt)[#to_markup(ex.stem)]

      #if ex.at("conditions", default: ()).len() > 0 [
        #conditions_box(ex.conditions)
      ]

      #for fig in ex.at("figures_svg", default: ()) [
        #v(0.25em)
        #align(center)[#image(bytes(fig), format: "svg")]
        #v(0.25em)
      ]

      #if ex.at("bogi", default: ()).len() > 0 [
        #bogi_box(ex.bogi)
      ]

      #if ex.at("choices", default: ()).len() > 0 [
        #choices_grid(ex.choices)
      ]

      #if solution_mode == "inline" and (ex.at("answer", default: none) != none or ex.at("solution", default: none) != none) [
        #v(0.35em)
        #block(
          width: 100%,
          fill: rgb("#f1f5f9"),
          stroke: 0.5pt + rgb("#cbd5e1"),
          radius: 2pt,
          inset: (x: 8pt, y: 5pt),
          [
            #if ex.at("answer", default: none) != none [
              #text(size: 8.6pt, weight: "bold", fill: th.primary_dark)[정답: #to_markup(ex.answer)]
              #if ex.at("solution", default: none) != none [ #h(0.8em) ]
            ]
            #if ex.at("solution", default: none) != none [
              #text(size: 8.5pt, fill: rgb("#334155"))[#to_markup(ex.solution)]
            ]
          ]
        )
      ]
    ]
  )
}

#let concept_doc_cover_header(
  title: "",
  subtitle: none,
  badge: none,
  theme: "blue",
  density: "normal",
) = {
  let th = get_theme(theme)
  let is_compact = (density == "compact" or density == "cozy")
  align(center)[
    #if badge != none [
      #box(
        stroke: 1.1pt + th.primary,
        fill: th.accent,
        inset: (x: 9pt, y: 3pt),
        radius: 3pt,
      )[#text(size: if is_compact { 9pt } else { 9.8pt }, weight: "bold", fill: th.primary_dark)[#badge]]
      #v(if is_compact { 3pt } else { 5pt })
    ]
    #text(size: if is_compact { 16.5pt } else { 18.5pt }, weight: "bold", fill: rgb("#0f172a"))[#title]
    #if subtitle != none and subtitle != "" [
      #v(2pt)
      #text(size: if is_compact { 9.8pt } else { 10.5pt }, fill: rgb("#475569"))[#subtitle]
    ]
  ]
  v(if is_compact { 4pt } else { 6pt })
  line(length: 100%, stroke: 1.4pt + th.primary)
  v(if is_compact { 0.5em } else { 0.8em })
}

#let to_concept_markup(val) = {
  if val == none {
    none
  } else if type(val) == str {
    eval(
      val,
      mode: "markup",
      scope: (
        concept_highlight: concept_highlight,
        concept_subheading: concept_subheading,
        concept_quote: concept_quote,
        concept_code_block: concept_code_block,
        callout_box: callout_box,
        concept_table: concept_table,
        section_header_banner: section_header_banner,
        render_concept_example: render_concept_example,
        conditions_box: conditions_box,
        bogi_box: bogi_box,
        choices_grid: choices_grid,
        given_box_render: given_box_render,
        passage_box: passage_box,
        points_badge: points_badge,
        topic_badge: topic_badge,
        KOREAN_FONTS: KOREAN_FONTS,
        KOREAN_SANS_FONTS: KOREAN_SANS_FONTS,
        KOREAN_SERIF_FONTS: KOREAN_SERIF_FONTS,
      )
    )
  } else {
    val
  }
}

#let to_markup = to_concept_markup
