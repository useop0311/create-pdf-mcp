import asyncio
from pathlib import Path
from create_pdf_mcp.models.concept import (
    CalloutBox,
    ConceptExampleItem,
    ConceptPDFRequest,
    ConceptSection,
)
from create_pdf_mcp.models.figures import FunctionPlotSpec, FunctionCurve, PlotPoint
from create_pdf_mcp.typst_engine import compile_concept_pdf, get_pdf_page_count

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output_samples"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_math_physics_sample():
    req = ConceptPDFRequest(
        title="2027 수능 수학·물리 통합 실전 개념서",
        subtitle="I. 다항함수의 미분법과 역학적 에너지 보존",
        subject_badge="수학Ⅱ & 물리학Ⅰ",
        footer_text="대구일과학고등학교 (제작: 송우섭)",
        footer_note="* 본 개념서는 상업적 이용 및 무단 복제를 금합니다.",
        layout_mode="concept_book",
        color_theme="blue",
        font_style="sans",
        show_toc=True,
        sections=[
            ConceptSection(
                badge="CHAPTER 01",
                title="미분계수의 기하학적 의미와 접선의 방정식",
                subtitle="곡선 위의 점에서의 순간변화율과 기하학적 접선",
                learning_objectives=[
                    "미분계수 f'(a)를 접선의 기울기로 기하학적으로 해석할 수 있다.",
                    "접선의 방정식을 구하는 3가지 기본 유형을 구분할 수 있다.",
                ],
                markdown="""
### 1. 미분계수의 수학적 정의
함수 $y=f(x)$에 대하여 $x=a$에서의 미분계수 $f'(a)$는 평균변화율의 극한값으로 정의된다:
$$f'(a) = \\lim_{\\Delta x \\to 0} \\frac{f(a+\\Delta x) - f(a)}{\\Delta x} = \\lim_{x \\to a} \\frac{f(x) - f(a)}{x - a}$$

> [!개념] 미분계수의 기하학적 해석
> 함수 $y=f(x)$의 $x=a$에서의 미분계수 $f'(a)$는 곡선 위의 점 $P(a, f(a))$에서 그은 ==접선의 기울기==와 정확히 일치한다.

| 접선 유형 | 주어진 조건 | 풀이 핵심 전략 |
|:---|:---|:---|
| 유형 1: 곡선 위의 점 $(x_1, y_1)$ | 접점의 좌표 $(x_1, y_1)$ | 기울기 $m = f'(x_1)$를 구한 뒤 $y - y_1 = m(x - x_1)$ |
| 유형 2: 기울기 $m$이 주어진 경우 | 접선의 기울기 $m$ | 방정식 $f'(t) = m$을 풀어 접점의 좌표 $(t, f(t))$를 구함 |
| 유형 3: 곡선 밖의 점 $(x_0, y_0)$ | 곡선 밖의 점 | 접점을 $(t, f(t))$로 놓고 접선 식에 $(x_0, y_0)$ 대입 |

아래 포물선 $y=x^2$ 위의 점 $(1, 1)$에서의 접선 기울기는 $f'(1) = 2$이다:
{{fig:0}}

> [!공식] 접선의 방정식 기본 공식
> 곡선 $y=f(x)$ 위의 점 $(t, f(t))$에서의 접선의 방정식은 다음과 같다:
> $$y - f(t) = f'(t)(x - t)$$

> [!주의] 오개념 체크
> 함수 $f(x)$가 $x=a$에서 연속이라고 해서 항상 미분가능한 것은 아니다.
> 예컨대 절댓값 함수 $f(x) = |x|$는 $x=0$에서 연속이지만 첨점(뾰족점)이므로 미분계수가 존재하지 않는다.
""",
                figures=[
                    FunctionPlotSpec(
                        type="function_plot",
                        width_cm=7.5,
                        x_range=[-1.0, 3.0],
                        y_range=[-0.5, 5.0],
                        functions=[
                            FunctionCurve(expr="x**2", label="y=x^2", color="#1d4ed8"),
                            FunctionCurve(expr="2*x - 1", label="y=2x-1", style="dashed", color="#dc2626"),
                        ],
                        points=[PlotPoint(x=1.0, y=1.0, label="P(1, 1)", show_projection="both")],
                    )
                ],
                examples=[
                    ConceptExampleItem(
                        label="필수 예제 01",
                        points=4,
                        topic_tag="미분계수 - 접선의 방정식",
                        stem="곡선 $y = x^3 - 3x + 2$ 위의 점 $(2, 4)$에서의 접선의 방정식을 구하시오.",
                        answer="$y = 9x - 14$",
                        solution="도함수 $y' = 3x^2 - 3$에 $x=2$를 대입하면 기울기 $m = 3(4) - 3 = 9$이다. 따라서 구하는 접선의 방정식은 $y - 4 = 9(x - 2) \\iff y = 9x - 14$이다.",
                    )
                ],
            )
        ],
    )
    pdf = compile_concept_pdf(req)
    out_file = OUTPUT_DIR / "sample_concept_book_math_physics.pdf"
    out_file.write_bytes(pdf)
    print(f"Generated: {out_file} ({len(pdf)} bytes, {get_pdf_page_count(pdf)} pages)")


