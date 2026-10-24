import pytest
from create_pdf_mcp.models.exam import ExamPDFRequest, ProblemItem, SubProblemItem
from create_pdf_mcp.models.figures import FunctionPlotSpec, FunctionCurve, PlotPoint
from create_pdf_mcp.typst_engine.compiler import (
    generate_typst_document,
    compile_typst_to_pdf,
    get_pdf_page_count,
)


@pytest.fixture
def sample_exam_request() -> ExamPDFRequest:
    return ExamPDFRequest(
        title="2027학년도 대학수학능력시험 모의평가",
        subtitle="제 2 교시",
        subject_badge="수학 영역",
        footer_note="* 시험지의 저작권은 출제자에게 있습니다.",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        problems=[
            ProblemItem(
                number=1,
                points=3,
                topic_tag="함수의 극한",
                stem="함수 $f(x) = x^2 - 4x + 3$에 대하여 $\\lim_{x \\to 1} \\frac{f(x)}{x - 1}$의 값은?",
                choices=["$-2$", "$-1$", "$0$", "$1$", "$2$"],
                answer="①",
                solution="$\\lim_{x \\to 1} \\frac{(x-1)(x-3)}{x-1} = \\lim_{x \\to 1} (x-3) = -2$이다.",
            ),
            ProblemItem(
                number=2,
                points=4,
                topic_tag="미분법",
                stem="최고차항의 계수가 $1$인 삼차함수 $f(x)$가 다음 조건을 만족시킨다.",
                conditions=[
                    "(가) $f(0) = 0$",
                    "(나) 함수 $f(x)$는 $x=1$에서 극솟값 $-2$를 갖는다.",
                ],
                bogi=[
                    "ㄱ. $f'(0) = 0$",
                    "ㄴ. $f(2) = 0$",
                    "ㄷ. 닫힌구간 $[0, 2]$에서 방정식 $f(x)=0$의 서로 다른 실근의 개수는 $2$이다.",
                ],
                figures=[
                    FunctionPlotSpec(
                        x_range=(-1.0, 3.0),
                        y_range=(-3.0, 3.0),
                        functions=[
                            FunctionCurve(expr="x**3 - 3*x", label="y=f(x)"),
                        ],
                        points=[
                            PlotPoint(x=1.0, y=-2.0, label="극솟값(1, -2)", show_projection="both"),
                        ],
                    )
                ],
                choices=["ㄱ", "ㄱ, ㄴ", "ㄱ, ㄷ", "ㄴ, ㄷ", "ㄱ, ㄴ, ㄷ"],
                answer="⑤",
                solution="$f'(x) = 3x(x-1)$ 등의 조건을 분석하여 판별한다.",
            ),
        ],
    )


def test_generate_typst_document(sample_exam_request):
    src = generate_typst_document(sample_exam_request)
    assert "render_exam_2col" in src
    assert "2027학년도 대학수학능력시험 모의평가" in src
    assert "render_solutions" in src


def test_compile_exam_2col_to_pdf(sample_exam_request):
    sample_exam_request.layout_mode = "exam_2col"
    src = generate_typst_document(sample_exam_request)
    pdf_bytes = compile_typst_to_pdf(src)

    assert pdf_bytes.startswith(b"%PDF-")
    pages = get_pdf_page_count(pdf_bytes)
    assert pages >= 1


def test_compile_pad_1p1q_to_pdf(sample_exam_request):
    sample_exam_request.layout_mode = "pad_1p1q"
    sample_exam_request.pad_note_style = "grid"
    src = generate_typst_document(sample_exam_request)
    pdf_bytes = compile_typst_to_pdf(src)

    assert pdf_bytes.startswith(b"%PDF-")
    pages = get_pdf_page_count(pdf_bytes)
    assert pages >= 2  # 2 problems, so at least 2 pages


def test_compile_workbook_to_pdf(sample_exam_request):
    sample_exam_request.layout_mode = "workbook"
    src = generate_typst_document(sample_exam_request)
    pdf_bytes = compile_typst_to_pdf(src)

    assert pdf_bytes.startswith(b"%PDF-")
    pages = get_pdf_page_count(pdf_bytes)
    assert pages >= 1


