# backend/app/ai/ocr/easyocr_provider.py
# ─────────────────────────────────────────────────────────────────────────────
# EasyOCR Provider
# ─────────────────────────────────────────────────────────────────────────────

import time
from app.ai.ocr.base import BaseOCRProvider
from app.ai.ocr.models import OCRExtractionResult, OCRTextBlock

# Attempt to import EasyOCR safely
try:
    import easyocr # type: ignore
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class EasyOCRProvider(BaseOCRProvider):
    """Provider for EasyOCR (typically used as a fallback)."""
    
    def __init__(self):
        self._reader = None
        if EASYOCR_AVAILABLE:
            pass

    @property
    def provider_name(self) -> str:
        return "easyocr"

    def is_available(self) -> bool:
        return EASYOCR_AVAILABLE

    async def extract_text(self, image_bytes: bytes, language: str = "en") -> OCRExtractionResult:
        start_time = time.time()
        
        if not self.is_available():
            raise RuntimeError("EasyOCR is not installed or available.")
            
        # ─────────────────────────────────────────────────────────────────────
        # Mocked implementation for architecture.
        # Actual implementation would use self._reader.readtext(image_bytes)
        # ─────────────────────────────────────────────────────────────────────
        
        blocks = []
        full_text = "Mocked EasyOCR Output: Patient John Doe. Blood Pressure 120/80."
        avg_confidence = 0.88
        
        blocks.append(OCRTextBlock(text=full_text, confidence=avg_confidence))
        
        processing_time = (time.time() - start_time) * 1000
        
        return OCRExtractionResult(
            provider_name=self.provider_name,
            full_text=full_text,
            blocks=blocks,
            average_confidence=avg_confidence,
            processing_time_ms=processing_time,
            warnings=["Using mocked EasyOCR output for architecture scaffolding."]
        )
