# backend/app/ai/multimodal/router.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Router
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.multimodal.interfaces import BaseRouter
from app.ai.multimodal.schemas import ProcessingContext
from app.ai.multimodal.enums import ProcessorType, ModalityType
from app.ai.multimodal.logger import MultimodalLogger, PipelineStage


class DefaultRouter(BaseRouter):
    """Routes based on classified modality."""
    
    def route(self, context: ProcessingContext) -> ProcessorType:
        upload_id = context.upload_id
        modality = context.modality
        
        try:
            if modality == ModalityType.IMAGE:
                processor = ProcessorType.VISION
            elif modality == ModalityType.DOCUMENT:
                # Route PDFs to the Vision model (Gemini). Gemini ingests PDFs
                # natively and produces a far richer clinical interpretation
                # (lab-value comparison, drug extraction, doctor-grade summary)
                # than raw OCR text extraction. OCR remains available as an
                # internal fallback inside the vision service if needed.
                processor = ProcessorType.VISION
            elif modality == ModalityType.TEXT:
                # Text doesn't need OCR or Vision, but we can bypass or route to a plain text parser
                processor = ProcessorType.UNKNOWN
            else:
                processor = ProcessorType.UNKNOWN
                
            MultimodalLogger.log_event(
                PipelineStage.CLASSIFICATION_COMPLETED, # piggybacking to log routing decision
                upload_id,
                f"Routed to {processor.value}",
                {"processor": processor.value}
            )
            return processor
            
        except Exception as e:
            MultimodalLogger.log_event(PipelineStage.PIPELINE_FAILED, upload_id, f"Routing failed: {e}", is_error=True)
            raise
