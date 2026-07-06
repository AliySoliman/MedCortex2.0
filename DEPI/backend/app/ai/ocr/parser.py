# backend/app/ai/ocr/parser.py
# ─────────────────────────────────────────────────────────────────────────────
# OCR Parser
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.shared.medical_parser import SharedMedicalParser
from app.ai.multimodal.schemas import ProcessingContext


class OCRMedicalParser(SharedMedicalParser):
    """
    Parses raw text extracted from OCR into the UnifiedMedicalContext.
    Inherits from SharedMedicalParser to ensure no duplicated parsing logic.
    """
    
    async def parse(self, text: str, context: ProcessingContext) -> None:
        """
        Store the raw OCR output, then delegate to the SharedMedicalParser
        for structured extraction.
        """
        context.unified_context.ocr_output = text
        await super().parse(text, context)
