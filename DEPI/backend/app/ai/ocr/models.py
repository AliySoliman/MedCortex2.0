# backend/app/ai/ocr/models.py
# ─────────────────────────────────────────────────────────────────────────────
# OCR Models
# ─────────────────────────────────────────────────────────────────────────────

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class OCRTextBlock(BaseModel):
    """A single block of text extracted by OCR."""
    text: str
    confidence: float
    bbox: Optional[List[List[int]]] = None


class OCRExtractionResult(BaseModel):
    """Raw extraction result from an OCR Provider."""
    provider_name: str
    full_text: str
    blocks: List[OCRTextBlock] = Field(default_factory=list)
    average_confidence: float
    processing_time_ms: float = 0.0
    warnings: List[str] = Field(default_factory=list)


class OCRStructuredData(BaseModel):
    """
    Structured output after parsing the raw OCR text.
    Matches the schema expected by the UnifiedMedicalContext.
    """
    patient: Dict[str, Any] = Field(default_factory=dict)
    doctor: Dict[str, Any] = Field(default_factory=dict)
    medications: List[Dict[str, Any]] = Field(default_factory=list)
    diagnoses: List[str] = Field(default_factory=list)
    lab_values: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
