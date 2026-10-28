// 2-Column Summary Sheet / Cheat-Sheet Concept Layout
#import "concept_base.typ": *

#let render_summary_2col(
  title: "핵심 요약노트",
  subtitle: none,
  subject_badge: none,
  footer_text: none,
  footer_note: none,
  color_theme: "amber",
  font_style: "sans",
  show_toc: false,
  example_solution_mode: "inline",
  density: "normal",
  sections: ()
) = {
  let th = get_theme(color_theme)
  let fonts = get_korean_fonts(font_style)

  set text(
    font: fonts,
    size: if density == "compact" { 8.8pt } else { 9.2pt },
    lang: "ko",
    fill: rgb("#0f172a"),
  )
  show math.equation: set text(font: MATH_FONTS)
  set par(leading: 0.65em, spacing: 0.5em, justify: true)

  set page(
    paper: "a4",
    margin: (x: 12mm, top: 13mm, bottom: 13mm),
    header: context {
      if counter(page).get().first() > 1 {
        grid(
          columns: (1fr, auto, 1fr),
          align: (left, center, right),
          [#text(size: 8pt, fill: rgb("#64748b"))[#title]],
          [
            #if subtitle != none [
              #text(size: 8pt, fill: rgb("#475569"), weight: "bold")[#subtitle]
            ]
          ],
          [
            #if subject_badge != none [
              #box(fill: th.accent, inset: (x: 4pt, y: 1pt), radius: 2pt)[
                #text(size: 7.5pt, fill: th.primary_dark, weight: "bold")[#subject_badge]
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
      v(2pt)
      grid(
        columns: (1fr, auto, 1fr),
        align: (left + horizon, center + horizon, right + horizon),
        [
          #if footer_text != none [
            #text(size: 7.8pt, fill: rgb("#64748b"))[#footer_text]
          ]
        ],
        [
          #text(size: 8pt, fill: rgb("#475569"))[- #counter(page).get().first() -]
        ],
        [
          #if footer_note != none [
            #text(size: 7.2pt, fill: rgb("#94a3b8"))[#footer_note]
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

  // 2-Column body
  columns(2, gutter: 14pt)[
    #for (idx, sec) in sections.enumerate() [
      #if sec.at("page_break_before", default: false) and idx > 0 [
        #colbreak()
      ]

      #block(
        width: 100%,
        breakable: sec.at("is_breakable", default: false),
        above: if idx == 0 { 0.2em } else { 0.9em },
        below: 0.4em,
      )[
        #section_header_banner(
          badge: sec.at("badge", default: none),
          title: sec.title,
          subtitle: sec.at("subtitle", default: none),
          objectives: sec.at("learning_objectives", default: ()),
          theme: color_theme,
        )

        #if sec.at("typst_body", default: none) != none [
          #to_markup(sec.typst_body)
        ]

        #for callout in sec.at("callouts", default: ()) [
          #callout_box(
            kind: callout.at("type", default: "concept"),
            title: callout.at("title", default: none),
            theme: color_theme,
            to_markup(callout.content)
          )
        ]

        #if sec.at("sidebar_notes", default: ()).len() > 0 [
          #block(
            width: 100%,
            breakable: false,
            above: 0.3em,
            below: 0.3em,
            fill: th.accent,
            stroke: (left: 2.5pt + th.primary),
            inset: (x: 7pt, y: 5pt),
            radius: 2pt,
            [
              #text(size: 8.4pt, weight: "bold", fill: th.primary)[◆ 요약 정리]\
              #for sn in sec.sidebar_notes [
                #v(1.5pt)
                #text(size: 8pt, fill: rgb("#334155"))[• #to_markup(sn)]
              ]
            ]
          )
        ]

        #for ex in sec.at("examples", default: ()) [
          #render_concept_example(
            ex,
            theme: color_theme,
            solution_mode: example_solution_mode,
          )
        ]
      ]
    ]
  ]
}