def generate_korean_english_sample():
    req = ConceptPDFRequest(
        title="수능 국어·영어 지문 분석 및 구문 개념노트",
        subtitle="인강 교재형 보조단 코넬식 개념정리",
        subject_badge="국어 & 영어",
        footer_text="대구일과학고등학교 (제작: 송우섭)",
        footer_note="* 본 교재는 수업용 부교재로 제작되었습니다.",
        layout_mode="sidebar_note",
        color_theme="emerald",
        font_style="sans",
        show_toc=True,
        sections=[
            ConceptSection(
                badge="THEME 01",
                title="국어 문법: 국어의 음운 변동 체계 완벽 정리",
                subtitle="교체·탈락·첨가·축약의 원리와 표준 발음법",
                sidebar_notes=[
                    "비음: ㄴ, ㅁ, ㅇ",
                    "유음: ㄹ",
                    "자음 체계: 조음 위치와 조음 방법의 2차원 표 암기 필수",
                    "구개음화: 'ㄷ, ㅌ'이 모음 'ㅣ'를 만나 'ㅈ, ㅊ'으로 교체",
                ],
                markdown="""
### 1. 음운 변동의 기본 유형과 원리
음운 변동은 한 음운이 인접한 음운이나 환경에 따라 다른 음운으로 바뀌거나 없어지는 현상으로, 크게 ==교체==, ==탈락==, ==첨가==, ==축약==으로 나뉜다.

| 변동 유형 | 음운 수 변화 | 주요 현상 | 대표 예시 단어 |
|:---|:---:|:---|:---|
| 교체 (Substitution) | $0$ (불변) | 음절의 끝소리 규칙, 비음화, 유음화, 구개음화, 된소리되기 | 빗[빋], 국물[궁물], 신라[실라] |
| 탈락 (Deletion) | $-1$ (감소) | 자음군 단순화, 'ㄹ' 탈락, 'ㅎ' 탈락, 'ㅡ' 탈락 | 닭[닥], 살-+-니[사니], 낳은[나은] |
| 첨가 (Addition) | $+1$ (증가) | 'ㄴ' 첨가, 반모음 첨가 | 맨입[맨닙], 피어[피여] |
| 축약 (Contraction) | $-1$ (감소) | 거센소리되기($\u3131+\u314e \to \u314b$), 모음 축약 | 축하[추카], 보-+-아[봐] |

> [!주의] 자음군 단순화 vs 된소리되기 혼동 주의
> '닭[닥]'은 두 자음 중 하나가 없어지므로 **탈락(자음군 단순화)**이지만, '국밥[국빱]'은 예사소리가 된소리로 바뀌는 **교체(된소리되기)**이다!

> [!지문분석] 독서 인문 철학 지문 독해 매뉴얼
> 1. 대립되는 두 철학자의 입장(예: 칸트 vs 흄)을 문단별로 이항대립 표로 정리한다.
> 2. `[A]` 구역이 나오면 반드시 해당 철학자의 전제 조건과 결론 논리를 확인한다.
""",
            ),
            ConceptSection(
                badge="THEME 02",
                title="영어 구문 독해: 도치(Inversion)와 특수 구문",
                subtitle="부정어 도치 및 장소 부사구 도치의 원리",
                sidebar_notes=[
                    "부정어구: Never, Seldom, Rarely, Hardly, Scarcely, Little",
                    "도치 어순: 부정어 + 조동사/be + 주어 + 동사원형",
                    "Only + 부사구/절이 문두에 올 때도 동일하게 도치 발생!",
                ],
                markdown="""
### 2. 부정어 도치(Negative Inversion)의 구조
강조를 위해 문두로 이동한 부정어 뒤에서는 ==조동사 의문문 어순==으로 도치가 일어난다.

> [!문법] 부정어 도치 기본 패턴
> $$ \\text{부정어} + \\begin{cases} \\text{be동사} + S \\\\ \\text{do/does/did} + S + V \\\\ \\text{조동사(can/will)} + S + V \\end{cases} $$

- **예문 1**: *Never have I seen such a brilliant lecture.*
- **예문 2**: *Seldom does he complain about his workload.*
""",
            ),
        ],
    )
    pdf = compile_concept_pdf(req)
    out_file = OUTPUT_DIR / "sample_sidebar_note_korean_english.pdf"
    out_file.write_bytes(pdf)
    print(f"Generated: {out_file} ({len(pdf)} bytes, {get_pdf_page_count(pdf)} pages)")


