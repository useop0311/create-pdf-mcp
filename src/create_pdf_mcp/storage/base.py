import io
from abc import ABC, abstractmethod
import qrcode
from qrcode.image.pil import PilImage


class StorageBackend(ABC):
    @abstractmethod
    async def save_pdf(self, file_id: str, pdf_bytes: bytes, filename: str) -> str:
        """Saves PDF and returns accessible download URL."""
        pass

    @abstractmethod
    async def save_image(self, file_id: str, img_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
        """Saves image (e.g. QR code) and returns accessible URL."""
        pass


def generate_qr_code_png(target_url: str) -> bytes:
    """Generates PNG bytes of a QR code pointing to target_url."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
