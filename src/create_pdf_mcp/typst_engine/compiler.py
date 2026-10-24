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

from ..models.exam import ExamPDFRequest, ProblemItem, SubProblemItem
from ..processors.math_text import markdown_to_typst
from ..processors.figure_renderer import render_figure_to_svg


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _escape_typst_string(s: str) -> str:
    """Escapes string literal for Typst code."""
    if not s:
        return '""'
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _render_figures_list(figures: list) -> list[str]:
    rendered: list[str] = []
    for fig in figures:
        try:
            rendered.append(render_figure_to_svg(fig))
        except Exception:
            pass
    return rendered


def _resolve_subjective_config(
    subjective_type: str,
    subjective_box_height: float | str,
    subjective_label: str | None,
    has_choices: bool,
    has_sub_problems: bool = False,
) -> tuple[str, str, str]:
    if subjective_type == "none" or (has_sub_problems and not has_choices and subjective_type == "auto"):
        return "none", "0.00cm", ""

    subj_type = subjective_type
    if subj_type == "auto":
        if isinstance(subjective_box_height, (int, float)) and subjective_box_height >= 2.5:
            subj_type = "descriptive"
        elif subjective_box_height in ("small", "medium", "large"):
            subj_type = "descriptive"
        else:
            subj_type = "short_answer"

    box_h = 1.1
    if subj_type == "descriptive":
        if subjective_box_height == "small":
            box_h = 3.0
        elif subjective_box_height == "medium":
            box_h = 5.0
        elif subjective_box_height == "large":
            box_h = 8.0
        elif isinstance(subjective_box_height, (int, float)) and subjective_box_height > 0:
            box_h = float(subjective_box_height)
        else:  # auto
            box_h = 4.5
    else:  # short_answer
        if isinstance(subjective_box_height, (int, float)) and subjective_box_height > 0:
            box_h = float(subjective_box_height)
        else:
            box_h = 1.1

    subj_label = subjective_label or ("풀이 과정 및 정답" if subj_type == "descriptive" else "정답")
    return subj_type, f"{box_h:.2f}cm", subj_label


def _build_sub_problem_typst_data(sub: SubProblemItem, sub_idx: int) -> dict:
    if sub.number is None:
        label = f"({sub_idx + 1})"
    elif isinstance(sub.number, int):
        label = f"({sub.number})"
    else:
        s_num = str(sub.number).strip()
        label = f"({s_num})" if s_num.isdigit() else s_num

    raw_stem = sub.stem.strip()
    # Strip redundant leading sub-problem label (e.g. "(1) ...") if already matched by label
    if raw_stem.startswith(label):
        rest = raw_stem[len(label):].lstrip()
        if rest:
            raw_stem = rest
    else:
        m_dup = re.match(rf"^\(\s*{sub_idx + 1}\s*\)\s+(.+)", raw_stem, flags=re.DOTALL)
        if m_dup:
            raw_stem = m_dup.group(1).strip()

    stem_typ = markdown_to_typst(raw_stem)
    passage_typ = markdown_to_typst(sub.passage) if sub.passage else None
    conds_typ = [markdown_to_typst(c) for c in sub.conditions]
    bogi_typ = [markdown_to_typst(b) for b in sub.bogi]
    choices_typ = [markdown_to_typst(c) for c in sub.choices]
    ans_typ = markdown_to_typst(sub.answer) if sub.answer else ""
    sol_typ = markdown_to_typst(sub.solution) if sub.solution else None

    figures_svg = _render_figures_list(sub.figures)
    solution_figures_svg = _render_figures_list(sub.solution_figures)
    solving_space = f"{sub.solving_space_cm:.2f}cm" if sub.solving_space_cm is not None else "0.40cm"

    subj_type, box_h_str, subj_label = _resolve_subjective_config(
        sub.subjective_type,
        sub.subjective_box_height,
        sub.subjective_label,
        has_choices=bool(sub.choices),
        has_sub_problems=False,
    )

    return {
        "label": label,
        "points": sub.points,
        "topic_tag": sub.topic_tag,
        "stem": stem_typ,
        "passage": passage_typ,
        "conditions": conds_typ,
        "bogi": bogi_typ,
        "choices": choices_typ,
        "subjective_type": subj_type,
        "subjective_box_height": box_h_str,
        "subjective_label": subj_label,
        "figures_svg": figures_svg,
        "answer": ans_typ,
        "solution": sol_typ,
        "solution_figures_svg": solution_figures_svg,
        "solving_space": solving_space,
    }


