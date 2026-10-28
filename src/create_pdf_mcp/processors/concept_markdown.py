import re
from typing import Any
from ..processors.math_text import latex_math_to_typst


_UL_START = "\uE001"
_UL_END = "\uE002"
_BOLD_START = "\uE003"
_BOLD_END = "\uE004"
_ITALIC_START = "\uE005"
_ITALIC_END = "\uE006"
_STRIKE_START = "\uE007"
_STRIKE_END = "\uE008"
_HL_START = "\uE009"
_HL_END = "\uE00A"
_ESCAPED_DOLLAR = "\uE00B"
_CODE_START = "\uE00C"
_CODE_END = "\uE00D"


def concept_inline_to_typst(text: str, theme: str = "blue") -> str:
    """
    Converts inline Markdown (bold, italic, strike, highlight, inline code, underlines, blanks)
    and LaTeX math ($...$, $$...$$, \\(...\\), \\[...]\\) to native Typst markup.
    """
    if not text:
        return ""

    s = text.replace(r"\$", _ESCAPED_DOLLAR)

    # 1. HTML tags: <u>...</u>, <mark>...</mark>, <b>...</b>, <i>...</i>, <del>...</del>
    s = re.sub(r"<u>(.*?)</u>", lambda m: f"{_UL_START}{m.group(1)}{_UL_END}", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<mark>(.*?)</mark>", lambda m: f"{_HL_START}{m.group(1)}{_HL_END}", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<b>(.*?)</b>", lambda m: f"{_BOLD_START}{m.group(1)}{_BOLD_END}", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<i>(.*?)</i>", lambda m: f"{_ITALIC_START}{m.group(1)}{_ITALIC_END}", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<del>(.*?)</del>", lambda m: f"{_STRIKE_START}{m.group(1)}{_STRIKE_END}", s, flags=re.DOTALL | re.IGNORECASE)

    # 2. LaTeX math display/inline normalization
    s = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", s, flags=re.DOTALL)
    s = re.sub(r"\\\((.*?)\\\)", r"$\1$", s, flags=re.DOTALL)

    pattern = re.compile(r"(\$\$.*?\$\$|\$[^$\n]+?\$(?![0-9a-zA-Z]))", re.DOTALL)
    parts = pattern.split(s)
    tokens: list[str] = []

    for part in parts:
        if not part:
            continue
        if part.startswith("$$") and part.endswith("$$") and len(part) >= 4:
            math_content = part[2:-2].strip()
            converted = latex_math_to_typst(math_content)
            tokens.append(f"\n$ {converted} $\n")
        elif part.startswith("$") and part.endswith("$") and len(part) >= 2 and "\n" not in part:
            math_content = part[1:-1].strip()
            converted = latex_math_to_typst(math_content)
            tokens.append(f"${converted}$")
        else:
            tokens.append(_format_plain_text(part, theme=theme))

    return "".join(tokens)


