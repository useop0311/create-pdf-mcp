from pathlib import Path
from create_pdf_mcp.models.exam import ExamPDFRequest, PassageGroup, ProblemItem
from create_pdf_mcp.models.figures import (
    FunctionPlotSpec,
    FunctionCurve,
    PlotPoint,
    ShadedArea,
    GeometryPhysicsSpec,
    GeoPoint,
    GeoSegment,
    GeoAngle,
    PhysicsObject,
)
from create_pdf_mcp.typst_engine import generate_typst_document, compile_typst_to_pdf


output_dir = Path("output_samples")
output_dir.mkdir(exist_ok=True)

problems = [
    # 1. 객관식 문항: 미적분 3차함수 + 적분 영역 그래프
    ProblemItem(
        number=1,
        points=4,
        topic_tag="수학Ⅱ - 정적분의 활용",
        stem="함수 $f(x) = x^3 - 3x$의 그래프와 $x$축으로 둘러싸인 부분 중 $x \\ge 0$인 영역의 넓이를 $S$라 하자.",
        conditions=[
            "(가) $f(0) = 0$, $f(\\sqrt{3}) = 0$",
            "(나) $x = 1$에서 극솟값 $-2$를 갖는다.",
        ],
        bogi=[
            "ㄱ. $f'(1) = 0$",
            "ㄴ. $S = \\frac{9}{4}$",
            "ㄷ. 곡선 $y=f(x)$와 직선 $y=k$가 서로 다른 세 점에서 만날 때 $-2 < k < 2$이다.",
        ],
        figures=[
            FunctionPlotSpec(
                x_range=(-0.5, 2.5),
                y_range=(-3.0, 3.0),
                functions=[
                    FunctionCurve(expr="x**3 - 3*x", label="y=f(x)"),
                ],
                points=[
                    PlotPoint(x=1.0, y=-2.0, label="(1, -2)", show_projection="both"),
                ],
                shaded_areas=[
                    ShadedArea(expr1="x**3 - 3*x", expr2="0", x_range=(0.0, 1.732))
                ],
                caption="<그림 1> 함수 $y=f(x)$의 그래프",
            )
        ],
        choices=["ㄱ", "ㄱ, ㄴ", "ㄱ, ㄷ", "ㄴ, ㄷ", "ㄱ, ㄴ, ㄷ"],
        answer="⑤",
        solution="정적분 $\\int_0^{\\sqrt{3}} (0 - (x^3 - 3x)) dx = [-\\frac{x^4}{4} + \\frac{3x^2}{2}]_0^{\\sqrt{3}} = \\frac{9}{4}$이다.",
    ),
    # 2. 주관식 단답형 문항: 기하 직각삼각형 (choices 없음 -> auto 단답형 답란)
    ProblemItem(
        number=2,
        points=3,
        topic_tag="기하 - 삼각비",
        stem="그림과 같이 $\\angle A = 90^\\circ$이고 $\\overline{AB} = 4, \\overline{AC} = 3$인 직각삼각형 $ABC$에서 $10 \\cos \\theta$의 값을 구하시오.",
        figures=[
            GeometryPhysicsSpec(
                points=[
                    GeoPoint(id="A", x=0.0, y=0.0, label="A"),
                    GeoPoint(id="B", x=4.0, y=0.0, label="B"),
                    GeoPoint(id="C", x=0.0, y=3.0, label="C"),
                ],
                segments=[
                    GeoSegment(p1="A", p2="B", length_label="4"),
                    GeoSegment(p1="B", p2="C", length_label="5"),
                    GeoSegment(p1="C", p2="A", length_label="3"),
                ],
                angles=[
                    GeoAngle(vertex="A", p1="B", p2="C", is_right_angle=True),
                    GeoAngle(vertex="B", p1="A", p2="C", label="θ"),
                ],
                caption="<그림 2> 직각삼각형 $ABC$",
            )
        ],
        choices=[],  # 주관식 단답형
        subjective_type="short_answer",
        subjective_box_height="auto",
        answer="8",
        solution="$\\cos \\theta = \\frac{4}{5}$이므로 $10 \\cos \\theta = 10 \\times \\frac{4}{5} = 8$이다.",
    ),
    # 3. 주관식 서술형 문항: 물리 빗면 역학 (서술형 풀이 및 답안 박스)
    ProblemItem(
        number=3,
        points=6,
        topic_tag="물리학Ⅰ - 뉴턴 역학 (서술형)",
        stem="경사각이 $\\theta$인 마찰이 없는 빗면 위에 질량 $m$인 물체가 놓여 있다. 물체가 빗면을 따라 미끄러져 내려갈 때, 물체에 작용하는 힘을 분석하고 가속도의 크기 $a$를 구하는 풀이 과정과 정답을 서술하시오. (단, 중력가속도는 $g$이다.)",
        figures=[
            GeometryPhysicsSpec(
                points=[],
                segments=[],
                physics_objects=[
                    PhysicsObject(kind="incline", pos=(0.0, 0.0), end_pos=(5.0, 3.0)),
                    PhysicsObject(kind="block", pos=(2.5, 1.5), angle_deg=31.0, label="m"),
                    PhysicsObject(kind="vector_arrow", pos=(2.5, 1.5), end_pos=(2.5, 0.5), label="mg"),
                ],
                caption="<그림 3> 빗면 위의 물체",
            )
        ],
        choices=[],
        subjective_type="descriptive",
        subjective_box_height="medium",  # 5.0cm 풀이 박스
        subjective_label="풀이 과정 및 정답",
        answer="$a = g \\sin \\theta$",
        solution="1) 물체에 작용하는 중력 $mg$를 빗면 방향과 수직 방향으로 분해한다.\n2) 빗면 방향 알짜힘 $F = mg \\sin \\theta$이다.\n3) 뉴턴 제2법칙 $F = ma$에 의해 $ma = mg \\sin \\theta$, 즉 $a = g \\sin \\theta$이다.",
    ),
]


