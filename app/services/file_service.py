import io
import os
from typing import Optional
from pypdf import PdfReader
from docx import Document

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
        except Exception as e:
            print(f"File extraction error: {e}", flush=True)
            return None

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages[:10]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            text = text.strip()
            
            if not text:
                # Try OCR with poppler
                try:
                    import pytesseract
                    from pdf2image import convert_from_bytes
                    
                    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                    
                    # Use the poppler path
                    poppler_path = r"C:\poppler\bin"
                    
                    images = convert_from_bytes(content, first_page=1, last_page=5, poppler_path=poppler_path)
                    ocr_text = ""
                    for img in images:
                        ocr_text += pytesseract.image_to_string(img) + "\n"
                    text = ocr_text.strip()
                    if text:
                        return text[:10000]
                except Exception as e:
                    print(f"OCR failed: {e}", flush=True)
                
                return "This PDF is scanned/image-based. OCR could not extract text. Please try a text-based PDF."
            
            return text[:10000]
        except Exception as e:
            print(f"PDF extraction error: {e}", flush=True)
            return None

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            doc = Document(io.BytesIO(content))
            return "\n".join([p.text for p in doc.paragraphs[:200]])[:10000]
        except Exception as e:
            print(f"DOCX extraction error: {e}", flush=True)
            return None

    @staticmethod
    def _extract_text(content: bytes) -> str:
        return content.decode("utf-8", errors="ignore")[:10000]

    @staticmethod
    def validate_size(content: bytes) -> bool:
        return len(content) <= 10 * 1024 * 1024
