# backend/app/ai/ocr/paddle_provider.py
# ─────────────────────────────────────────────────────────────────────────────
# PaddleOCR Provider
# ─────────────────────────────────────────────────────────────────────────────

import time
from app.ai.ocr.base import BaseOCRProvider
from app.ai.ocr.models import OCRExtractionResult, OCRTextBlock

# Attempt to import PaddleOCR safely
try:
    from paddleocr import PaddleOCR # type: ignore
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


class PaddleOCRProvider(BaseOCRProvider):
    """Provider for PaddleOCR."""
    
    def __init__(self):
        self._ocr_instance = None
        if PADDLE_AVAILABLE:
            # Lazy initialization or basic setup
            # In production, we'd want this to be instantiated once or managed in a pool
            pass

    @property
    def provider_name(self) -> str:
        return "paddleocr"

    def is_available(self) -> bool:
        return PADDLE_AVAILABLE

    async def extract_text(self, image_bytes: bytes, language: str = "en") -> OCRExtractionResult:
        start_time = time.time()
        
        if not self.is_available():
            raise RuntimeError("PaddleOCR is not installed or available.")
            
        # ─────────────────────────────────────────────────────────────────────
        # Note: In a real implementation we would convert image_bytes to a 
        # numpy array and pass it to PaddleOCR. We mock the structure here
        # to ensure the architecture behaves properly.
        # ─────────────────────────────────────────────────────────────────────
        
        # MOCK IMPLEMENTATION FOR ARCHITECTURE
        # For actual implementation:
        # np_arr = np.frombuffer(image_bytes, np.uint8)
        # img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        # result = self._ocr_instance.ocr(img, cls=True)
        
        blocks = []
        full_text = "Mocked PaddleOCR Output: Amoxicillin 500mg, Diagnosis: Strep Throat"
        avg_confidence = 0.95
        
        blocks.append(OCRTextBlock(text=full_text, confidence=avg_confidence))
        
        processing_time = (time.time() - start_time) * 1000
        
        return OCRExtractionResult(
            provider_name=self.provider_name,
            full_text=full_text,
            blocks=blocks,
            average_confidence=avg_confidence,
            processing_time_ms=processing_time,
            warnings=["Using mocked PaddleOCR output for architecture scaffolding."]
        )
