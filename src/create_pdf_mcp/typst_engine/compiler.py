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

from ..models.exam import ExamPDFRequest, PassageGroup, ProblemItem, SubProblemItem
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
        if isinstance(p.number, int):
            num_to_idx[p.number] = idx
        elif isinstance(p.number, str):
            m = re.match(r"^(\d+)", p.number.strip())
            if m:
                num_to_idx[int(m.group(1))] = idx
        else:
            num_to_idx[idx + 1] = idx

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
            target_nums = [problems[0].number if isinstance(problems[0].number, int) else 1]

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
            first_num = problems[i].number if isinstance(problems[i].number, int) else (i + 1)
            last_num = problems[j - 1].number if isinstance(problems[j - 1].number, int) else j
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
    conds_typ = [markdown_to_typst(c) for c in sub.conditions]
    bogi_typ = [markdown_to_typst(b) for b in sub.bogi]
    bogi_title_typ = markdown_to_typst(sub.bogi_title) if getattr(sub, "bogi_title", None) else None
    choices_typ = [markdown_to_typst(c) for c in sub.choices]
    ans_typ = markdown_to_typst(sub.answer) if sub.answer else ""
    sol_typ = markdown_to_typst(sub.solution) if sub.solution else None

    # Sub-problem passage or given_box if any
    inline_passage = None
    if sub.passage:
        inline_passage = _build_passage_dict(
            raw_passage=sub.passage,
            header=None,
            title=getattr(sub, "passage_title", None),
            source=getattr(sub, "passage_source", None),
            footnotes=getattr(sub, "passage_footnotes", None),
        )
    given_box_data = None
    raw_given_str = _join_text_or_list(getattr(sub, "given_box", None))
    if raw_given_str:
        given_box_data = {
            "title": markdown_to_typst(sub.given_box_title) if getattr(sub, "given_box_title", None) else None,
            "content": markdown_to_typst(raw_given_str),
        }

    passage_typ = markdown_to_typst(sub.passage) if (sub.passage and not inline_passage) else None

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
        "given_box": given_box_data,
        "inline_passage": inline_passage,
        "passage": passage_typ,
        "conditions": conds_typ,
        "bogi": bogi_typ,
        "bogi_title": bogi_title_typ,
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


def _build_problem_typst_data(
    p: ProblemItem,
    default_num: int = 1,
    layout_mode: str = "exam_2col",
    pre_passage: dict | None = None,
    pad_pre_passage: dict | None = None,
    has_passage_context: bool = False,
    passage_consumed: bool = False,
    idx: int | None = None,
) -> dict:
    if idx is not None and default_num == 1 and p.number is None:
        num = idx + 1
    else:
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

    conds_typ = [markdown_to_typst(c) for c in p.conditions]
    bogi_typ = [markdown_to_typst(b) for b in p.bogi]
    bogi_title_typ = markdown_to_typst(p.bogi_title) if p.bogi_title else None
    choices_typ = [
        markdown_to_typst(re.sub(r"^[①②③④⑤]\s*", "", c.strip()))
        for c in p.choices
    ]
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

    passage_typ = markdown_to_typst(p.passage) if (p.passage and not passage_consumed and not inline_passage) else None

    # Build given_box (주어진 글 / 문장 삽입 / 제시문)
    given_box_data = None
    raw_given_str = _join_text_or_list(p.given_box)
    if raw_given_str:
        given_box_data = {
            "title": markdown_to_typst(p.given_box_title) if p.given_box_title else None,
            "content": markdown_to_typst(raw_given_str),
        }
        has_passage_context = True

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

    # Determine bottom solving space
    if p.solving_space_cm is not None:
        solving_space = f"{p.solving_space_cm:.2f}cm"
    elif is_header_only:
        solving_space = "0.20cm"
    elif has_passage_context:
        solving_space = "0.45cm" if layout_mode == "exam_2col" else "0.65cm"
    else:
        solving_space = "1.20cm" if layout_mode == "exam_2col" else "2.00cm"

    # Determine breakability
    total_inline_chars = (
        len(p.stem)
        + len(raw_inline_passage_str)
        + len(raw_given_str)
        + sum(len(b) for b in p.bogi)
        + sum(len(c) for c in p.choices)
    )
    is_breakable = len(raw_inline_passage_str) > 500 or total_inline_chars > 700

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
        "pre_passage": pre_passage,
        "pad_pre_passage": pad_pre_passage,
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
        "given_box": given_box_data,
        "inline_passage": inline_passage,
        "passage": passage_typ,
        "conditions": conds_typ,
        "bogi": bogi_typ,
        "bogi_title": bogi_title_typ,
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
        "is_breakable": is_breakable,
    }


def _prepare_problems_typst_data(request_or_problems: ExamPDFRequest | list[ProblemItem]) -> list[dict]:
    """
    Builds Typst problem dictionaries with smart auto-numbering, standalone group header merging,
    passage assignment resolution, and consecutive group_header deduplication for continuous layouts.
    """
    if isinstance(request_or_problems, ExamPDFRequest):
        request = request_or_problems
    else:
        request = ExamPDFRequest(problems=request_or_problems)

    problems = request.problems

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

    # Step 2: Resolve passage assignments on merged items
    req_with_merged = request.model_copy(update={"problems": merged_items})
    (
        pre_passages_by_idx,
        pad_passages_by_idx,
        has_passage_context_indices,
        consumed_indices,
    ) = _resolve_passage_assignments(req_with_merged)

    # Step 3: Build Typst dicts and track sequential problem numbering
    problems_data: list[dict] = []
    auto_num = 1
    last_group_header: str | None = None
    last_group_passage: str | None = None

    for i, p in enumerate(merged_items):
        p_dict = _build_problem_typst_data(
            p=p,
            default_num=auto_num,
            layout_mode=request.layout_mode,
            pre_passage=pre_passages_by_idx.get(i),
            pad_pre_passage=pad_passages_by_idx.get(i),
            has_passage_context=(i in has_passage_context_indices),
            passage_consumed=(i in consumed_indices),
        )
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
    problems_data = _prepare_problems_typst_data(request)
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
