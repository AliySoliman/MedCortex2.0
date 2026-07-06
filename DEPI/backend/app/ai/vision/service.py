# backend/app/ai/vision/service.py
# ─────────────────────────────────────────────────────────────────────────────
# Vision Service
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.vision.provider import VisionProvider
from app.ai.shared.medical_parser import SharedMedicalParser
from app.ai.multimodal.schemas import ProcessingContext


class VisionService:
    """
    Main service orchestrating Vision analysis and parsing.
    Called by the Multimodal Orchestrator.
    """
    
    def __init__(self, provider: VisionProvider = None, parser: SharedMedicalParser = None):
        self.provider = provider or VisionProvider()
        self.parser = parser or SharedMedicalParser()
        
    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Executes the Vision pipeline: Provider (VLM) -> Parser (LLM).
        Updates the context in place and returns it.
        Vision output is always preserved even if parser fails.
        """
        
        # 1. Analyze image using Vision Language Model
        image_bytes = context.preprocessed_bytes or context.file_bytes
        vision_result = await self.provider.analyze_image(
            image_bytes=image_bytes,
            mime_type=context.mime_type,
            upload_id=context.upload_id
        )
        
        # 2. Update context with extraction metadata (preserve vision output always)
        context.unified_context.vision_output = vision_result["raw_text"]
        context.unified_context.vision_confidence = vision_result["confidence"]
        context.unified_context.confidence_scores.vision = vision_result["confidence"]
        context.unified_context.processing_metadata.provider = self.provider.provider_name
        context.unified_context.processing_metadata.model_name = vision_result["model_used"]
        
        # 3. Parse raw vision text into structured medical context (non-fatal)
        try:
            await self.parser.parse(vision_result["raw_text"], context)
        except Exception as e:
            # Parser failure should not overwrite vision output
            # Log the error but continue with vision output preserved
            from app.ai.multimodal.logger import MultimodalLogger, PipelineStage
            MultimodalLogger.log_event(
                PipelineStage.PARSER_COMPLETED,
                context.upload_id,
                f"Parser failed but vision output preserved: {e}",
                is_error=True
            )
            # Set parser confidence to 0 to indicate failure
            context.unified_context.parser_confidence = 0.0
            context.unified_context.confidence_scores.parser = 0.0
        
        # 4. Overall confidence blending (use vision confidence if parser failed)
        base_conf = vision_result["confidence"]
        parser_conf = context.unified_context.parser_confidence or 1.0

        blended_confidence = (base_conf * 0.7) + (parser_conf * 0.3)
        context.unified_context.overall_confidence = blended_confidence
        context.unified_context.confidence_scores.overall = blended_confidence

        return context
