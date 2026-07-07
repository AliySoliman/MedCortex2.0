# backend/app/ai/multimodal/orchestrator.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Orchestrator
# LLM-driven classify + route, with a heuristic safety-net fallback.
# ─────────────────────────────────────────────────────────────────────────────

import time
from typing import Optional

from app.ai.multimodal.classifier import DefaultClassifier
from app.ai.multimodal.decision import OrchestrationDecision, OrchestrationDecisionError
from app.ai.multimodal.enums import PipelineStage
from app.ai.multimodal.exceptions import ValidationError
from app.ai.multimodal.interfaces import BaseOrchestratorBrain
from app.ai.multimodal.llm_brain import GroqOrchestratorBrain
from app.ai.multimodal.logger import MultimodalLogger
from app.ai.multimodal.preprocessing import DefaultPreprocessor
from app.ai.multimodal.router import DefaultRouter
from app.ai.multimodal.schemas import (
    ProcessingContext,
    ProcessingHistoryEntry,
    UnifiedMedicalContext,
)


class MultimodalOrchestrator:
    """
    Orchestrates the ingestion, classification, routing, and preprocessing
    of every uploaded file in MedCortex.

    Classification and routing are driven by a pluggable LLM brain (default:
    GroqOrchestratorBrain using Llama 3.3 70B). If the brain cannot produce a
    usable decision, the orchestrator transparently falls back to the original
    MIME-heuristic classifier + rule-based router so the pipeline never
    hard-fails. The downstream LangGraph (graph/multimodal_builder) consumes
    the resulting `ProcessingContext.processor_type` to execute extraction.
    """

    def __init__(
        self,
        brain: Optional[BaseOrchestratorBrain] = None,
        classifier: Optional[DefaultClassifier] = None,
        router: Optional[DefaultRouter] = None,
        preprocessor: Optional[DefaultPreprocessor] = None,
    ):
        self.brain = brain or GroqOrchestratorBrain()
        self.classifier = classifier or DefaultClassifier()
        self.router = router or DefaultRouter()
        self.preprocessor = preprocessor or DefaultPreprocessor()

    async def process_upload(
        self,
        upload_id: str,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        upload_type: str = "document",
    ) -> ProcessingContext:
        """
        Main entrypoint for any uploaded file.

        Validates, initializes the unified context, asks the LLM brain to
        classify + route (with heuristic fallback), then preprocesses the file.
        Returns a ProcessingContext ready to be executed by the multimodal
        LangGraph (OCR / Vision / text parsing).
        """
        start_time = time.time()
        MultimodalLogger.log_stage_start(
            PipelineStage.UPLOAD_RECEIVED,
            upload_id,
            {"filename": filename, "mime_type": mime_type, "upload_type": upload_type},
        )

        try:
            # 1. Validation
            self._validate_input(upload_id, file_bytes, mime_type)
            MultimodalLogger.log_stage_complete(PipelineStage.UPLOAD_VALIDATED, upload_id)

            # 2. Initialization
            unified_context = UnifiedMedicalContext(
                upload_id=upload_id,
                filename=filename,
                mime_type=mime_type,
            )
            unified_context.processing_history.append(
                ProcessingHistoryEntry(
                    stage=PipelineStage.UPLOAD_RECEIVED,
                    message="Upload received",
                )
            )
            unified_context.processing_history.append(
                ProcessingHistoryEntry(
                    stage=PipelineStage.UPLOAD_VALIDATED,
                    message="Upload validated",
                )
            )

            context = ProcessingContext(
                upload_id=upload_id,
                filename=filename,
                mime_type=mime_type,
                file_bytes=file_bytes,
                upload_type=upload_type,
                unified_context=unified_context,
            )

            # 3. Classification + routing (LLM brain, heuristic fallback)
            await self._classify_and_route(context)

            # 4. Preprocessing
            processed_bytes = await self.preprocessor.preprocess(context)
            context.preprocessed_bytes = processed_bytes
            context.unified_context.processing_history.append(
                ProcessingHistoryEntry(
                    stage=PipelineStage.PREPROCESSING_COMPLETED,
                    message="Preprocessing completed",
                )
            )

            processing_time = (time.time() - start_time) * 1000
            context.unified_context.processing_metadata.processing_time_ms = processing_time

            return context

        except Exception as e:
            MultimodalLogger.log_event(PipelineStage.PIPELINE_FAILED, upload_id, str(e), is_error=True)
            raise

    async def _classify_and_route(self, context: ProcessingContext) -> None:
        """
        Resolve modality / document type / processor for the upload.

        Prefer the LLM brain. On any failure, fall back to the MIME-heuristic
        classifier + rule-based router and record that the fallback was used.
        """
        try:
            decision = await self.brain.decide(context)
            self._apply_decision(context, decision, source="llm")
        except OrchestrationDecisionError as exc:
            MultimodalLogger.log_event(
                PipelineStage.CLASSIFICATION_COMPLETED,
                context.upload_id,
                f"LLM brain unavailable, falling back to heuristics: {exc}",
                {"fallback": True},
            )
            await self._fallback_classify_and_route(context)

    async def _fallback_classify_and_route(self, context: ProcessingContext) -> None:
        """Heuristic safety net: MIME-based classifier + rule-based router."""
        modality, doc_type, confidence = await self.classifier.classify(context)

        # The router reads context.modality, so write the classification result
        # onto the context before routing.
        context.modality = modality
        context.document_type = doc_type
        context.classification_confidence = confidence

        processor = self.router.route(context)

        context.processor_type = processor

        context.unified_context.modality = modality
        context.unified_context.classification = doc_type
        context.unified_context.classification_confidence = confidence
        context.unified_context.confidence_scores.classification = confidence
        context.unified_context.processing_metadata.fallback_used = True
        context.unified_context.processing_history.append(
            ProcessingHistoryEntry(
                stage=PipelineStage.CLASSIFICATION_COMPLETED,
                message=(
                    f"Classified as {modality.value}/{doc_type.value} "
                    f"(heuristic fallback) -> {processor.value}"
                ),
                provider="heuristic",
            )
        )

    def _apply_decision(
        self, context: ProcessingContext, decision: OrchestrationDecision, source: str
    ) -> None:
        """Write an LLM (or other brain) decision into the processing context."""
        context.modality = decision.modality
        context.document_type = decision.document_type
        context.classification_confidence = decision.confidence
        context.processor_type = decision.processor

        context.unified_context.modality = decision.modality
        context.unified_context.classification = decision.document_type
        context.unified_context.classification_confidence = decision.confidence
        context.unified_context.confidence_scores.classification = decision.confidence

        provider_name = getattr(self.brain, "provider_name", source)
        model_name = getattr(self.brain, "model_name", source)
        context.unified_context.processing_metadata.provider = provider_name
        context.unified_context.processing_metadata.model_name = model_name

        context.unified_context.processing_history.append(
            ProcessingHistoryEntry(
                stage=PipelineStage.CLASSIFICATION_COMPLETED,
                message=(
                    f"Classified as {decision.modality.value}/{decision.document_type.value} "
                    f"-> {decision.processor.value}"
                    + (f" ({decision.reasoning})" if decision.reasoning else "")
                ),
                provider=provider_name,
                model_name=model_name,
            )
        )

    def _validate_input(self, upload_id: str, file_bytes: bytes, mime_type: str) -> None:
        if not file_bytes:
            raise ValidationError("File is empty.")
        # Basic validation placeholder.
        # In a real implementation, we would check magic bytes, max size, etc.
