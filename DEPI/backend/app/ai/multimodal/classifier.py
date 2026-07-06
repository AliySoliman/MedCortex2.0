# backend/app/ai/multimodal/classifier.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Classifier
# ─────────────────────────────────────────────────────────────────────────────

from typing import Tuple
from app.ai.multimodal.interfaces import BaseClassifier
from app.ai.multimodal.schemas import ProcessingContext
from app.ai.multimodal.enums import ModalityType, DocumentType
from app.ai.multimodal.utils import get_mime_modality
from app.ai.multimodal.logger import MultimodalLogger, PipelineStage


class DefaultClassifier(BaseClassifier):
    """
    Default classifier based on heuristics and MIME types.
    Can be extended to use an LLM for deeper classification.
    """
    
    async def classify(self, context: ProcessingContext) -> Tuple[ModalityType, DocumentType, float]:
        MultimodalLogger.log_stage_start(PipelineStage.CLASSIFICATION_STARTED, context.upload_id)
        
        try:
            # Basic MIME-based modality
            mime_modality = get_mime_modality(context.mime_type)
            
            if mime_modality == "image":
                modality = ModalityType.IMAGE
                confidence = 0.9
            elif mime_modality == "document":
                modality = ModalityType.DOCUMENT
                confidence = 0.9
            elif mime_modality == "text":
                modality = ModalityType.TEXT
                confidence = 1.0
            else:
                modality = ModalityType.UNKNOWN
                confidence = 0.0
                
            # For Milestone 1, we default DocumentType to UNKNOWN
            # In Sprint 3 (Clinical Intelligence), we will use LLMs to classify the specific DocumentType
            doc_type = DocumentType.UNKNOWN

            context.unified_context.classification_confidence = confidence
            context.unified_context.confidence_scores.classification = confidence

            MultimodalLogger.log_stage_complete(
                PipelineStage.CLASSIFICATION_COMPLETED,
                context.upload_id,
                {"modality": modality.value, "confidence": confidence}
            )
            return modality, doc_type, confidence
            
        except Exception as e:
            MultimodalLogger.log_stage_error(PipelineStage.CLASSIFICATION_COMPLETED, context.upload_id, str(e))
            raise
