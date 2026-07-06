# backend/app/ai/vision/ocr_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────
# OCR Pipeline
# Optical character recognition for medical documents
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class OCREngine(ABC):
    """Abstract base class for OCR engines."""
    
    @abstractmethod
    def extract_text(
        self,
        image_data: bytes,
    ) -> str:
        """
        Extract text from image.
        
        Placeholder for future implementation.
        """
        pass
    
    @abstractmethod
    def extract_structured_text(
        self,
        image_data: bytes,
    ) -> Dict[str, Any]:
        """
        Extract structured text from image.
        
        Placeholder for future implementation.
        """
        pass


class OCRPipeline:
    """Pipeline for OCR operations."""
    
    def __init__(self, engine: Optional[OCREngine] = None):
        self.engine = engine
    
    def process(
        self,
        image_data: bytes,
    ) -> Dict[str, Any]:
        """
        Process image through OCR pipeline.
        
        Placeholder for future implementation.
        """
        return {
            "status": "not_implemented",
        }