def main():
    layouts = [
        ("exam_2col", "sample_exam_2col.pdf"),
        ("pad_1p1q", "sample_pad_1p1q.pdf"),
        ("workbook", "sample_workbook.pdf"),
    ]

    for mode, fname in layouts:
        req = ExamPDFRequest(
            title="2027학년도 대학수학능력시험 실전 모의평가",
            subtitle="제 2 교시",
            subject_badge="수학 및 물리학",
            footer_text="대구일과학고등학교 (제작: 송우섭)",
            footer_note="* 본 문제지의 저작권은 출제자에게 있습니다.",
            layout_mode=mode,
            pad_note_style="blank",
            answer_sheet_mode="append",
            problems=problems,
        )
        src = generate_typst_document(req)
        pdf = compile_typst_to_pdf(src)
        out_path = output_dir / fname
        out_path.write_bytes(pdf)
        print(f"Generated {fname} ({len(pdf)} bytes, layout: {mode})")

    # 국어 영역 샘플 시험지 생성
    korean_req = ExamPDFRequest(
        title="2027학년도 대학수학능력시험 모의평가 문제지",
        subtitle="제 1 교시",
        subject_badge="국어 영역",
        footer_text="대구일과학고등학교 (제작: 송우섭)",
        footer_note="* 본 문제지의 저작권은 출제자에게 있습니다.",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        passage_groups=[
            PassageGroup(
                problem_numbers=[1, 2],
                header="[1~2] 다음 글을 읽고 물음에 답하시오.",
                passage=[
                    "**(가)** 조선 후기 실학자들은 성리학적 명분론의 한계를 극복하고 당대의 사회적 모순을 해결하기 위해 "
                    "㉠ <u>경세치용(經世致用)</u>과 이용후생(利用厚生)의 학문을 주창하였다. 이들은 공리공담에 치우친 당시의 학풍을 비판하며, "
                    "백성의 삶에 실질적인 도움이 되는 제도 개혁과 기술 수용을 강조하였다.",
                    "**(나)** 모든 인식은 경험에서 시작되지만, 경험 그 자체가 보편타당한 지식을 보장하는 것은 아니다. "
                    "칸트는 감성을 통해 받아들인 직관의 자료가 지성의 선험적 범주에 의해 종합될 때 비로소 객관적 인식이 성립한다고 보았다. "
                    "즉, [A] <u>‘내용 없는 사유는 공허하고, 개념 없는 직관은 맹목적이다’</u>라는 그의 명제는 경험론과 합리론의 대립을 "
                    "종합하려는 비판철학의 핵심을 잘 보여 준다.",
                ],
                source="박지원, 「북학의」 / 임마누엘 칸트, 「순수이성비판」",
                footnotes=["* 경세치용: 세상을 다스리고 실생활에 쓰임이 있게 함."],
            )
        ],
        problems=[
            ProblemItem(
                number=1,
                points=2,
                topic_tag="독서 - 내용 일치",
                stem="(가)와 (나)에 대한 이해로 가장 적절한 것은?",
                choices=[
                    "(가)의 실학자들은 성리학적 명분론을 강화하는 데 주력하였다.",
                    "(가)의 실학자들은 백성의 삶과 무관한 형이상학적 탐구를 지향하였다.",
                    "(나)의 칸트는 감성적 직관만으로도 보편적 지식이 성립한다고 보았다.",
                    "(나)의 칸트는 경험론과 합리론의 한계를 종합적으로 극복하고자 하였다.",
                    "(가)와 (나) 모두 전통적 권위를 절대적 진리의 기준으로 삼았다.",
                ],
                answer="④",
                solution="(나)에서 칸트는 감성의 직관과 지성의 범주가 결합해야 객관적 인식이 성립한다고 보았다.",
            ),
            ProblemItem(
                number=2,
                points=3,
                topic_tag="독서 - <보기> 적용",
                stem="[A]의 관점에서 <보기>의 ‘갑’에게 해 줄 수 있는 조언으로 가장 적절한 것은?",
                bogi=(
                    "갑은 수많은 역사적 사료와 통계 데이터만을 끝없이 수집하면 역사 발전의 보편 법칙이 저절로 드러날 것이라고 믿고, "
                    "이론적 개념이나 분석 틀을 세우는 일을 전혀 하지 않고 있다."
                ),
                choices=[
                    "감성적 직관의 자료를 수집하는 일을 즉시 중단해야 합니다.",
                    "개념적 분석 틀이 없는 단순한 자료 수집만으로는 체계적 인식에 도달할 수 없습니다.",
                    "경험적 자료 없이 순수한 사유만으로 역사 법칙을 연역해야 합니다.",
                    "선험적 범주를 버리고 개별 사료의 특수성에만 집중해야 합니다.",
                    "모든 이론적 개념은 경험적 관찰 이후에 자동으로 생성됨을 기억해야 합니다.",
                ],
                answer="②",
                solution="‘개념 없는 직관은 맹목적이다’라는 [A]의 명제에 따라 개념적 분석 틀의 필요성을 조언해야 한다.",
            ),
        ],
    )
    kor_pdf = compile_typst_to_pdf(generate_typst_document(korean_req))
    (output_dir / "sample_korean_exam_2col.pdf").write_bytes(kor_pdf)
    print(f"Generated sample_korean_exam_2col.pdf ({len(kor_pdf)} bytes)")

    # 영어 영역 샘플 시험지 생성
    english_req = ExamPDFRequest(
        title="2027학년도 대학수학능력시험 모의평가 문제지",
        subtitle="제 3 교시",
        subject_badge="영어 영역",
        footer_text="대구일과학고등학교 (제작: 송우섭)",
        footer_note="* 본 문제지의 저작권은 출제자에게 있습니다.",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        problems=[
            ProblemItem(
                number=31,
                points=2,
                topic_tag="영어 - 빈칸 추론",
                stem="다음 빈칸에 들어갈 말로 가장 적절한 것을 고르시오.",
                passage=(
                    "In modern behavioral economics, researchers have repeatedly found that consumers rarely make decisions "
                    "in a vacuum. When a store offers a basic subscription for $10 and a premium package for $25, adding a "
                    "decoy option priced at $24 can dramatically shift consumer preference toward the premium tier. "
                    "This phenomenon demonstrates that human judgment of value is fundamentally __________ rather than absolute."
                ),
                passage_footnotes=["* decoy: 미끼 상품  ** vacuum: 진공, 고립된 상태"],
                choices=["comparative", "innate", "permanent", "random", "independent"],
                answer="①",
                solution="주변 선택지($10, $24, $25)와의 비교를 통해 가치를 판단하므로 빈칸에는 comparative가 적절하다.",
            ),
            ProblemItem(
                number=38,
                points=3,
                topic_tag="영어 - 문장 삽입",
                stem="글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?",
                given_box=(
                    "However, when those same algorithms are trained exclusively on historical data, they risk "
                    "amplifying existing social biases under the guise of objectivity."
                ),
                given_box_title="주어진 문장",
                passage=(
                    "Automated decision-making systems are increasingly deployed in hiring, lending, and healthcare. "
                    "( ① ) Proponents argue that algorithmic evaluations eliminate human fatigue and emotional prejudice. "
                    "( ② ) In many routine tasks, statistical models do outperform individual human judges in consistency. "
                    "( ③ ) This occurs because past records often reflect institutional inequalities rather than pure merit. "
                    "( ④ ) Consequently, engineers must actively audit training datasets before deploying models at scale. "
                    "( ⑤ ) Without such oversight, automation merely codifies past unfairness into future policy."
                ),
                passage_footnotes=["* guise: 외관, 구실  ** codify: 체계화하다"],
                choices=["①", "②", "③", "④", "⑤"],
                answer="③",
                solution="( ③ ) 뒤의 'This occurs because past records...'가 주어진 문장의 원인을 설명하므로 ③이 적절하다.",
            ),
        ],
    )
    eng_pdf = compile_typst_to_pdf(generate_typst_document(english_req))
    (output_dir / "sample_english_exam_2col.pdf").write_bytes(eng_pdf)
    print(f"Generated sample_english_exam_2col.pdf ({len(eng_pdf)} bytes)")


if __name__ == "__main__":
    main()
