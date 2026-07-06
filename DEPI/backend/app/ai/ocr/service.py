# backend/app/ai/ocr/service.py
# ─────────────────────────────────────────────────────────────────────────────
# OCR Service
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.ocr.provider import RobustOCRExtractor
from app.ai.ocr.parser import OCRMedicalParser
from app.ai.multimodal.schemas import ProcessingContext


class OCRService:
    """
    Main service orchestrating the OCR extraction and parsing.
    Called by the Multimodal Orchestrator or Router.
    """
    
    def __init__(self, extractor: RobustOCRExtractor = None, parser: OCRMedicalParser = None):
        self.extractor = extractor or RobustOCRExtractor()
        self.parser = parser or OCRMedicalParser()
        
    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Executes the OCR pipeline: Extractor -> Parser.
        Updates the context in place and returns it.
        """
        
        # 1. Extract text from image (using preprocessed bytes if available, else raw)
        image_bytes = context.preprocessed_bytes or context.file_bytes
        extraction_result = await self.extractor.extract(image_bytes, context.upload_id)
        
        # 2. Update context with extraction metadata
        context.unified_context.ocr_confidence = extraction_result.average_confidence
        context.unified_context.confidence_scores.ocr = extraction_result.average_confidence
        context.unified_context.processing_metadata.provider = extraction_result.provider_name

        # If fallback was used, the provider name in result will differ from primary
        if extraction_result.warnings:
            context.unified_context.processing_metadata.fallback_used = True
            context.unified_context.processing_metadata.warnings.extend(extraction_result.warnings)
            
        # 3. Parse raw text into structured medical context
        await self.parser.parse(extraction_result.full_text, context)
        
        # 4. Overall confidence blending
        # For OCR, overall confidence relies heavily on the text extraction confidence
        # combined with parser confidence.
        base_conf = extraction_result.average_confidence
        parser_conf = context.unified_context.parser_confidence or 1.0

        blended_confidence = (base_conf * 0.7) + (parser_conf * 0.3)
        context.unified_context.overall_confidence = blended_confidence
        context.unified_context.confidence_scores.overall = blended_confidence

        return context
