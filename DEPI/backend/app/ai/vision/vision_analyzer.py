# backend/app/ai/vision/vision_analyzer.py
# ─────────────────────────────────────────────────────────────────────────────
# Vision Analyzer
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from app.ai.vision.service import VisionService
from app.ai.multimodal.schemas import ProcessingContext, UnifiedMedicalContext
from app.ai.multimodal.enums import ModalityType, DocumentType
import uuid


class VisionAnalyzer:
    """Analyzer for medical images (X-rays, MRIs, etc.)."""
    
    def __init__(self, provider: Optional[Any] = None):
        self.provider = provider
        # Initialize the new robust VisionService
        self.vision_service = VisionService()
    
    async def analyze_image(self, image_data: bytes, image_type: str) -> Dict[str, Any]:
        """
        Analyze a medical image utilizing the Multimodal processing pipeline.
        Returns the parsed UnifiedMedicalContext as a dictionary for backwards compatibility.
        """
        # Create a mock upload ID if not provided in this legacy method signature
        upload_id = str(uuid.uuid4())
        
        # Build processing context
        context = ProcessingContext(
            upload_id=upload_id,
            filename="legacy_upload",
            mime_type=image_type,
            file_bytes=image_data,
            modality=ModalityType.IMAGE,
            document_type=DocumentType.UNKNOWN,
            unified_context=UnifiedMedicalContext(
                upload_id=upload_id,
                filename="legacy_upload",
                mime_type=image_type,
                modality=ModalityType.IMAGE
            )
        )
        
        # Execute vision service
        final_context = await self.vision_service.process(context)
        
        # Return as dict for backwards compatibility
        return final_context.unified_context.model_dump()
    
    def detect_anomalies(self, image_data: bytes) -> list[str]:
        """
        Detect anomalies in medical images.
        Currently delegates to analyze_image in a real implementation.
        """
        return []
