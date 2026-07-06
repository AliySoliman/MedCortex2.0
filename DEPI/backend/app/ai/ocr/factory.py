# backend/app/ai/ocr/factory.py
# ─────────────────────────────────────────────────────────────────────────────
# OCR Provider Factory
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.ocr.base import BaseOCRProvider
from app.ai.ocr.paddle_provider import PaddleOCRProvider
from app.ai.ocr.easyocr_provider import EasyOCRProvider


class OCRProviderFactory:
    """Factory to create OCR providers."""
    
    @staticmethod
    def get_provider(provider_name: str) -> BaseOCRProvider:
        """
        Returns an instance of the requested OCR provider.
        """
        name = provider_name.lower()
        if name == "paddleocr":
            return PaddleOCRProvider()
        elif name == "easyocr":
            return EasyOCRProvider()
        else:
            raise ValueError(f"Unknown OCR provider requested: {provider_name}")