def _format_plain_text(part: str, theme: str = "blue") -> str:
    """Escapes Typst special characters while processing Markdown inline tags."""
    t = part
    txt_ph: list[str] = []

    def _add_ph(val: str) -> str:
        idx = len(txt_ph)
        txt_ph.append(val)
        return f"\x00TXTPH{idx}\x00"

    # Inline code: `code`
    def _repl_code(m: re.Match) -> str:
        code_txt = m.group(1).replace("\\", "\\\\").replace('"', '\\"')
        return _add_ph(f'#raw("{code_txt}")')

    t = re.sub(r"`([^`\n]+)`", _repl_code, t)

    # Highlights: ==text==
    t = re.sub(r"==([^=\n]+?)==", lambda m: f"{_HL_START}{m.group(1)}{_HL_END}", t)

    # Underline: __text__
    t = re.sub(r"__([^_\n]+?)__", lambda m: f"{_UL_START}{m.group(1)}{_UL_END}", t)

    # Strike: ~~text~~
    t = re.sub(r"~~([^~\n]+?)~~", lambda m: f"{_STRIKE_START}{m.group(1)}{_STRIKE_END}", t)

    # Blanks: [빈칸: 라벨] or [빈칸] / (빈칸)
    def _repl_labeled_blank(m: re.Match) -> str:
        lbl = m.group(1).strip().replace("#", r"\#").replace("@", r"\@").replace("<", r"\<").replace("_", r"\_")
        return _add_ph(
            f'#box(stroke: 0.6pt + rgb("#333"), inset: (x: 5pt, y: 1.5pt), baseline: 20%, radius: 1.5pt)[#text(size: 8.8pt)[{lbl}]]'
        )

    t = re.sub(r"\[\s*빈칸\s*:\s*([^\]]+?)\s*\]", _repl_labeled_blank, t)
    t = re.sub(
        r"\[\s*빈칸\s*\]|\(\s*빈칸\s*\)",
        lambda _: _add_ph(
            '#box(width: 3.2em, height: 1.05em, baseline: 18%, stroke: 0.6pt + rgb("#333"), radius: 1.5pt)[]'
        ),
        t,
    )

    # Underscores: 2 or more consecutive underscores
    def _repl_underscore_blank(m: re.Match) -> str:
        count = len(m.group(0))
        width_em = max(2.5, min(10.0, count * 0.55))
        return _add_ph(
            f'#box(width: {width_em:.1f}em, height: 0.8em, baseline: 12%, stroke: (bottom: 0.6pt + rgb("#333")))[#h({width_em:.1f}em)]'
        )

    t = re.sub(r"_{2,}", _repl_underscore_blank, t)

    # Bold: **text**
    t = re.sub(r"\*\*(.+?)\*\*", lambda m: f"{_BOLD_START}{m.group(1)}{_BOLD_END}", t)

    # Italic: *text* (when not preceded/followed by *)
    t = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", lambda m: f"{_ITALIC_START}{m.group(1)}{_ITALIC_END}", t)

    # Escape Typst specials
    t = t.replace("\\", "")
    t = t.replace("#", r"\#")
    t = t.replace("@", r"\@")
    t = t.replace("$", r"\$")
    t = t.replace("<", r"\<")
    t = t.replace("~", r"\~")
    t = t.replace("*", r"\*")
    t = t.replace("_", r"\_")
    t = t.replace("//", r"\/")
    t = re.sub(r"(?m)^(\s*)=", r"\1\\=", t)

    # Restore placeholders
    t = t.replace(_BOLD_START, "*").replace(_BOLD_END, "*")
    t = t.replace(_ITALIC_START, "_").replace(_ITALIC_END, "_")
    t = t.replace(_STRIKE_START, "#strike[").replace(_STRIKE_END, "]")
    t = t.replace(_UL_START, "#underline[").replace(_UL_END, "]")
    t = t.replace(_HL_START, f'#concept_highlight(theme: "{theme}")[').replace(_HL_END, "]")
    t = t.replace(_ESCAPED_DOLLAR, "$")

    for idx, ph_val in enumerate(txt_ph):
        t = t.replace(f"\x00TXTPH{idx}\x00", ph_val)

    return t


def _parse_pipe_table(table_lines: list[str], theme: str = "blue") -> str:
    """Converts GitHub-flavored Markdown pipe table lines to Typst concept_table macro."""
    if len(table_lines) < 2:
        return "\n".join(table_lines)

    rows_data: list[list[str]] = []
    aligns: list[str] = []

    for line_idx, line in enumerate(table_lines):
        line = line.strip()
        if not line:
            continue
        # Split by pipe, stripping leading/trailing pipes
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line)]
        if cells and cells[0] == "":
            cells.pop(0)
        if cells and cells[-1] == "":
            cells.pop()

        if line_idx == 1 and all(re.match(r"^:?-+:?$", c.replace(" ", "")) for c in cells):
            # This is separator line
            for c in cells:
                c = c.replace(" ", "")
                if c.startswith(":") and c.endswith(":"):
                    aligns.append("center")
                elif c.endswith(":"):
                    aligns.append("right")
                else:
                    aligns.append("left")
            continue

        converted_cells = [f"[{concept_inline_to_typst(c, theme=theme)}]" for c in cells]
        rows_data.append(converted_cells)

    if not rows_data:
        return ""

    headers = rows_data[0]
    body_rows = rows_data[1:] if len(rows_data) > 1 else []
    col_count = len(headers)

    if not aligns or len(aligns) != col_count:
        aligns = ["left"] * col_count

    col_widths = ", ".join(["1fr"] * col_count)
    align_strs = ", ".join(aligns)
    header_str = ", ".join(headers)

    row_strs = []
    for r in body_rows:
        # pad row if shorter
        while len(r) < col_count:
            r.append("[]")
        row_strs.append(f"({', '.join(r[:col_count])})")
    rows_joined = ", ".join(row_strs)

    return (
        f'#align(center)[\n'
        f'  #concept_table(\n'
        f'    columns: ({col_widths}),\n'
        f'    aligns: ({align_strs}),\n'
        f'    headers: ({header_str}),\n'
        f'    rows: ({rows_joined}),\n'
        f'    theme: "{theme}"\n'
        f'  )\n'
        f']\n'
    )


_CALLOUT_MAP = {
    "개념": "concept",
    "concept": "concept",
    "정의": "definition",
    "definition": "definition",
    "공식": "formula",
    "formula": "formula",
    "주의": "warning",
    "경고": "warning",
    "warning": "warning",
    "caution": "warning",
    "팁": "tip",
    "tip": "tip",
    "point": "tip",
    "핵심": "tip",
    "예시": "example",
    "example": "example",
    "지문": "passage",
    "지문분석": "passage",
    "passage": "passage",
    "문법": "grammar",
    "grammar": "grammar",
    "요약": "summary",
    "summary": "summary",
    "보조단": "sidebar",
    "sidebar": "sidebar",
    "note": "note",
    "참고": "note",
}


