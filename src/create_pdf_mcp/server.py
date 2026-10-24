import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .config import settings
from .models.exam import ExamPDFRequest, ExamPDFResponse
from .models.figures import FigureSpec
from .processors.figure_renderer import render_figure_to_svg
from .storage import get_storage_backend, generate_qr_code_png, LocalStorage
from .typst_engine import generate_typst_document, compile_typst_to_pdf, get_pdf_page_count
from .typst_engine.compiler import _extract_standalone_group_header


# Initialize MCPServer (MCP 2.x standard)
mcp = MCPServer(
    name="CreatePDFMCP",
    instructions=(
        "CreatePDFMCP is a specialized MCP server for generating high-quality Korean CSAT/mock-exam/worksheet PDFs "
        "across all subjects — including Korean (국어 영역: 독서/문학/화작/언매), English (영어 영역: 단독 독해/빈칸 추론/순서/문장 삽입/장문 독해), "
        "Math (수학 영역), and Physics/Science (물리/과학 탐구) "
        "in 3 layouts (수능 2단 칼럼 exam_2col, 패드 1페이지 1문항 pad_1p1q, 1단 워크북 workbook). "
        "Supports single-problem passages (`passage`), multi-problem shared passage groups (`passage_groups` or `passage_range`), "
        "grouped question instruction banners (e.g. group_header='[4~8번] 빈칸에 들어갈 알맞은 문장을 고르시오.'), "
        "multi-part sub-questions (sub_problems: (1), (2), ... under a parent question like '6. 물음에 답하시오.'), "
        "fill-in-the-blank expressions (____, [빈칸], [빈칸: (가)], (      ), $\\boxed{...}$), "
        "given-sentence/ordering boxes (`given_box`), footnotes (`passage_footnotes`), source citations (`passage_source`), "
        "underlines (`<u>...</u>`), LaTeX math (`$...$`), conditions (가/나), <보기> (ㄱ/ㄴ/ㄷ 또는 문단), "
        "and 3-tier vector figures."
    ),
)


