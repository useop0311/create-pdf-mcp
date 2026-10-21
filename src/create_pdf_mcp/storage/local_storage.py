import asyncio
import os
import time
from pathlib import Path
from .base import StorageBackend
from ..config import settings


class LocalStorage(StorageBackend):
    def __init__(self, storage_dir: Path | None = None, base_url: str | None = None):
        self.storage_dir = storage_dir or settings.local_storage_path
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = (base_url or settings.PUBLIC_BASE_URL).rstrip("/")

    async def save_pdf(self, file_id: str, pdf_bytes: bytes, filename: str) -> str:
        file_path = self.storage_dir / f"{file_id}_{filename}"
        file_path.write_bytes(pdf_bytes)
        return f"{self.base_url}/files/{file_id}_{filename}"

    async def save_image(self, file_id: str, img_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
        file_path = self.storage_dir / f"{file_id}_{filename}"
        file_path.write_bytes(img_bytes)
        return f"{self.base_url}/files/{file_id}_{filename}"

    def cleanup_expired_files(self, ttl_hours: int | None = None) -> int:
        """Deletes files older than ttl_hours. Returns count of deleted files."""
        ttl = (ttl_hours or settings.LOCAL_FILE_TTL_HOURS) * 3600
        now = time.time()
        deleted = 0
        for item in self.storage_dir.glob("*"):
            if item.is_file():
                try:
                    if now - item.stat().st_mtime > ttl:
                        item.unlink()
                        deleted += 1
                except Exception:
                    pass
        return deleted