def concept_markdown_to_typst(
    markdown_text: str,
    theme: str = "blue",
    figure_svgs: list[str] | None = None,
) -> tuple[str, list[str]]:
    """
    Parses a complete Markdown document for a Concept Book and returns:
      - typst_code: Converted Typst markup code
      - extracted_sidebar_notes: List of text blocks extracted from `> [!보조단]` directives
    """
    if not markdown_text:
        return "", []

    fig_svgs = figure_svgs or []
    used_fig_indices: set[int] = set()
    extracted_sidebar: list[str] = []

    lines = markdown_text.splitlines()
    out_lines: list[str] = []
    idx = 0
    n = len(lines)

    while idx < n:
        line = lines[idx]
        stripped = line.strip()

        # 1. Blank line
        if not stripped:
            out_lines.append("")
            idx += 1
            continue

        # 2. Horizontal rule: ---, ***, ___
        if re.match(r"^(\*{3,}|-{3,}|_{3,})$", stripped):
            out_lines.append(f'#v(0.3em)\n#line(length: 100%, stroke: 0.5pt + rgb("#cbd5e1"))\n#v(0.3em)')
            idx += 1
            continue

        # 3. Fenced Code Block: ```lang ... ```
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "text"
            code_lines = []
            idx += 1
            while idx < n and not lines[idx].strip().startswith("```"):
                code_lines.append(lines[idx])
                idx += 1
            if idx < n and lines[idx].strip().startswith("```"):
                idx += 1
            full_code = "\n".join(code_lines).replace("\\", "\\\\").replace('"', '\\"')
            out_lines.append(f'#concept_code_block(lang: "{lang}", code: "{full_code}", theme: "{theme}")')
            continue

        # 4. Figure Placeholders: {{fig:0}}, {{figure:0}}, ![caption](fig:0), ![caption](figure:0)
        fig_match = re.match(r"^(?:\{\{\s*(?:fig|figure):(\d+)\s*\}\}|!\[(.*?)\]\((?:fig|figure):(\d+)\))$", stripped, re.IGNORECASE)
        if fig_match:
            f_idx_str = fig_match.group(1) or fig_match.group(3)
            f_idx = int(f_idx_str)
            caption = fig_match.group(2) if fig_match.group(2) else ""
            if 0 <= f_idx < len(fig_svgs):
                used_fig_indices.add(f_idx)
                svg_encoded = fig_svgs[f_idx].replace("\\", "\\\\").replace('"', '\\"')
                cap_typ = f'#text(size: 8.5pt, fill: rgb("#555"))[{caption}]' if caption else 'none'
                out_lines.append(
                    f'#v(0.4em)\n#align(center)[\n'
                    f'  #image(bytes("{svg_encoded}"), format: "svg")\n'
                    f'  #if {cap_typ} != none [ #v(2pt) #caption ]\n'
                    f']\n#v(0.4em)'
                )
            idx += 1
            continue

        # 5. Callouts / Blockquotes: > ...
        if stripped.startswith(">"):
            quote_lines = []
            while idx < n and (
                lines[idx].strip().startswith(">")
                or (
                    lines[idx].strip()
                    and not lines[idx].strip().startswith(("#", "-", "*", "+", "1.", "|", "```"))
                )
            ):
                q_raw = lines[idx].strip()
                # If we already have at least one line and the next line starts a new [!CALLOUT], break here
                if quote_lines and re.match(r"^>\s*\[!", q_raw):
                    break
                q_line = q_raw[1:].strip() if q_raw.startswith(">") else q_raw
                quote_lines.append(q_line)
                idx += 1

            first_q = quote_lines[0] if quote_lines else ""
            # Check if callout header: [!TYPE] Title
            callout_m = re.match(r"^\[!\s*([a-zA-Z가-힣]+)\s*\]\s*(.*)$", first_q)
            if callout_m:
                raw_type = callout_m.group(1).lower()
                c_title = callout_m.group(2).strip()
                c_kind = _CALLOUT_MAP.get(raw_type, "note")
                body_text = "\n".join(quote_lines[1:]).strip()

                if c_kind == "sidebar":
                    # Sidebar directive: extract for sidebar
                    if c_title and body_text:
                        extracted_sidebar.append(f"{c_title}: {body_text}")
                    elif c_title:
                        extracted_sidebar.append(c_title)
                    elif body_text:
                        extracted_sidebar.append(body_text)
                    continue

                if not c_title:
                    default_titles = {
                        "concept": "핵심 개념",
                        "definition": "정의",
                        "formula": "핵심 공식",
                        "warning": "주의 / 오개념 체크",
                        "tip": "암기 팁 & 핵심 포인트",
                        "example": "예시",
                        "passage": "지문 / 작품 분석",
                        "grammar": "문법 포인트",
                        "summary": "단원 요약",
                        "note": "참고",
                    }
                    c_title = default_titles.get(c_kind, "참고")

                c_title_typ = concept_inline_to_typst(c_title, theme=theme)
                c_body_typ = concept_inline_to_typst(body_text, theme=theme)

                out_lines.append(
                    f'#callout_box(kind: "{c_kind}", title: [{c_title_typ}], theme: "{theme}")[\n'
                    f'  {c_body_typ}\n'
                    f']'
                )
            else:
                # Regular blockquote
                body_text = "\n".join(quote_lines).strip()
                b_typ = concept_inline_to_typst(body_text, theme=theme)
                out_lines.append(f'#concept_quote(theme: "{theme}")[\n  {b_typ}\n]')
            continue

        # 6. Pipe Tables: | ... |
        if stripped.startswith("|") and stripped.endswith("|") and "|" in stripped[1:-1]:
            table_lines = []
            while idx < n and lines[idx].strip().startswith("|") and lines[idx].strip().endswith("|"):
                table_lines.append(lines[idx].strip())
                idx += 1
            out_lines.append(_parse_pipe_table(table_lines, theme=theme))
            continue

        # 7. Headings: #, ##, ###, ####
        heading_m = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading_m:
            level = len(heading_m.group(1))
            h_text = heading_m.group(2).strip()
            h_typ = concept_inline_to_typst(h_text, theme=theme)
            h_typ = re.sub(r"^(\d+)\.(\s+)", r"\1\\.\2", h_typ)
            out_lines.append(f'#concept_subheading(level: {level}, theme: "{theme}")[{h_typ}]')
            idx += 1
            continue

        # 8. Lists: - , * , + , or 1.
        list_m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.+)$", line)
        if list_m:
            indent_spaces = len(list_m.group(1))
            bullet = list_m.group(2)
            content = list_m.group(3).strip()
            c_typ = concept_inline_to_typst(content, theme=theme)

            typst_bullet = "+" if bullet.endswith(".") else "-"
            indent_prefix = "  " * (indent_spaces // 2)
            out_lines.append(f"{indent_prefix}{typst_bullet} {c_typ}")
            idx += 1
            continue

        # 9. Normal paragraph text
        p_typ = concept_inline_to_typst(stripped, theme=theme)
        out_lines.append(p_typ)
        idx += 1

    # Render any unused figures at the end of the section
    unused_figs = [fig_svgs[i] for i in range(len(fig_svgs)) if i not in used_fig_indices]
    for u_fig in unused_figs:
        u_encoded = u_fig.replace("\\", "\\\\").replace('"', '\\"')
        out_lines.append(
            f'#v(0.4em)\n#align(center)[#image(bytes("{u_encoded}"), format: "svg")]\n#v(0.4em)'
        )

    typst_body = "\n".join(out_lines)
    return typst_body, extracted_sidebar


def split_markdown_into_sections(markdown_text: str) -> list[dict[str, Any]]:
    """
    Splits a single raw Markdown text by # or ## into structured section dictionaries.
    """
    if not markdown_text:
        return []

    lines = markdown_text.splitlines()
    sections: list[dict[str, Any]] = []
    current_title = ""
    current_badge = ""
    current_lines: list[str] = []

    def _flush():
        nonlocal current_title, current_badge, current_lines
        body = "\n".join(current_lines).strip()
        if current_title or body:
            title = current_title or "개념 요약"
            sections.append({
                "badge": current_badge or None,
                "title": title,
                "markdown": body,
            })
        current_title = ""
        current_badge = ""
        current_lines = []

    for line in lines:
        h_match = re.match(r"^(#{1,2})\s+(.+)$", line.strip())
        if h_match:
            _flush()
            raw_h = h_match.group(2).strip()
            # Check if header contains badge like "[개념 01] 미분" or "CHAPTER 1. 미분"
            badge_m = re.match(r"^\[(.*?)\]\s*(.+)$", raw_h)
            if badge_m:
                current_badge = badge_m.group(1).strip()
                current_title = badge_m.group(2).strip()
            else:
                chap_m = re.match(r"^((?:Chapter|CHAPTER|단원|개념|Theme)\s*[\w\d]+)[:.]?\s*(.+)$", raw_h, re.IGNORECASE)
                if chap_m:
                    current_badge = chap_m.group(1).strip()
                    current_title = chap_m.group(2).strip()
                else:
                    current_title = raw_h
        else:
            current_lines.append(line)

    _flush()
    return sections