@mcp.tool(
    name="create_exam_pdf",
    description=(
        "Generate a Korean, English, Math, or Science/Physics exam/worksheet PDF "
        "(supporting reading passages, shared passage sets [1~3], multi-part sub-questions (1)/(2), blank lines, given-sentence boxes, math formulas, and vector figures) "
        "and return accessible download URL and QR code."
    )
)
async def create_exam_pdf(request: ExamPDFRequest) -> ExamPDFResponse:
    """
    Main tool for generating exam PDFs.
    """
    file_id = uuid.uuid4().hex[:12]
    storage = get_storage_backend()

    # 1. Generate and compile the main exam Typst document
    typst_src = generate_typst_document(request)
    pdf_bytes = compile_typst_to_pdf(typst_src)
    page_count = get_pdf_page_count(pdf_bytes)

    # 2. Save Exam PDF
    safe_title = "".join(c for c in request.title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    exam_filename = f"{safe_title or 'exam'}.pdf"
    pdf_url = await storage.save_pdf(file_id, pdf_bytes, exam_filename)

    # 3. Generate QR Code pointing to the PDF URL
    qr_png_bytes = generate_qr_code_png(pdf_url)
    qr_code_url = await storage.save_image(file_id, qr_png_bytes, "qr.png", "image/png")

    # 4. Handle Separate Solution PDF if requested
    sol_url = None
    if request.answer_sheet_mode == "separate":
        sol_typst_src = generate_typst_document(request, for_solutions_only=True)
        sol_pdf_bytes = compile_typst_to_pdf(sol_typst_src)
        sol_url = await storage.save_pdf(file_id, sol_pdf_bytes, f"{safe_title or 'exam'}_solutions.pdf")

    graded_count = sum(1 for p in request.problems if _extract_standalone_group_header(p) is None) or len(request.problems)

    summary = (
        f"### 📄 문제지 PDF 생성이 완료되었습니다!\n"
        f"- **제목**: {request.title} ({request.subtitle or ''})\n"
        f"- **레이아웃**: `{request.layout_mode}` ({page_count} 페이지, 총 {graded_count}문항)\n"
        f"- **문제지 다운로드**: [PDF 다운로드]({pdf_url})\n"
    )
    if sol_url:
        summary += f"- **해설지 다운로드**: [별도 해설지 PDF]({sol_url})\n"
    summary += f"- **패드 스캔용 QR 코드**: ![QR Code]({qr_code_url})\n"

    return ExamPDFResponse(
        pdf_url=pdf_url,
        qr_code_url=qr_code_url,
        solution_pdf_url=sol_url,
        page_count=page_count,
        problem_count=graded_count,
        layout_mode=request.layout_mode,
        summary_markdown=summary,
    )


@mcp.tool(
    name="preview_figure",
    description="Preview and validate a function plot, geometry diagram, or physics diagram before including it in an exam."
)
async def preview_figure(figure: FigureSpec) -> dict:
    """
    Validates and renders a figure to SVG string for previewing.
    """
    svg_code = render_figure_to_svg(figure)
    return {
        "type": figure.type,
        "width_cm": figure.width_cm,
        "caption": figure.caption,
        "svg_code": svg_code,
    }


@mcp.resource("schema://exam_guide", name="exam_guide")
def get_exam_schema_guide() -> str:
    """Returns guide and examples for authoring Korean, English, Math, and Science exam questions."""
    return """
# Korean, English, Math & Physics Exam Authoring Guide

## 1. Reading Passages (국어·영어 지문 및 세트 문항)
- **Single-Problem Passage (영어 독해 18~40번, 국어 단독 지문)**:
  - Set `passage` on `ProblemItem` (string or list of paragraph strings).
  - By default (`passage_position="auto"`), it renders inside a bordered box right below the question `stem`.
  - Optional: `passage_title` (title inside box), `passage_source` (e.g. `"박지원, 「호질」"`), `passage_footnotes` (e.g. `["* resilient: 회복력 있는", "** paradigm: 패러다임"]`).
- **Shared / Grouped Passage (국어 `[1~4]` 독서·문학 세트, 영어 `[41~42]` 장문 독해)**:
  - **Method A (`passage_groups` on `ExamPDFRequest`)**:
    Add a `PassageGroup` with `problem_numbers=[1, 2, 3]` (or `start_number=1, end_number=3`), `header="[1~3] 다음 글을 읽고 물음에 답하시오."`, `passage="..."`, `source="..."`, `footnotes=[...]`.
  - **Method B (`passage_range` on the first `ProblemItem`)**:
    Set `passage="..."` and `passage_range="1~3"` (or `passage_range="[41~42] 다음 글을 읽고, 물음에 답하시오."`) on the first problem of the set.
  - **Method C (`group_header` on `ProblemItem`)**:
    Set `group_header="[4~8번] 빈칸에 들어갈 알맞은 문장을 고르시오."` on the problem item(s).
- **Given Sentence / Ordering Intro Box (영어 문장 삽입·글의 순서, 국어 제시문)**:
  - Set `given_box` (and optional `given_box_title`, e.g. `"주어진 문장"` or `"주어진 글"`) on `ProblemItem`. It renders in a distinct box above the main `passage`.
- **Underlines & Blanks (밑줄 및 빈칸 추론)**:
  - Wrap underlined words/sentences with `<u>...</u>` or `__...__` (e.g. `㉠ <u>그의 사상</u>`, `(a) <u>wake-up call</u>`).
  - Write 2 or more underscores `____` for blank-filling questions (빈칸 추론); it automatically renders as a crisp horizontal blank line.
  - Boxed blanks: `[빈칸]`, `[빈칸: (가)]`, or in math `$\\boxed{\\text{(가)}}$`, `$\\boxed{\\quad}$`.
  - Wide parentheses/brackets: `(        )` or `[        ]` or `(   가   )`.

## 2. Multi-Part Sub-Questions (`6. 물음에 답하시오. (1) ... (2) ...`)
- **Structured Sub-Questions (`sub_problems`)**:
  - Use `sub_problems` inside `ProblemItem` for multi-part questions (새끼문제):
    - Parent `stem`: `"다음 물음에 답하시오."`
    - `sub_problems`: list of `SubProblemItem` with `number` (`"(1)"`, `"(2)"`), `stem`, `points`, `choices` (or `subjective_type`), `answer`, and `solution`.
- **Inline Sub-Questions**:
  - Inline sub-questions in `stem` (e.g. `"물음에 답하시오. (1) ... (2) ..."`) are also automatically formatted onto separate lines.

## 3. Math Formula Syntax
- Use standard LaTeX math: `$f(x) = x^3 - 3x + 1$`, `$\\int_0^1 f(x)dx$`, `$\\frac{a}{b}$`.
- For prime notation, use `$f'(x)$` or `$f^{\\prime}(x)$`.

## 4. Common Exam Components
- `conditions`: List of condition strings like `["(가) 모든 실수 $x$에 대하여 $f(x) \\ge 0$", "(나) $f(1) = 2$"]`
- `bogi`: List of items (`["ㄱ. ...", "ㄴ. ...", "ㄷ. ..."]`) OR a Korean `<보기>` reading paragraph string. Optional `bogi_title` (default `"<보 기>"`).
- `choices`: List of 5 choices. Numbering ①~⑤ is automatically formatted.
- `figures`:
  - `function_plot`: Explicit, Implicit, Parametric, or Polar curves with shaded areas and points.
  - `geometry_physics`: Specify `points`, `segments`, `circles`, `angles`, `physics_objects`.
  - `raw_svg`: Custom raw SVG string.
"""


# Periodic cleanup background task for local storage
async def periodic_cleanup():
    storage = get_storage_backend()
    if isinstance(storage, LocalStorage):
        while True:
            await asyncio.sleep(3600)  # run every hour
            storage.cleanup_expired_files()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background cleanup
    cleanup_task = asyncio.create_task(periodic_cleanup())
    async with mcp.session_manager.run():
        yield
    cleanup_task.cancel()


# FastAPI App for unified HTTP hosting (MCP + Static file downloads)
app = FastAPI(
    title="CreatePDFMCP Server",
    description="MCP server and PDF file hosting for Korean Math/Physics/CSAT exam generation",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "storage_mode": settings.STORAGE_MODE,
        "r2_configured": settings.is_r2_configured,
        "local_storage_dir": str(settings.local_storage_path),
    }


@app.get("/files/{filename}")
async def get_local_file(filename: str):
    """Serves generated PDF or QR code image in local storage mode."""
    file_path = settings.local_storage_path / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    content_type = "application/pdf" if filename.endswith(".pdf") else "image/png"
    return FileResponse(file_path, media_type=content_type)


# Configure transport security allowing tunnel/external domain hosts (e.g. Cloudflare Tunnel)
security_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)

# Initialize MCP Streamable HTTP and SSE apps
http_app = mcp.streamable_http_app(streamable_http_path="/mcp", transport_security=security_settings)
sse_app = mcp.sse_app(transport_security=security_settings)

# Mount MCP Streamable HTTP endpoints (/mcp and /mcp/) directly to avoid 307 redirects and sub-app 404s
mcp_endpoint = http_app.routes[0].endpoint
app.router.add_route("/mcp", mcp_endpoint, methods=["GET", "POST", "DELETE", "OPTIONS"])
app.router.add_route("/mcp/", mcp_endpoint, methods=["GET", "POST", "DELETE", "OPTIONS"])

# Mount MCP SSE endpoints (/sse and /messages)
for route in sse_app.routes:
    app.routes.append(route)


def main():
    """Server entrypoint."""
    import uvicorn
    transport = os.environ.get("MCP_TRANSPORT", "http").lower()
    if transport == "stdio":
        asyncio.run(mcp.run_stdio_async())
    else:
        print(f"Starting CreatePDFMCP on {settings.HOST}:{settings.PORT}")
        uvicorn.run(app, host=settings.HOST, port=settings.PORT)


if __name__ == "__main__":
    main()
