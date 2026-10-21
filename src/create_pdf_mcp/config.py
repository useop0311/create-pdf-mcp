from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # Storage: "auto", "r2", "local", "both"
    STORAGE_MODE: str = "auto"
    LOCAL_STORAGE_DIR: str = "./data/files"
    LOCAL_FILE_TTL_HOURS: int = 24

    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "exam-pdfs"
    R2_PUBLIC_DOMAIN: str = ""
    R2_PRESIGNED_EXPIRY_SECONDS: int = 604800  # 7 days

    @property
    def local_storage_path(self) -> Path:
        p = Path(self.LOCAL_STORAGE_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_r2_configured(self) -> bool:
        return bool(
            self.R2_ACCOUNT_ID
            and self.R2_ACCESS_KEY_ID
            and self.R2_SECRET_ACCESS_KEY
            and self.R2_BUCKET_NAME
        )


settings = Settings()
