import io
from typing import Optional
from pypdf import PdfReader
from docx import Document

from app.config import settings

class FileService:
    @staticmethod
    def extract_text(filename: str, content: bytes) -> Optional[str]:
        lower_name = filename.lower()
        try:
            if lower_name.endswith(".pdf"):
                return FileService._extract_pdf(content)
            elif lower_name.endswith(".docx"):
                return FileService._extract_docx(content)
            else:
                return FileService._extract_text(content)
        except Exception:
            return None

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages[:5]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()[:5000]

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        doc = Document(io.BytesIO(content))
        return "\n".join([p.text for p in doc.paragraphs[:100]])[:5000]

    @staticmethod
    def _extract_text(content: bytes) -> str:
        return content.decode("utf-8", errors="ignore")[:5000]

    @staticmethod
    def validate_size(content: bytes) -> bool:
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        return len(content) <= max_bytes
