import pytest
from create_pdf_mcp.models.exam import ExamPDFRequest, ProblemItem
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
