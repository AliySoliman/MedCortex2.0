# backend/app/ai/ocr/base.py
# ─────────────────────────────────────────────────────────────────────────────
# Base OCR Provider
# ─────────────────────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from typing import Optional
from app.ai.ocr.models import OCRExtractionResult


class BaseOCRProvider(ABC):
    """Abstract base class for all OCR Providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the OCR provider."""
        pass

    @abstractmethod
    async def extract_text(self, image_bytes: bytes, language: str = "en") -> OCRExtractionResult:
        """
        Extract text from the given image bytes.
        Returns an OCRExtractionResult containing text and confidence.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available (e.g. dependencies installed)."""
        pass
