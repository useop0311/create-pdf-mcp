import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from mcp.server import MCPServer

from .config import settings
from .models.exam import ExamPDFRequest, ExamPDFResponse
from .models.figures import FigureSpec
from .processors.figure_renderer import render_figure_to_svg
from .storage import get_storage_backend, generate_qr_code_png, LocalStorage
from .typst_engine import generate_typst_document, compile_typst_to_pdf, get_pdf_page_count


# Initialize MCPServer (MCP 2.x standard)
mcp = MCPServer(
    name="CreatePDFMCP",
    instructions=(
        "CreatePDFMCP is a specialized MCP server for generating high-quality Korean Math and Physics "
        "exam/worksheet PDFs (수능 2단 칼럼, 패드 1페이지 1문항 필기용 모눈/백지, 1단 워크북) "
        "with 3-tier vector figures (SymPy function plots, declarative geometry/physics diagrams, and raw SVGs). "
        "Always structure problems with Markdown and LaTeX math ($...$, $$...$$), conditions (가/나), and <보기> (ㄱ/ㄴ/ㄷ)."
    ),
)


@mcp.tool(
    name="create_exam_pdf",
    description="Generate a Korean Math or Physics exam/worksheet PDF and return accessible download URL and QR code."
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

    summary = (
        f"### 📄 문제지 PDF 생성이 완료되었습니다!\n"
        f"- **제목**: {request.title} ({request.subtitle or ''})\n"
        f"- **레이아웃**: `{request.layout_mode}` ({page_count} 페이지, 총 {len(request.problems)}문항)\n"
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
        problem_count=len(request.problems),
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
    """Returns guide and examples for authoring Korean exam questions."""
    return """
# Korean Math & Physics Exam Authoring Guide

## 1. Math Formula Syntax
- Use standard LaTeX math: `$f(x) = x^3 - 3x + 1$`, `$\\int_0^1 f(x)dx$`, `$\\frac{a}{b}$`.
- For prime notation, use `$f'(x)$` or `$f^{\\prime}(x)$`.

## 2. Korean Exam Components
- `conditions`: List of condition strings like `["(가) 모든 실수 $x$에 대하여 $f(x) \\ge 0$", "(나) $f(1) = 2$"]`
- `bogi`: List of items like `["ㄱ. $f(0) = 0$", "ㄴ. $f'(1) > 0$", "ㄷ. 방정식 $f(x)=0$은 오직 하나의 실근을 갖는다."]`.
- `choices`: List of 5 choices. Numbering ①~⑤ is automatically formatted.
- `figures`:
  - `function_plot`: Specify `functions` with `expr`, `x_range`, `y_range`, `points`, `shaded_areas`.
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
    yield
    cleanup_task.cancel()


# FastAPI App for unified HTTP hosting (MCP + Static file downloads)
app = FastAPI(
    title="CreatePDFMCP Server",
    description="MCP server and PDF file hosting for Korean Math/Physics exam generation",
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


# Mount MCP Streamable HTTP and SSE apps
app.mount("/mcp", mcp.streamable_http_app())
app.mount("/sse", mcp.sse_app())


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
