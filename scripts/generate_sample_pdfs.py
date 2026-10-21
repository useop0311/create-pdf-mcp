import asyncio
from pathlib import Path
from create_pdf_mcp.models.exam import ExamPDFRequest, ProblemItem
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


if __name__ == "__main__":
    main()
