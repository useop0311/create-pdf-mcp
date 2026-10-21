import pytest
from create_pdf_mcp.models.exam import ExamPDFRequest, ProblemItem
from create_pdf_mcp.typst_engine import generate_typst_document, compile_typst_to_pdf, get_pdf_page_count


def test_subjective_short_and_descriptive_compilation():
    req = ExamPDFRequest(
        title="수학 서술형 및 단답형 평가",
        subtitle="1학기 지필평가",
        subject_badge="수학Ⅱ",
        footer_text="대구일과학고등학교",
        footer_note="* 본 문제지의 저작권은 출제자에게 있습니다.",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        problems=[
            # 1. 단답형 문항 (auto box)
            ProblemItem(
                number=1,
                points=3,
                topic_tag="함수의 극한",
                stem="함수 $f(x) = x^2 - 1$에 대하여 $\\lim_{x \\to 2} f(x)$의 값을 구하시오.",
                choices=[],  # empty -> short answer
                subjective_type="short_answer",
                subjective_box_height="auto",
                answer="3",
                solution="$\\lim_{x \\to 2} (x^2 - 1) = 4 - 1 = 3$",
            ),
            # 2. 서술형 문항 (medium box - 5cm)
            ProblemItem(
                number=2,
                points=7,
                topic_tag="미분법 - 접선의 방정식",
                stem="곡선 $y = x^3 - 3x$ 위의 점 $(1, -2)$에서의 접선의 방정식을 구하는 풀이 과정과 정답을 서술하시오.",
                choices=[],
                subjective_type="descriptive",
                subjective_box_height="medium",
                subjective_label="풀이 과정 및 정답",
                answer="$y = -2$",
                solution="$y' = 3x^2 - 3$이므로 $x=1$에서 기울기는 $0$이다. 따라서 접선의 방정식은 $y = -2$이다.",
            ),
            # 3. 서술형 문항 (custom box height - 6.0cm)
            ProblemItem(
                number=3,
                points=10,
                topic_tag="정적분의 활용",
                stem="두 곡선 $y = x^2$과 $y = 2 - x^2$으로 둘러싸인 도형의 넓이를 구하는 과정을 단계별로 서술하시오.",
                choices=[],
                subjective_type="descriptive",
                subjective_box_height=6.0,
                subjective_label="[단계 1: 교점 구하기] / [단계 2: 정적분 계산]",
                answer="$\\frac{8}{3}$",
                solution="교점은 $x = \\pm 1$이다. 넓이 $S = \\int_{-1}^1 (2 - 2x^2) dx = [2x - \\frac{2x^3}{3}]_{-1}^1 = \\frac{8}{3}$이다.",
            ),
        ],
    )

    src = generate_typst_document(req)
    assert "subjective_type" in src
    pdf_bytes = compile_typst_to_pdf(src)
    assert pdf_bytes.startswith(b"%PDF-")
    pages = get_pdf_page_count(pdf_bytes)
    assert pages >= 1