_RANGE_NUM_RE = re.compile(r"^\[?\s*\d+\s*[~\-～∼]\s*\d+\s*번?\s*\]?$")
_RANGE_STEM_PREFIX_RE = re.compile(r"^(\[\s*\d+\s*[~\-～∼]\s*\d+\s*번?\s*\])\s*(.*)$", flags=re.DOTALL)


def _extract_standalone_group_header(p: ProblemItem) -> str | None:
    """
    Returns the group header text if ProblemItem `p` is a standalone group instruction item
    (e.g., `[4~8번] 빈칸에 들어갈 알맞은 문장을 고르시오.` with no choices, no sub_problems, and no answer).
    """
    if p.choices or p.sub_problems or (p.answer is not None and p.answer.strip() != ""):
        return None
    num_str = str(p.number).strip() if p.number is not None else ""
    stem_str = p.stem.strip()

    if num_str and _RANGE_NUM_RE.match(num_str):
        bracketed = num_str if num_str.startswith("[") else f"[{num_str}]"
        return f"{bracketed} {stem_str}".strip() if not stem_str.startswith("[") else stem_str

    if "\n" not in stem_str and _RANGE_STEM_PREFIX_RE.match(stem_str):
        return stem_str

    return None


def _build_problem_typst_data(p: ProblemItem, default_num: int) -> dict:
    num = p.number if p.number is not None else default_num
    raw_stem = p.stem.strip()
    group_header_raw = p.group_header.strip() if p.group_header else None

    # Check if this item is a standalone header-only item
    standalone_hdr = _extract_standalone_group_header(p)
    is_header_only = standalone_hdr is not None
    if is_header_only and not group_header_raw:
        group_header_raw = standalone_hdr

    # If group_header is not explicitly set, check if stem starts with "[4~8번] ...\n<actual stem>"
    if not group_header_raw and "\n" in raw_stem:
        first_line, rest = raw_stem.split("\n", 1)
        if _RANGE_STEM_PREFIX_RE.match(first_line.strip()) and rest.strip():
            group_header_raw = first_line.strip()
            raw_stem = rest.strip()

    # Strip redundant leading problem number from stem (e.g. "6번. 물음에 답하시오." when number is 6)
    num_digits_m = re.match(r"^(\d+)(?:번)?\.?$", str(num).strip())
    if num_digits_m and not is_header_only:
        d_str = num_digits_m.group(1)
        raw_stem = re.sub(rf"^{d_str}\s*(?:번\s*\.?|\.)\s+", "", raw_stem)

    stem_typ = "" if is_header_only else markdown_to_typst(raw_stem)
    group_header_typ = markdown_to_typst(group_header_raw) if group_header_raw else None
    group_passage_typ = markdown_to_typst(p.group_passage) if p.group_passage else None
    group_conds_typ = [markdown_to_typst(c) for c in p.group_conditions]
    group_bogi_typ = [markdown_to_typst(b) for b in p.group_bogi]
    group_figures_svg = _render_figures_list(p.group_figures)

    passage_typ = markdown_to_typst(p.passage) if p.passage else None
    conds_typ = [markdown_to_typst(c) for c in p.conditions]
    bogi_typ = [markdown_to_typst(b) for b in p.bogi]
    choices_typ = [markdown_to_typst(c) for c in p.choices]
    sol_typ = markdown_to_typst(p.solution) if p.solution else None

    figures_svg = _render_figures_list(p.figures)
    solution_figures_svg = _render_figures_list(p.solution_figures)

    sub_problems_data = [
        _build_sub_problem_typst_data(sub, s_idx) for s_idx, sub in enumerate(p.sub_problems)
    ]

    # Synthesize parent answer from sub_problems if parent answer is omitted
    if p.answer is not None and p.answer.strip() != "":
        ans_typ = markdown_to_typst(p.answer)
        quick_ans_typ = ans_typ
    elif sub_problems_data:
        sub_ans_pairs = [
            (s["label"], s["answer"]) for s in sub_problems_data if s.get("answer")
        ]
        ans_typ = " / ".join(f"{lbl} {ans}" for lbl, ans in sub_ans_pairs)
        quick_ans_typ = " \n".join(f"{lbl} {ans}" for lbl, ans in sub_ans_pairs)
    else:
        ans_typ = ""
        quick_ans_typ = ""

    solving_space = (
        "0.20cm"
        if is_header_only
        else (f"{p.solving_space_cm:.2f}cm" if p.solving_space_cm else "1.2cm")
    )

    subj_type, box_h_str, subj_label = _resolve_subjective_config(
        "none" if is_header_only else p.subjective_type,
        p.subjective_box_height,
        p.subjective_label,
        has_choices=bool(p.choices),
        has_sub_problems=bool(sub_problems_data),
    )

    return {
        "number": num,
        "is_header_only": is_header_only,
        "group_header": group_header_typ,
        "pad_group_header": group_header_typ,
        "group_passage": group_passage_typ,
        "pad_group_passage": group_passage_typ,
        "group_conditions": group_conds_typ,
        "group_bogi": group_bogi_typ,
        "group_figures_svg": group_figures_svg,
        "points": p.points,
        "topic_tag": p.topic_tag,
        "stem": stem_typ,
        "passage": passage_typ,
        "conditions": conds_typ,
        "bogi": bogi_typ,
        "choices": choices_typ,
        "sub_problems": sub_problems_data,
        "subjective_type": subj_type,
        "subjective_box_height": box_h_str,
        "subjective_label": subj_label,
        "figures_svg": figures_svg,
        "answer": ans_typ,
        "quick_answer": quick_ans_typ,
        "solution": sol_typ,
        "solution_figures_svg": solution_figures_svg,
        "solving_space": solving_space,
    }


