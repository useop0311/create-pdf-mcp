import io
import json
import logging
import os
import tempfile
from pathlib import Path
from pypdf import PdfReader
import typst

logger = logging.getLogger(__name__)

from ..models.exam import ExamPDFRequest, ProblemItem
from ..processors.math_text import markdown_to_typst
from ..processors.figure_renderer import render_figure_to_svg


TEMPLATES_DIR = Path(__file__).parent / "templates"


def _escape_typst_string(s: str) -> str:
    """Escapes string literal for Typst code."""
    if not s:
        return '""'
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _build_problem_typst_data(p: ProblemItem, idx: int) -> dict:
    num = p.number or (idx + 1)
    stem_typ = markdown_to_typst(p.stem)
    conds_typ = [markdown_to_typst(c) for c in p.conditions]
    bogi_typ = [markdown_to_typst(b) for b in p.bogi]
    choices_typ = [markdown_to_typst(c) for c in p.choices]
    ans_typ = markdown_to_typst(p.answer)
    sol_typ = markdown_to_typst(p.solution) if p.solution else None

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

    solving_space = f"{p.solving_space_cm:.2f}cm" if p.solving_space_cm else "1.2cm"

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
        "conditions": conds_typ,
        "bogi": bogi_typ,
        "choices": choices_typ,
        "subjective_type": subj_type,
        "subjective_box_height": f"{box_h:.2f}cm",
        "subjective_label": subj_label,
        "figures_svg": figures_svg,
        "answer": ans_typ,
        "solution": sol_typ,
        "solution_figures_svg": solution_figures_svg,
        "solving_space": solving_space,
    }


def generate_typst_document(request: ExamPDFRequest, for_solutions_only: bool = False) -> str:
    """
    Constructs the complete Typst source code by loading templates and formatting data.
    """
    problems_data = [_build_problem_typst_data(p, i) for i, p in enumerate(request.problems)]
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