def test_group_headers_blanks_and_sub_problems():
    """
    Tests:
    1) Group instruction headers like '[4~8번] 빈칸에 들어갈 알맞은 문장을 고르시오.' (both via group_header and standalone item)
    2) Blank expressions (_____, [빈칸], [빈칸: (가)], (      ), \\boxed)
    3) Sub-problems ('6번. 물음에 답하시오. (1) ~~~ (2) ~~~') both structured and inline
    across exam_2col, workbook, and pad_1p1q layouts.
    """
    req = ExamPDFRequest(
        title="빈칸 및 새끼문제 통합 모의평가",
        subtitle="제 1 교시",
        subject_badge="통합 영역",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        problems=[
            # Problem 4 with group_header and passage with blanks
            ProblemItem(
                number=4,
                group_header="[4~5번] 빈칸에 들어갈 알맞은 문장을 고르시오.",
                group_bogi=[
                    "ㄱ. 함수 $f(x)$는 $x=0$에서 연속이다.",
                    "ㄴ. $\\lim_{x \\to 0} f(x)$가 존재한다.",
                ],
                points=3,
                stem="다음 대화의 빈칸 _____ 에 들어갈 알맞은 문장을 고르시오.",
                passage="학생 A: 미분가능한 함수는 항상 연속일까?\n학생 B: 맞아, [빈칸: (가)] 이므로 항상 성립해.",
                choices=["ㄱ", "ㄴ", "ㄱ, ㄴ", "모두 아님", "알 수 없음"],
                answer="①",
                solution="미분가능하면 연속이다.",
            ),
            # Problem 5 with duplicate group_header (should be deduplicated in exam_2col/workbook)
            ProblemItem(
                number=5,
                group_header="[4~5번] 빈칸에 들어갈 알맞은 문장을 고르시오.",
                points=3,
                stem="다음 식의 빈칸 (          ) 및 $\\boxed{\\text{(나)}}$에 들어갈 알맞은 것은?",
                choices=["$0$", "$1$", "$2$", "$3$", "$4$"],
                answer="②",
                solution="항등식의 성질에 의해 $1$이다.",
            ),
            # Problem 6 with structured sub_problems (새끼문제)
            ProblemItem(
                number=6,
                points=6,
                topic_tag="미분법 - 서술 및 소문항",
                stem="6번. 물음에 답하시오.",
                conditions=[
                    "(가) 삼차함수 $f(x) = x^3 - 3x^2 + 2$",
                    "(나) 실수 전체의 집합에서 정의됨",
                ],
                sub_problems=[
                    SubProblemItem(
                        number="(1)",
                        points=3,
                        stem="(1) 도함수 $f'(x)$를 구하고 극값을 구하시오.",
                        subjective_type="short_answer",
                        answer="극댓값 $2$, 극솟값 $-2$",
                        solution="$f'(x) = 3x(x-2) = 0$에서 $x=0, 2$이다.",
                    ),
                    SubProblemItem(
                        number=2,
                        points=3,
                        stem="방정식 $f(x) = k$가 서로 다른 세 실근을 갖도록 하는 정수 $k$의 개수는?",
                        choices=["$1$", "$2$", "$3$", "$4$", "$5$"],
                        answer="③",
                        solution="$-2 < k < 2$인 정수는 $-1, 0, 1$로 3개이다.",
                    ),
                ],
            ),
            # Problem 7 with inline sub-questions in stem
            ProblemItem(
                number=7,
                points=4,
                stem="물음에 답하시오. (1) $\\sin 30^\\circ$의 값을 구하시오. (2) $\\cos 60^\\circ$의 값을 구하시오.",
                subjective_type="short_answer",
                answer="(1) $\\frac{1}{2}$ / (2) $\\frac{1}{2}$",
                solution="$\\sin 30^\\circ = \\cos 60^\\circ = \\frac{1}{2}$이다.",
            ),
            # Standalone group header item followed by Problem 8
            ProblemItem(
                stem="[8~9번] 빈칸에 들어갈 알맞은 식을 고르시오.",
            ),
            ProblemItem(
                number=8,
                points=3,
                stem="등차수열 $\\{a_n\\}$의 일반항은 $a_n = a_1 + \\underline{\\hspace{2cm}}$ 이다.",
                choices=["$(n-1)d$", "$nd$", "$(n+1)d$", "$n^2 d$", "$2nd$"],
                answer="①",
                solution="등차수열의 일반항 공식이다.",
            ),
        ],
    )

    for mode in ("exam_2col", "workbook", "pad_1p1q"):
        req.layout_mode = mode
        src = generate_typst_document(req)
        pdf_bytes = compile_typst_to_pdf(src)
        assert pdf_bytes.startswith(b"%PDF-")
        assert get_pdf_page_count(pdf_bytes) >= 1

    # Also test separate solutions compilation
    sol_src = generate_typst_document(req, for_solutions_only=True)
    sol_pdf = compile_typst_to_pdf(sol_src)
    assert sol_pdf.startswith(b"%PDF-")
