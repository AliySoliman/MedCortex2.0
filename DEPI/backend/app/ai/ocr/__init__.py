# backend/app/ai/ocr/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# OCR Module
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.ocr.service import OCRService
from app.ai.ocr.provider import RobustOCRExtractor
from app.ai.ocr.factory import OCRProviderFactory
from app.ai.ocr.models import OCRExtractionResult, OCRStructuredData

__all__ = [
    "OCRService",
    "RobustOCRExtractor",
    "OCRProviderFactory",
    "OCRExtractionResult",
    "OCRStructuredData"
]
