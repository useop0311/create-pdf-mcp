import io
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from pypdf import PdfReader
import typst

logger = logging.getLogger(__name__)

from ..models.exam import ExamPDFRequest, PassageGroup, ProblemItem
from ..processors.math_text import markdown_to_typst
from ..processors.figure_renderer import render_figure_to_svg


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _escape_typst_string(s: str) -> str:
    """Escapes string literal for Typst code."""
    if not s:
        return '""'
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _join_text_or_list(val: str | list[str] | None) -> str:
    if not val:
        return ""
    if isinstance(val, list):
        return "\n\n".join(str(x).strip() for x in val if str(x).strip())
    return str(val).strip()


def _normalize_footnotes(footnotes: list[str] | str | None) -> list[str]:
    if not footnotes:
        return []
    if isinstance(footnotes, str):
        lines = [line.strip() for line in footnotes.splitlines() if line.strip()]
        return [markdown_to_typst(line) for line in lines]
    return [markdown_to_typst(str(fn).strip()) for fn in footnotes if str(fn).strip()]


def _format_range_header(range_str: str | None) -> str | None:
    """
    Formats a passage range string like '1~3', '[1~3]', or '[41~42] 다음 글을 읽고, 물음에 답하시오.'
    into a standard CSAT group instruction header.
    """
    if not range_str:
        return None
    s = range_str.strip()
    if not s:
        return None
    # Pure numbers range like '1~3' or '1-3'
    m_pure = re.match(r"^(\d+)\s*[~-]\s*(\d+)$", s)
    if m_pure:
        return f"[{m_pure.group(1)}~{m_pure.group(2)}] 다음 글을 읽고 물음에 답하시오."
    # Single number like '1' or '[1]'
    m_single = re.match(r"^\[?(\d+)\]?$", s)
    if m_single:
        return f"[{m_single.group(1)}] 다음 글을 읽고 물음에 답하시오."
    # Bracketed range only like '[1~3]' or '[1-3]'
    m_bracket = re.match(r"^\[(\d+)\s*[~-]\s*(\d+)\]$", s)
    if m_bracket:
        return f"[{m_bracket.group(1)}~{m_bracket.group(2)}] 다음 글을 읽고 물음에 답하시오."
    return s


