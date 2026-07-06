# backend/app/ai/multimodal/logger.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Logger
# Standardized logging for pipeline events
# ─────────────────────────────────────────────────────────────────────────────

import logging
from typing import Any, Dict, Optional
from app.ai.multimodal.enums import PipelineStage

logger = logging.getLogger("medcortex.multimodal")

class MultimodalLogger:
    """Standardized logging for the Multimodal pipeline."""

    @staticmethod
    def log_event(
        stage: PipelineStage,
        upload_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        is_error: bool = False
    ) -> None:
        """
        Log a pipeline event with context.
        Sensitive patient data should NOT be passed into `metadata`.
        """
        log_data = {
            "stage": stage.value,
            "upload_id": upload_id,
        }
        if metadata:
            log_data.update(metadata)
            
        log_msg = f"[{stage.value}] [Upload: {upload_id}] - {message} | Meta: {log_data}"

        if is_error:
            logger.error(log_msg)
        else:
            logger.info(log_msg)

    @staticmethod
    def log_stage_start(stage: PipelineStage, upload_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        MultimodalLogger.log_event(stage, upload_id, "Stage started", metadata)

    @staticmethod
    def log_stage_complete(stage: PipelineStage, upload_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        MultimodalLogger.log_event(stage, upload_id, "Stage completed successfully", metadata)

    @staticmethod
    def log_stage_error(stage: PipelineStage, upload_id: str, error_msg: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if metadata is None:
            metadata = {}
        metadata["error"] = error_msg
        MultimodalLogger.log_event(stage, upload_id, f"Stage failed: {error_msg}", metadata, is_error=True)
