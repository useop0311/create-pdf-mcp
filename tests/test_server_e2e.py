import pytest
from httpx import AsyncClient, ASGITransport
from create_pdf_mcp.server import create_exam_pdf, preview_figure, app
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


@pytest.fixture
def rich_exam_request() -> ExamPDFRequest:
    return ExamPDFRequest(
        title="2027학년도 대학수학능력시험 실전 모의평가",
        subtitle="제 2 교시",
        subject_badge="수학 및 물리학",
        footer_note="* 본 문제지의 저작권은 출제자에게 있습니다.",
        layout_mode="exam_2col",
        answer_sheet_mode="append",
        problems=[
            # 1. Math Calculus with Function Plot & Shaded Area
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
            # 2. Geometry Right-angle triangle
            ProblemItem(
                number=2,
                points=3,
                topic_tag="기하 - 삼각비",
                stem="그림과 같이 $\\angle A = 90^\\circ$이고 $\\overline{AB} = 4, \\overline{AC} = 3$인 직각삼각형 $ABC$에서 $\\cos \\theta$의 값은?",
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
                choices=["$\\frac{3}{5}$", "$\\frac{4}{5}$", "$1$", "$\\frac{5}{4}$", "$\\frac{5}{3}$"],
                answer="②",
                solution="$\\cos \\theta = \\frac{\\overline{AB}}{\\overline{BC}} = \\frac{4}{5}$이다.",
            ),
            # 3. Physics Inclined Plane Mechanics
            ProblemItem(
                number=3,
                points=4,
                topic_tag="물리학Ⅰ - 뉴턴 운동 법칙",
                stem="경사각이 $\\theta$인 마찰이 없는 빗면 위에 질량 $m$인 물체가 놓여 있다. 물체가 빗면을 따라 미끄러져 내려갈 때 가속도의 크기는? (단, 중력가속도는 $g$이다.)",
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
                choices=["$g$", "$g \\sin \\theta$", "$g \\cos \\theta$", "$g \\tan \\theta$", "$2g$"],
                answer="②",
                solution="빗면 방향으로 작용하는 알짜힘은 $F = mg \\sin \\theta$이므로 $a = g \\sin \\theta$이다.",
            ),
        ],
    )


@pytest.mark.asyncio
async def test_create_exam_pdf_end_to_end(rich_exam_request):
    resp = await create_exam_pdf(rich_exam_request)
    assert resp.pdf_url.endswith(".pdf")
    assert resp.qr_code_url.endswith(".png")
    assert resp.problem_count == 3
    assert resp.page_count >= 1
    assert "문제지 PDF 생성이 완료되었습니다" in resp.summary_markdown


@pytest.mark.asyncio
async def test_create_exam_pdf_with_displaystyle_integral():
    r"""Regression test: verifies create_exam_pdf does not raise TypstError on \displaystyle\int."""
    req = ExamPDFRequest(
        title="미적분 실전 모의고사",
        layout_mode="exam_2col",
        problems=[
            ProblemItem(
                number=1,
                points=4,
                stem=r"함수 $f(x)$에 대하여 $\displaystyle\int_0^1 f(x) dx = 3$일 때, $\displaystyle\int_0^1 (2f(x) + 1) dx$의 값을 구하시오.",
                choices=["$5$", "$6$", "$7$", "$8$", "$9$"],
                answer="③",
                solution=r"$\displaystyle\int_0^1 (2f(x) + 1) dx = 2\displaystyle\int_0^1 f(x) dx + \displaystyle\int_0^1 1 dx = 2(3) + 1 = 7$",
            )
        ]
    )
    resp = await create_exam_pdf(req)
    assert resp.pdf_url.endswith(".pdf")
    assert resp.problem_count == 1
    assert resp.page_count >= 1


@pytest.mark.asyncio
async def test_preview_figure_tool():
    spec = FunctionPlotSpec(
        x_range=(-2.0, 2.0),
        y_range=(-2.0, 2.0),
        functions=[FunctionCurve(expr="x**2", label="y=x^2")],
    )
    result = await preview_figure(spec)
    assert result["type"] == "function_plot"
    assert "<svg" in result["svg_code"]


@pytest.mark.asyncio
async def test_fastapi_endpoints(rich_exam_request):
    # 1. Create PDF
    resp = await create_exam_pdf(rich_exam_request)

    # 2. Test downloading via FastAPI
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Health
        h_res = await ac.get("/health")
        assert h_res.status_code == 200
        assert h_res.json()["status"] == "healthy"

        # File download
        pdf_filename = resp.pdf_url.split("/")[-1]
        f_res = await ac.get(f"/files/{pdf_filename}")
        assert f_res.status_code == 200
        assert f_res.headers["content-type"] == "application/pdf"
        assert f_res.content.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_mcp_streamable_http_and_sse_endpoints():
    """Verifies that MCP Streamable HTTP (/mcp) and SSE (/sse) work with custom domains (e.g. Cloudflare Tunnel)."""
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        # 1. MCP Streamable HTTP /mcp
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
        headers = {
            "Host": "pdf-mcp.0311.kr",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        res_mcp = client.post("/mcp", json=init_payload, headers=headers, follow_redirects=False)
        assert res_mcp.status_code == 200
        assert "text/event-stream" in res_mcp.headers.get("content-type", "")
        assert "CreatePDFMCP" in res_mcp.text or "capabilities" in res_mcp.text

        # 2. MCP Streamable HTTP /mcp/ (trailing slash)
        res_mcp_slash = client.post("/mcp/", json=init_payload, headers=headers, follow_redirects=False)
        assert res_mcp_slash.status_code == 200

        # 3. MCP SSE /sse
        with client.stream("GET", "/sse", headers={"Host": "pdf-mcp.0311.kr"}) as sse_stream:
            assert sse_stream.status_code == 200
            assert "text/event-stream" in sse_stream.headers.get("content-type", "")
            first_line = next(sse_stream.iter_lines())
            assert "event: endpoint" in first_line
