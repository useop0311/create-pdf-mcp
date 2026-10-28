import pytest
from create_pdf_mcp.models.concept import (
    CalloutBox,
    ConceptExampleItem,
    ConceptPDFRequest,
    ConceptSection,
)
from create_pdf_mcp.models.figures import FigureSpec, FunctionPlotSpec, FunctionCurve
from create_pdf_mcp.processors.concept_markdown import (
    concept_inline_to_typst,
    concept_markdown_to_typst,
    split_markdown_into_sections,
)
from create_pdf_mcp.server import create_concept_pdf
from create_pdf_mcp.typst_engine import (
    generate_concept_typst_document,
    compile_typst_to_pdf,
    get_pdf_page_count,
)


def test_concept_inline_formatting():
    # Test highlight, bold, italic, strike, underline, and latex math
    text = "이것은 ==핵심 개념==이고, **중요**하며, *강조*, ~~취소~~, <u>밑줄</u>, 그리고 $f(x) = x^2 + 1$ 이다."
    typ = concept_inline_to_typst(text, theme="blue")
    assert '#concept_highlight(theme: "blue")[핵심 개념]' in typ
    assert "*중요*" in typ
    assert "_강조_" in typ
    assert "#strike[취소]" in typ
    assert "#underline[밑줄]" in typ
    assert "$f(x) = x^2 + 1$" in typ


def test_pipe_table_and_callout_parsing():
    md = """
### 1. 주요 무역 형태 비교
| 구분 | 정기선 | 부정기선 |
|:---|:---:|---:|
| 운항 일정 | 정기적 고정 | 수요에 따라 변동 |
| 운임 | 안정적 | 시황에 따라 급변 |

> [!공식] 에너지-질량 등가 공식
> 모든 질량 $m$은 에너지 $E$와 동등하다.
> $$E = m c^2$$

> [!주의] 오개념 체크
> 정기선과 부정기선의 차이를 혼동하지 말 것.

> [!보조단] 시험 직전 필수 암기 키워드
"""
    typ, sidebar = concept_markdown_to_typst(md, theme="emerald")
    assert "#concept_subheading(level: 3" in typ
    assert "#concept_table(" in typ
    assert "정기선" in typ
    assert 'kind: "formula"' in typ
    assert "에너지-질량 등가 공식" in typ
    assert 'kind: "warning"' in typ
    assert len(sidebar) == 1
    assert "시험 직전 필수 암기 키워드" in sidebar[0]


def test_split_markdown_into_sections():
    raw_md = """
# [개념 01] 함수의 극한과 연속
함수 $f(x)$에 대하여 $x \\to a$일 때...

## [개념 02] 미분계수와 도함수
미분계수는 평균변화율의 극한값이다.
"""
    sections = split_markdown_into_sections(raw_md)
    assert len(sections) == 2
    assert sections[0]["badge"] == "개념 01"
    assert sections[0]["title"] == "함수의 극한과 연속"
    assert "함수 $f(x)$" in sections[0]["markdown"]

    assert sections[1]["badge"] == "개념 02"
    assert sections[1]["title"] == "미분계수와 도함수"