def generate_history_social_sample():
    req = ConceptPDFRequest(
        title="수능 한국사·사회탐구 단권화 압축 서머리 시트",
        subtitle="조선 후기 사회 변혁과 근현대사 핵심 총정리",
        subject_badge="한국사 & 사탐",
        footer_text="대구일과학고등학교 (제작: 송우섭)",
        footer_note="* 본 요약 시트는 시험 직전 파이널 리마인드용입니다.",
        layout_mode="summary_2col",
        color_theme="amber",
        font_style="sans",
        show_toc=False,
        markdown="""
# [테마 01] 조선 후기 농촌 경제와 농민층의 분화
조선 후기에는 ==이앙법(모내기법)==이 전국적으로 확산되면서 벼와 보리의 이모작이 가능해졌고, 노동력이 획기적으로 절감되었다.

| 구분 | 이앙법 보급 전 | 이앙법 보급 후 |
|:---|:---|:---|
| 노동력 투입 | 김매기에 많은 노동력 소요 | 제초 노동력 급감 ($1/4$ 수준) |
| 농업 생산력 | 가뭄 시 수확량 불안정 | 이모작 가능, 수확량 대폭 증가 |
| 사회적 결과 | 자영농 중심의 체제 유지 | ==광작==의 유행, 농민층의 양극화 분화 |

> [!팁] 광작(廣作)의 결과
> 한 사람이 넓은 면적을 경작할 수 있게 되어 일부 농민은 **경영형 부농**으로 성장하였으나, 다수의 농민은 토지를 잃고 **임노동자**로 전락하였다.

# [테마 02] 수취 체제의 개편 (대동법·영정법·균역법)
조선 후기 삼정(전정, 군정, 환곡)의 문란을 수습하기 위해 국가 제도가 개편되었다.

1. **영정법 (인조, 1635)**: 풍흉에 상관없이 토지 1결당 ==미곡 4두== 고정
2. **대동법 (광해군~숙종, 1608~1708)**:
   - 가호별 공물(특산물) 납부 대신 ==토지 결수당 쌀 12두== 납부
   - 왕실 물품 구매를 담당하는 ==공인(貢人)== 등장 $\to$ 상품 화폐 경제 발전
3. **균역법 (영조, 1750)**:
   - 군포 부담을 2필에서 ==1필==로 경감
   - 부족분 보충: 결작(결당 2두), 선무군관포, 어장세/염세

> [!주의] 공인의 의의
> 대동법으로 등장한 공인은 국가로부터 공가를 받아 대량 구매를 진행함으로써 장시의 전국적 연결과 화폐 유통(상평통보)에 결정적 기여를 하였다.
""",
    )
    pdf = compile_concept_pdf(req)
    out_file = OUTPUT_DIR / "sample_summary_2col_history_social.pdf"
    out_file.write_bytes(pdf)
    print(f"Generated: {out_file} ({len(pdf)} bytes, {get_pdf_page_count(pdf)} pages)")


if __name__ == "__main__":
    generate_math_physics_sample()
    generate_korean_english_sample()
    generate_history_social_sample()
