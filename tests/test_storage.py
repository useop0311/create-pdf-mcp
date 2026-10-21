import pytest
from pathlib import Path
from create_pdf_mcp.storage.base import generate_qr_code_png
from create_pdf_mcp.storage.local_storage import LocalStorage


@pytest.mark.asyncio
async def test_qr_code_generation():
    png_bytes = generate_qr_code_png("https://example.com/test.pdf")
    assert png_bytes.startswith(b"\x89PNG")
    assert len(png_bytes) > 100


@pytest.mark.asyncio
async def test_local_storage_saving_and_cleanup(tmp_path: Path):
    storage = LocalStorage(storage_dir=tmp_path, base_url="http://testserver:8000")
    dummy_pdf = b"%PDF-1.4 dummy content"

    url = await storage.save_pdf("test_id", dummy_pdf, "sample.pdf")
    assert url == "http://testserver:8000/files/test_id_sample.pdf"
    assert (tmp_path / "test_id_sample.pdf").exists()

    # Test QR image save
    qr_bytes = generate_qr_code_png(url)
    img_url = await storage.save_image("test_id", qr_bytes, "qr.png")
    assert img_url == "http://testserver:8000/files/test_id_qr.png"
    assert (tmp_path / "test_id_qr.png").exists()

    # Test cleanup with ttl 0
    deleted = storage.cleanup_expired_files(ttl_hours=-1)
    assert deleted >= 2