def _parse_range_numbers(range_str: str | None) -> tuple[int, int] | None:
    if not range_str:
        return None
    m = re.search(r"\[?(\d+)\s*[~-]\s*(\d+)\]?", range_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    m_single = re.match(r"^\[?(\d+)\]?(?:\s|$)", range_str.strip())
    if m_single:
        n = int(m_single.group(1))
        return n, n
    return None


def _build_passage_dict(
    raw_passage: str | list[str] | None,
    header: str | None = None,
    title: str | None = None,
    source: str | None = None,
    footnotes: list[str] | str | None = None,
) -> dict | None:
    joined = _join_text_or_list(raw_passage)
    if not joined:
        return None
    return {
        "header": markdown_to_typst(header) if header else None,
        "title": markdown_to_typst(title) if title else None,
        "content": markdown_to_typst(joined),
        "source": markdown_to_typst(source) if source else None,
        "footnotes": _normalize_footnotes(footnotes),
    }


def _resolve_passage_assignments(request: ExamPDFRequest) -> tuple[dict[int, dict], dict[int, dict], set[int], set[int]]:
    """
    Resolves shared/group passages and deduplicates identical consecutive passages.
    Returns:
      - pre_passages_by_idx: problem index -> passage_dict to render BEFORE the problem in exam_2col/workbook
      - pad_passages_by_idx: problem index -> passage_dict to render at the top of the page in pad_1p1q
      - has_passage_context_indices: set of problem indices that have a passage or belong to a shared passage group
      - consumed_problem_passage_indices: set of problem indices whose p.passage was promoted/deduplicated into pre_passages
    """
    problems = request.problems
    num_to_idx: dict[int, int] = {}
    for idx, p in enumerate(problems):
        num = p.number or (idx + 1)
        num_to_idx[num] = idx

    pre_passages_by_idx: dict[int, dict] = {}
    pad_passages_by_idx: dict[int, dict] = {}
    has_passage_context_indices: set[int] = set()
    consumed_problem_passage_indices: set[int] = set()

    # 1. Process explicit request.passage_groups
    for pg in request.passage_groups:
        target_nums: list[int] = []
        if pg.problem_numbers:
            target_nums = sorted(pg.problem_numbers)
        elif pg.start_number is not None and pg.end_number is not None:
            target_nums = list(range(pg.start_number, pg.end_number + 1))
        elif pg.start_number is not None:
            target_nums = [pg.start_number]

        target_indices = [num_to_idx[n] for n in target_nums if n in num_to_idx]
        if not target_indices and problems:
            target_indices = [0]
            target_nums = [problems[0].number or 1]

        if not target_indices:
            continue

        first_num = target_nums[0]
        last_num = target_nums[-1]
        default_hdr = (
            f"[{first_num}~{last_num}] 다음 글을 읽고 물음에 답하시오."
            if first_num != last_num
            else f"[{first_num}] 다음 글을 읽고 물음에 답하시오."
        )
        hdr = pg.header or default_hdr
        p_dict = _build_passage_dict(
            raw_passage=pg.passage,
            header=hdr,
            title=pg.title,
            source=pg.source,
            footnotes=pg.footnotes,
        )
        if p_dict:
            first_idx = target_indices[0]
            pre_passages_by_idx[first_idx] = p_dict
            for tidx in target_indices:
                pad_passages_by_idx[tidx] = p_dict
                has_passage_context_indices.add(tidx)

    # 2. Deduplicate consecutive identical p.passage across problems (when LLM repeats shared passage on each problem)
    i = 0
    n_probs = len(problems)
    while i < n_probs:
        p = problems[i]
        raw_text = _join_text_or_list(p.passage)
        if not raw_text or i in pre_passages_by_idx:
            i += 1
            continue

        # Check how many consecutive problems share the exact same passage text
        j = i + 1
        while j < n_probs and _join_text_or_list(problems[j].passage) == raw_text:
            j += 1

        if j - i >= 2:
            # Consecutive problems [i .. j-1] share the identical passage
            first_num = problems[i].number or (i + 1)
            last_num = problems[j - 1].number or j
            hdr = _format_range_header(p.passage_range)
            title = p.passage_title
            if not hdr:
                if title and re.match(r"^\[?\d+\s*[~-]\s*\d+\]?", title.strip()):
                    hdr = _format_range_header(title)
                    title = None
                else:
                    hdr = f"[{first_num}~{last_num}] 다음 글을 읽고 물음에 답하시오."

            p_dict = _build_passage_dict(
                raw_passage=p.passage,
                header=hdr,
                title=title,
                source=p.passage_source,
                footnotes=p.passage_footnotes,
            )
            if p_dict:
                pre_passages_by_idx[i] = p_dict
                for k in range(i, j):
                    pad_passages_by_idx[k] = p_dict
                    has_passage_context_indices.add(k)
                    consumed_problem_passage_indices.add(k)
            i = j
            continue

        # 3. Single problem with passage_range or before_stem or range-like passage_title
        title_looks_like_range = bool(
            p.passage_title and re.match(r"^\[?\d+\s*[~-]\s*\d+\]?", p.passage_title.strip())
        )
        is_before = (
            p.passage_position == "before_stem"
            or bool(p.passage_range)
            or (p.passage_position == "auto" and title_looks_like_range)
        )
        if is_before:
            hdr = _format_range_header(p.passage_range)
            title = p.passage_title
            if not hdr and title_looks_like_range:
                hdr = _format_range_header(title)
                title = None
            elif hdr and title and hdr == title:
                title = None

            p_dict = _build_passage_dict(
                raw_passage=p.passage,
                header=hdr,
                title=title,
                source=p.passage_source,
                footnotes=p.passage_footnotes,
            )
            if p_dict:
                pre_passages_by_idx[i] = p_dict
                pad_passages_by_idx[i] = p_dict
                has_passage_context_indices.add(i)
                consumed_problem_passage_indices.add(i)

                # Mark range problems as sharing this passage context
                rng = _parse_range_numbers(p.passage_range or p.passage_title)
                if rng:
                    for rnum in range(rng[0], rng[1] + 1):
                        if rnum in num_to_idx:
                            ridx = num_to_idx[rnum]
                            has_passage_context_indices.add(ridx)
                            if ridx not in pad_passages_by_idx:
                                pad_passages_by_idx[ridx] = p_dict

        i += 1

    return (
        pre_passages_by_idx,
        pad_passages_by_idx,
        has_passage_context_indices,
        consumed_problem_passage_indices,
    )


def _build_problem_typst_data(
    p: ProblemItem,
    idx: int,
    layout_mode: str = "exam_2col",
    pre_passage: dict | None = None,
    pad_pre_passage: dict | None = None,
    has_passage_context: bool = False,
    passage_consumed: bool = False,
) -> dict:
    num = p.number or (idx + 1)
    stem_typ = markdown_to_typst(p.stem)
    conds_typ = [markdown_to_typst(c) for c in p.conditions]
    bogi_typ = [markdown_to_typst(b) for b in p.bogi]
    bogi_title_typ = markdown_to_typst(p.bogi_title) if p.bogi_title else None
    choices_typ = [
        markdown_to_typst(re.sub(r"^[①②③④⑤]\s*", "", c.strip()))
        for c in p.choices
    ]
    ans_typ = markdown_to_typst(p.answer)
    sol_typ = markdown_to_typst(p.solution) if p.solution else None

    # Build inline passage if not already consumed as pre_passage
    inline_passage = None
    raw_inline_passage_str = ""
    if p.passage and not passage_consumed:
        raw_inline_passage_str = _join_text_or_list(p.passage)
        inline_passage = _build_passage_dict(
            raw_passage=p.passage,
            header=None,
            title=p.passage_title,
            source=p.passage_source,
            footnotes=p.passage_footnotes,
        )
        if inline_passage:
            has_passage_context = True

    # Build given_box (주어진 글 / 문장 삽입 / 제시문)
    given_box_data = None
    raw_given_str = _join_text_or_list(p.given_box)
    if raw_given_str:
        given_box_data = {
            "title": markdown_to_typst(p.given_box_title) if p.given_box_title else None,
            "content": markdown_to_typst(raw_given_str),
        }
        has_passage_context = True

    # Render SVGs for figures
    figures_svg = []
    for fig in p.figures:
        try:
            figures_svg.append(render_figure_to_svg(fig))
        except Exception:
            pass

    solution_figures_svg = []
    for sfig in p.solution_figures:
        try:
            solution_figures_svg.append(render_figure_to_svg(sfig))
        except Exception:
            pass

    # Determine bottom solving space:
    # Reading-comprehension problems (Korean/English) use compact spacing by default unless solving_space_cm is explicitly set.
    if p.solving_space_cm is not None:
        solving_space = f"{p.solving_space_cm:.2f}cm"
    elif has_passage_context:
        solving_space = "0.45cm" if layout_mode == "exam_2col" else "0.65cm"
    else:
        solving_space = "1.20cm" if layout_mode == "exam_2col" else "2.00cm"

    # Determine if problem block should be breakable across columns (prevent overflow for very long inline passages)
    total_inline_chars = (
        len(p.stem)
        + len(raw_inline_passage_str)
        + len(raw_given_str)
        + sum(len(b) for b in p.bogi)
        + sum(len(c) for c in p.choices)
    )
    is_breakable = len(raw_inline_passage_str) > 500 or total_inline_chars > 700

    # Subjective question resolution
    subj_type = p.subjective_type
    if subj_type == "auto":
        if isinstance(p.subjective_box_height, (int, float)) and p.subjective_box_height >= 2.5:
            subj_type = "descriptive"
        elif p.subjective_box_height in ("small", "medium", "large"):
            subj_type = "descriptive"
        else:
            subj_type = "short_answer"

    box_h = 1.1
    if subj_type == "descriptive":
        if p.subjective_box_height == "small":
            box_h = 3.0
        elif p.subjective_box_height == "medium":
            box_h = 5.0
        elif p.subjective_box_height == "large":
            box_h = 8.0
        elif isinstance(p.subjective_box_height, (int, float)) and p.subjective_box_height > 0:
            box_h = float(p.subjective_box_height)
        else:  # auto
            box_h = 4.5
    else:  # short_answer
        if isinstance(p.subjective_box_height, (int, float)) and p.subjective_box_height > 0:
            box_h = float(p.subjective_box_height)
        else:
            box_h = 1.1

    subj_label = p.subjective_label or ("풀이 과정 및 정답" if subj_type == "descriptive" else "정답")

    return {
        "number": num,
        "points": p.points,
        "topic_tag": p.topic_tag,
        "stem": stem_typ,
        "pre_passage": pre_passage,
        "pad_pre_passage": pad_pre_passage,
        "inline_passage": inline_passage,
        "given_box": given_box_data,
        "conditions": conds_typ,
        "bogi": bogi_typ,
        "bogi_title": bogi_title_typ,
        "choices": choices_typ,
        "subjective_type": subj_type,
        "subjective_box_height": f"{box_h:.2f}cm",
        "subjective_label": subj_label,
        "figures_svg": figures_svg,
        "answer": ans_typ,
        "solution": sol_typ,
        "solution_figures_svg": solution_figures_svg,
        "solving_space": solving_space,
        "is_breakable": is_breakable,
    }


def generate_typst_document(request: ExamPDFRequest, for_solutions_only: bool = False) -> str:
    """
    Constructs the complete Typst source code by loading templates and formatting data.
    """
    (
        pre_passages_by_idx,
        pad_passages_by_idx,
        has_passage_context_indices,
        consumed_indices,
    ) = _resolve_passage_assignments(request)

    problems_data = [
        _build_problem_typst_data(
            p=p,
            idx=i,
            layout_mode=request.layout_mode,
            pre_passage=pre_passages_by_idx.get(i),
            pad_pre_passage=pad_passages_by_idx.get(i),
            has_passage_context=(i in has_passage_context_indices),
            passage_consumed=(i in consumed_indices),
        )
        for i, p in enumerate(request.problems)
    ]
    problems_json_str = json.dumps(problems_data, ensure_ascii=False)
    encoded_json = json.dumps(problems_json_str, ensure_ascii=False)

    footer_t = f'"{request.footer_text}"' if request.footer_text else "none"
    footer_n = f'"{request.footer_note}"' if request.footer_note else "none"

    lines = []
    base_path = (TEMPLATES_DIR / "base.typ").resolve().as_posix()
    lines.append(f'#import "{base_path}": *')
    lines.append(f'#let problems_data = json(bytes({encoded_json}))')

    if for_solutions_only:
        sol_path = (TEMPLATES_DIR / "solutions.typ").resolve().as_posix()
        lines.append(f'#import "{sol_path}": *')
        lines.append(
            f'#render_solutions('
            f'title: "정답 및 해설", '
            f'footer_text: {footer_t}, '
            f'footer_note: {footer_n}, '
            f'problems: problems_data'
            f')'
        )
        return "\n".join(lines)

    layout = request.layout_mode
    if layout == "exam_2col":
        tmpl_path = (TEMPLATES_DIR / "exam_2col.typ").resolve().as_posix()
        lines.append(f'#import "{tmpl_path}": *')
        sub_badge = f'"{request.subject_badge}"' if request.subject_badge else "none"
        subtitle = f'"{request.subtitle}"' if request.subtitle else "none"

        lines.append(
            f'#render_exam_2col('
            f'title: "{request.title}", '
            f'subtitle: {subtitle}, '
            f'subject_badge: {sub_badge}, '
            f'footer_text: {footer_t}, '
            f'footer_note: {footer_n}, '
            f'problems: problems_data'
            f')'
        )

    elif layout == "pad_1p1q":
        tmpl_path = (TEMPLATES_DIR / "pad_1p1q.typ").resolve().as_posix()
        lines.append(f'#import "{tmpl_path}": *')
        sub_badge = f'"{request.subject_badge}"' if request.subject_badge else "none"
        subtitle = f'"{request.subtitle}"' if request.subtitle else "none"

        lines.append(
            f'#render_pad_1p1q('
            f'title: "{request.title}", '
            f'subtitle: {subtitle}, '
            f'subject_badge: {sub_badge}, '
            f'footer_text: {footer_t}, '
            f'footer_note: {footer_n}, '
            f'pad_note_style: "{request.pad_note_style}", '
            f'problems: problems_data'
            f')'
        )

    else:  # workbook
        tmpl_path = (TEMPLATES_DIR / "workbook.typ").resolve().as_posix()
        lines.append(f'#import "{tmpl_path}": *')
        sub_badge = f'"{request.subject_badge}"' if request.subject_badge else "none"
        subtitle = f'"{request.subtitle}"' if request.subtitle else "none"

        lines.append(
            f'#render_workbook('
            f'title: "{request.title}", '
            f'subtitle: {subtitle}, '
            f'subject_badge: {sub_badge}, '
            f'footer_text: {footer_t}, '
            f'footer_note: {footer_n}, '
            f'problems: problems_data'
            f')'
        )

    # Append solutions at the end if requested
    if request.answer_sheet_mode == "append":
        sol_path = (TEMPLATES_DIR / "solutions.typ").resolve().as_posix()
        lines.append(f'#import "{sol_path}": *')
        lines.append('#pagebreak()')
        lines.append(
            f'#render_solutions('
            f'title: "정답 및 해설", '
            f'footer_text: {footer_t}, '
            f'footer_note: {footer_n}, '
            f'problems: problems_data'
            f')'
        )

    return "\n".join(lines)


def compile_typst_to_pdf(typst_source: str) -> bytes:
    """
    Compiles Typst source string into PDF bytes using typst Python library.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".typ", delete=False, encoding="utf-8") as f:
        f.write(typst_source)
        temp_path = f.name

    try:
        pdf_bytes = typst.compile(temp_path, root="/")
        return pdf_bytes
    except Exception as e:
        logger.error(f"Typst compilation failed: {e}\nTypst source snippet:\n{typst_source[:1500]}")
        raise
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Returns total number of pages in the PDF."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return len(reader.pages)
    except Exception:
        return 1