@pytest.mark.asyncio
async def test_compile_concept_book_1col():
    req = ConceptPDFRequest(
        title="2027 수능 수학Ⅱ 실전 개념완성",
        subtitle="I. 다항함수의 미분법",
        subject_badge="수학Ⅱ",
        layout_mode="concept_book",
        color_theme="blue",
        font_style="sans",
        show_toc=True,
        sections=[
            ConceptSection(
                badge="CHAPTER 01",
                title="미분계수의 기하학적 의미와 접선의 방정식",
                subtitle="곡선 위의 점에서의 순간변화율과 접선의 기울기",
                learning_objectives=[
                    "미분계수를 기하학적으로 해석할 수 있다.",
                    "접선의 방정식을 구하는 3가지 유형을 구분할 수 있다.",
                ],
                markdown="""
### 1. 미분계수의 정의
함수 $y=f(x)$의 $x=a$에서의 미분계수 $f'(a)$는 다음과 같다:
$$f'(a) = \\lim_{\\Delta x \\to 0} \\frac{f(a+\\Delta x) - f(a)}{\\Delta x}$$

> [!개념] 기하학적 의미
> $f'(a)$는 곡선 $y=f(x)$ 위의 점 $(a, f(a))$에서의 **접선의 기울기**를 뜻한다.

아래 그래프에서 점 $P$에서의 접선 기울기가 바로 미분계수이다:
{{fig:0}}
""",
                figures=[
                    FunctionPlotSpec(
                        type="function_plot",
                        width_cm=8.0,
                        x_range=[-1.0, 3.0],
                        y_range=[-1.0, 5.0],
                        functions=[FunctionCurve(expr="x**2", label="y=x^2")],
                    )
                ],
                examples=[
                    ConceptExampleItem(
                        label="개념 확인 01",
                        stem="곡선 $y=x^2$ 위의 점 $(1, 1)$에서의 접선의 기울기를 구하시오.",
                        choices=["$1$", "$2$", "$3$", "$4$", "$5$"],
                        answer="②",
                        solution="$y'=2x$이므로 $x=1$을 대입하면 기울기는 $2$이다.",
                    )
                ],
            )
        ],
    )

    typ_src = generate_concept_typst_document(req)
    assert "render_concept_book" in typ_src
    pdf_bytes = compile_typst_to_pdf(typ_src)
    assert pdf_bytes.startswith(b"%PDF-")
    page_count = get_pdf_page_count(pdf_bytes)
    assert page_count >= 1


@pytest.mark.asyncio
async def test_compile_sidebar_note_and_summary_2col():
    # 1. sidebar_note layout with emerald theme
    req_sidebar = ConceptPDFRequest(
        title="수능 국어 문법/독서 핵심 정리",
        subtitle="음운 변동과 담화 구조",
        subject_badge="국어",
        layout_mode="sidebar_note",
        color_theme="emerald",
        font_style="sans",
        markdown="""
# [개념 01] 음운 변동의 4대 유형
음운 변동은 크게 ==교체==, ==탈락==, ==첨가==, ==축약==의 네 가지로 구분된다.

| 변동 유형 | 예시 단어 | 발음 | 비고 |
|:---|:---:|:---:|:---|
| 교체 (음절의 끝소리) | 빗 | [빋] | 대표음 실현 |
| 비음화 | 국물 | [궁물] | 조음 방법 동화 |
| 유음화 | 신라 | [실라] | 유음 [ㄹ] 동화 |

> [!보조단] 비음: ㄴ, ㅁ, ㅇ
> [!보조단] 유음: ㄹ

> [!주의] 예외 주의사항
> 된소리되기는 교체에 해당하며, 자음군 단순화는 탈락에 해당함을 헷갈리지 말 것!
""",
    )
    typ_sidebar = generate_concept_typst_document(req_sidebar)
    assert "render_sidebar_note" in typ_sidebar
    pdf_sidebar = compile_typst_to_pdf(typ_sidebar)
    assert pdf_sidebar.startswith(b"%PDF-")

    # 2. summary_2col layout with amber theme
    req_summary = ConceptPDFRequest(
        title="한국사 조선 후기 사회 변혁 핵심 요약",
        subtitle="단권화 서머리 시트",
        subject_badge="한국사",
        layout_mode="summary_2col",
        color_theme="amber",
        font_style="sans",
        markdown="""
# 1. 조선 후기 농촌 사회의 변화
- 모내기법(이앙법)의 전국적 확산
- 광작 현상으로 인한 농민층의 분화 (경영형 부농 vs 임노동자)

# 2. 대동법과 상품 화폐 경제
- 방납의 폐단을 시정하기 위해 특산물 대신 쌀/동전/포 납부
- 공인의 활동으로 장시와 포구 발달
""",
    )
    typ_summary = generate_concept_typst_document(req_summary)
    assert "render_summary_2col" in typ_summary
    pdf_summary = compile_typst_to_pdf(typ_summary)
    assert pdf_summary.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_create_concept_pdf_server_tool():
    req = ConceptPDFRequest(
        title="물리학Ⅰ 역학적 에너지 보존",
        subtitle="개념과 필수 예제",
        subject_badge="물리학Ⅰ",
        layout_mode="concept_book",
        color_theme="purple",
        font_style="sans",
        sections=[
            ConceptSection(
                title="역학적 에너지 보존 법칙",
                markdown="""
마찰이나 공기 저항이 없을 때 물체의 운동 에너지 $E_k$와 퍼텐셜 에너지 $E_p$의 합은 항상 일정하다:
$$E = E_k + E_p = \\frac{1}{2}m v^2 + m g h = \\text{const}$$
""",
            )
        ],
    )
    resp = await create_concept_pdf(req)
    assert resp.pdf_url.endswith(".pdf")
    assert resp.qr_code_url.endswith(".png")
    assert resp.page_count >= 1
    assert "📘 개념서 PDF 생성이 완료되었습니다!" in resp.summary_markdown


