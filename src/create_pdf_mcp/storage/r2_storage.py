import boto3
from botocore.config import Config
from .base import StorageBackend
from ..config import settings


class CloudflareR2Storage(StorageBackend):
    def __init__(self):
        self.endpoint_url = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        self.bucket = settings.R2_BUCKET_NAME
        self.public_domain = settings.R2_PUBLIC_DOMAIN.rstrip("/") if settings.R2_PUBLIC_DOMAIN else None
        self.expiry_sec = settings.R2_PRESIGNED_EXPIRY_SECONDS

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

    async def save_pdf(self, file_id: str, pdf_bytes: bytes, filename: str) -> str:
        key = f"exams/{file_id}_{filename}"
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        return self._generate_url(key)

    async def save_image(self, file_id: str, img_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
        key = f"qr/{file_id}_{filename}"
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=img_bytes,
            ContentType=content_type,
        )
        return self._generate_url(key)

    def _generate_url(self, key: str) -> str:
        if self.public_domain:
            return f"{self.public_domain}/{key}"

        # Otherwise generate presigned URL
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.expiry_sec,
        )