def _prepare_problems_typst_data(problems: list[ProblemItem]) -> list[dict]:
    """
    Builds Typst problem dictionaries with smart auto-numbering, standalone group header merging,
    and consecutive group_header deduplication for continuous layouts.
    """
    # Step 1: Merge any standalone group header item into the immediately following problem if one exists
    merged_items: list[ProblemItem] = []
    pending_header_item: ProblemItem | None = None

    for p in problems:
        standalone_hdr = _extract_standalone_group_header(p)
        if standalone_hdr is not None:
            if pending_header_item is not None:
                merged_items.append(pending_header_item)
            pending_header_item = p
        else:
            if pending_header_item is not None:
                hdr_text = _extract_standalone_group_header(pending_header_item)
                p = p.model_copy(
                    update={
                        "group_header": p.group_header or hdr_text,
                        "group_passage": p.group_passage or pending_header_item.group_passage or pending_header_item.passage,
                        "group_conditions": p.group_conditions or pending_header_item.group_conditions or pending_header_item.conditions,
                        "group_bogi": p.group_bogi or pending_header_item.group_bogi or pending_header_item.bogi,
                        "group_figures": p.group_figures or pending_header_item.group_figures or pending_header_item.figures,
                    }
                )
                pending_header_item = None
            merged_items.append(p)

    if pending_header_item is not None:
        merged_items.append(pending_header_item)

    # Step 2: Build Typst dicts and track sequential problem numbering
    problems_data: list[dict] = []
    auto_num = 1
    last_group_header: str | None = None
    last_group_passage: str | None = None

    for p in merged_items:
        p_dict = _build_problem_typst_data(p, auto_num)
        if not p_dict["is_header_only"]:
            if isinstance(p.number, int):
                auto_num = p.number + 1
            elif isinstance(p.number, str):
                m_num = re.match(r"^(\d+)(?:번)?\.?$", p.number.strip())
                auto_num = (int(m_num.group(1)) + 1) if m_num else (auto_num + 1)
            else:
                auto_num += 1

        # Deduplicate identical consecutive group_header / group_passage for continuous layouts
        cur_hdr = p_dict["group_header"]
        if cur_hdr and cur_hdr == last_group_header:
            p_dict["group_header"] = None
        else:
            last_group_header = cur_hdr

        cur_psg = p_dict["group_passage"]
        if cur_psg and cur_psg == last_group_passage:
            p_dict["group_passage"] = None
        else:
            last_group_passage = cur_psg

        problems_data.append(p_dict)

    return problems_data


def generate_typst_document(request: ExamPDFRequest, for_solutions_only: bool = False) -> str:
    """
    Constructs the complete Typst source code by loading templates and formatting data.
    """
    problems_data = _prepare_problems_typst_data(request.problems)
    problems_json_str = json.dumps(problems_data, ensure_ascii=False)
    encoded_json = json.dumps(problems_json_str)

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
