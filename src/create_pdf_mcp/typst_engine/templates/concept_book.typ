// 1-Column Textbook Concept Layout
#import "concept_base.typ": *

#let render_concept_book(
  title: "개념서",
  subtitle: none,
  subject_badge: none,
  footer_text: none,
  footer_note: none,
  color_theme: "blue",
  font_style: "sans",
  show_toc: false,
  example_solution_mode: "inline",
  density: "normal",
  sections: ()
) = {
  let th = get_theme(color_theme)
  let fonts = get_korean_fonts(font_style)
  let d_cfg = get_density_config(density)

  set text(
    font: fonts,
    size: d_cfg.body_size,
    lang: "ko",
    fill: rgb("#0f172a"),
  )
  show math.equation: set text(font: MATH_FONTS)
  set par(leading: d_cfg.leading, spacing: d_cfg.par_spacing, justify: true)

  set page(
    paper: "a4",
    margin: (x: d_cfg.margin_x, top: d_cfg.margin_y, bottom: d_cfg.margin_y),
    header: context {
      if counter(page).get().first() > 1 {
        grid(
          columns: (1fr, auto, 1fr),
          align: (left, center, right),
          [#text(size: 8.5pt, fill: rgb("#64748b"))[#title]],
          [
            #if subtitle != none [
              #text(size: 8.5pt, fill: rgb("#475569"), weight: "bold")[#subtitle]
            ]
          ],
          [
            #if subject_badge != none [
              #box(fill: th.accent, inset: (x: 5pt, y: 1.5pt), radius: 2pt)[
                #text(size: 7.8pt, fill: th.primary_dark, weight: "bold")[#subject_badge]
              ]
            ]
          ]
        )
        v(2pt)
        line(length: 100%, stroke: 0.4pt + rgb("#cbd5e1"))
      }
    },
    footer: context {
      line(length: 100%, stroke: 0.4pt + rgb("#cbd5e1"))
      v(3pt)
      grid(
        columns: (1fr, auto, 1fr),
        align: (left + horizon, center + horizon, right + horizon),
        [
          #if footer_text != none [
            #text(size: 8pt, fill: rgb("#64748b"))[#footer_text]
          ]
        ],
        [
          #text(size: 8.5pt, fill: rgb("#475569"))[- #counter(page).get().first() -]
        ],
        [
          #if footer_note != none [
            #text(size: 7.5pt, fill: rgb("#94a3b8"))[#footer_note]
          ]
        ]
      )
    }
  )

  // Document Title Banner on Page 1
  concept_doc_cover_header(
    title: title,
    subtitle: subtitle,
    badge: subject_badge,
    theme: color_theme,
    density: density,
  )

  // Optional Table of Contents
  if show_toc and sections.len() > 1 {
    block(
      width: 100%,
      breakable: false,
      fill: th.accent,
      stroke: 0.6pt + th.border,
      inset: (x: 12pt, y: 8pt),
      radius: 4pt,
      [
        #text(size: 10.2pt, weight: "bold", fill: th.primary_dark)[목 차 (Contents)]\
        #v(4pt)
        #for (s_idx, sec) in sections.enumerate() [
          #let s_num = if sec.at("badge", default: none) != none { sec.badge } else { str(s_idx + 1) }
          #grid(
            columns: (auto, 1fr),
            gutter: 8pt,
            [#text(weight: "bold", fill: th.primary)[#s_num]],
            [#text(fill: rgb("#334155"))[#sec.title]]
          )
          #v(2pt)
        ]
      ]
    )
    v(0.8em)
  }

  // Iterate sections
  for (idx, sec) in sections.enumerate() [
    #if sec.at("page_break_before", default: false) and idx > 0 [
      #pagebreak()
    ]

    #block(
      width: 100%,
      breakable: sec.at("is_breakable", default: true),
      above: if idx == 0 { 0.2em } else { d_cfg.section_gap },
      below: 0.4em,
    )[
      #section_header_banner(
        badge: sec.at("badge", default: none),
        title: sec.title,
        subtitle: sec.at("subtitle", default: none),
        objectives: sec.at("learning_objectives", default: ()),
        theme: color_theme,
      )

      // Main section markdown body
      #if sec.at("typst_body", default: none) != none [
        #to_markup(sec.typst_body)
      ]

      // Structured Callouts
      #for callout in sec.at("callouts", default: ()) [
        #callout_box(
          kind: callout.at("type", default: "concept"),
          title: callout.at("title", default: none),
          theme: color_theme,
          to_markup(callout.content)
        )
      ]

      // Sidebar notes in 1-col mode become side-note boxes
      #if sec.at("sidebar_notes", default: ()).len() > 0 [
        #block(
          width: 100%,
          breakable: false,
          above: 0.4em,
          below: 0.4em,
          fill: rgb("#f8fafc"),
          stroke: (left: 3pt + th.primary, rest: 0.5pt + rgb("#e2e8f0")),
          inset: (x: 10pt, y: 6.5pt),
          radius: 2pt,
          [
            #text(size: 8.8pt, weight: "bold", fill: th.primary)[◆ 핵심 정리 & 보충 노트]\
            #for sn in sec.sidebar_notes [
              #v(2pt)
              #text(size: 8.6pt, fill: rgb("#334155"))[• #to_markup(sn)]
            ]
          ]
        )
      ]

      // Section Examples
      #for ex in sec.at("examples", default: ()) [
        #render_concept_example(
          ex,
          theme: color_theme,
          solution_mode: example_solution_mode,
        )
      ]
    ]
  ]
}
