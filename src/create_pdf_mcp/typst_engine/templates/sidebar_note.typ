// Asymmetric Sidebar Concept Note Layout (Lecture / Study Guide Style)
#import "concept_base.typ": *

#let render_sidebar_note(
  title: "개념서",
  subtitle: none,
  subject_badge: none,
  footer_text: none,
  footer_note: none,
  color_theme: "emerald",
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
    margin: (left: 14mm, right: 14mm, top: d_cfg.margin_y, bottom: d_cfg.margin_y),
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
      inset: (x: 11pt, y: 7.5pt),
      radius: 4pt,
      [
        #text(size: 10pt, weight: "bold", fill: th.primary_dark)[목 차 (Contents)]\
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

    // Wrap the entire section (Banner + Left Sidebar + Right Main Body) in a block
    // so short/medium sections never split awkwardly at the bottom of a page.
    #block(
      width: 100%,
      breakable: sec.at("is_breakable", default: false),
      above: if idx == 0 { 0.2em } else { d_cfg.section_gap },
      below: 0.4em,
    )[
      // Section header across full width
      #section_header_banner(
        badge: sec.at("badge", default: none),
        title: sec.title,
        subtitle: sec.at("subtitle", default: none),
        objectives: sec.at("learning_objectives", default: ()),
        theme: color_theme,
      )

      // 2-Column Asymmetric layout per section: Left sidebar (42mm) + Right main body (1fr)
      #grid(
        columns: (42mm, 1fr),
        column-gutter: 12pt,
        align: (left + top, left + top),
        [
          // Left Column: Sidebar Notes / Key terms
          #block(
            width: 100%,
            breakable: false,
            fill: th.accent,
            stroke: (right: 1.5pt + th.border),
            inset: (x: 7pt, y: 6.5pt),
            radius: 2pt,
            [
              #text(size: 8.6pt, weight: "bold", fill: th.primary_dark)[◆ 핵심 키워드 / 노트]\
              #v(3.5pt)
              #if sec.at("sidebar_notes", default: ()).len() > 0 [
                #for sn in sec.sidebar_notes [
                  #v(2.5pt)
                  #text(size: 8.1pt, fill: rgb("#334155"))[• #to_markup(sn)]
                ]
              ] else [
                #text(size: 8pt, fill: rgb("#64748b"))[(단원 핵심 개념 및 필기 공간)]
              ]
            ]
          )
        ],
        [
          // Right Column: Main Body
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

          // Section Examples
          #for ex in sec.at("examples", default: ()) [
            #render_concept_example(
              ex,
              theme: color_theme,
              solution_mode: example_solution_mode,
            )
          ]
        ]
      )
    ]
  ]
}