@pytest.mark.asyncio
async def test_smart_page_fit_and_section_per_page():
    # 1. Verify section_per_page forces each section onto its own page
    req_per_page = ConceptPDFRequest(
        title="단원별 페이지 분리 테스트",
        layout_mode="sidebar_note",
        color_theme="emerald",
        page_fit_mode="section_per_page",
        sections=[
            ConceptSection(badge="THEME 01", title="첫 번째 단원", markdown="첫 번째 단원 본문입니다."),
            ConceptSection(badge="THEME 02", title="두 번째 단원", markdown="두 번째 단원 본문입니다."),
        ],
    )
    resp_per_page = await create_concept_pdf(req_per_page)
    assert resp_per_page.page_count == 2

    # 2. Verify smart page-fitting compacts slight 2-page overflow into 1 clean page
    req_smart = ConceptPDFRequest(
        title="스마트 1페이지 피팅 테스트",
        subtitle="미세 넘침 자동 압축",
        subject_badge="국어 & 영어",
        layout_mode="sidebar_note",
        color_theme="emerald",
        page_fit_mode="smart",
        show_toc=True,
        sections=[
            ConceptSection(
                badge="THEME 01",
                title="음운 변동의 4대 유형",
                sidebar_notes=["비음: ㄴ, ㅁ, ㅇ", "유음: ㄹ"],
                markdown="""
### 1. 음운 변동의 기본 원리
음운 변동은 크게 ==교체==, ==탈락==, ==첨가==, ==축약==으로 나뉜다.

| 변동 유형 | 음운 수 변화 | 대표 예시 |
|:---|:---:|:---|
| 교체 | $0$ | 국물[궁물], 신라[실라] |
| 탈락 | $-1$ | 닭[닥], 낳은[나은] |
| 첨가 | $+1$ | 맨입[맨닙] |
| 축약 | $-1$ | 축하[추카] ($ㄱ+ㅎ \to ㅋ$) |

> [!주의] 혼동 주의
> 자음군 단순화는 탈락이고, 된소리되기는 교체이다.
""",
            ),
            ConceptSection(
                badge="THEME 02",
                title="영어 부정어 도치 구문",
                sidebar_notes=["Never, Seldom, Rarely, Hardly, Little"],
                markdown="""
### 2. 부정어 도치의 어순
부정어가 문두에 위치하면 ==조동사 의문문 어순==으로 도치된다.

> [!문법] 부정어 도치 공식
> $$ \\text{부정어} + \\text{조동사/be} + S + V $$
""",
            ),
        ],
    )
    resp_smart = await create_concept_pdf(req_smart)
    assert resp_smart.page_count == 1
