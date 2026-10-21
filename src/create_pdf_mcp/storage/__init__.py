from .base import StorageBackend, generate_qr_code_png
from .local_storage import LocalStorage
from .r2_storage import CloudflareR2Storage
from ..config import settings


def get_storage_backend() -> StorageBackend:
    """Returns configured storage backend based on settings."""
    mode = settings.STORAGE_MODE.lower()
    if mode == "r2":
        return CloudflareR2Storage()
    elif mode == "local":
        return LocalStorage()
    else:  # auto
        if settings.is_r2_configured:
            return CloudflareR2Storage()
        return LocalStorage()


__all__ = [
    "StorageBackend",
    "LocalStorage",
    "CloudflareR2Storage",
    "get_storage_backend",
    "generate_qr_code_png",
]
