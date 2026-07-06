# backend/app/ai/multimodal/decision.py
# ─────────────────────────────────────────────────────────────────────────────
# Orchestration Decision
# The structured decision produced by the LLM orchestration brain.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.ai.multimodal.enums import ModalityType, DocumentType, ProcessorType


class OrchestrationDecision(BaseModel):
    """
    Structured output of the orchestration brain.

    The brain (LLM or otherwise) must produce one of these for every upload,
    deciding both the fine-grained document type and which processor should
    handle extraction, together with a confidence score and a short rationale.
    """

    modality: ModalityType = ModalityType.UNKNOWN
    document_type: DocumentType = DocumentType.UNKNOWN
    processor: ProcessorType = ProcessorType.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = None

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, value: float) -> float:
        if value is None:
            return 0.0
        return max(0.0, min(1.0, float(value)))


class OrchestrationDecisionError(Exception):
    """
    Raised when the orchestration brain cannot return a usable decision
    (LLM call failure, malformed JSON, invalid enum value, etc.).

    The orchestrator catches this and falls back to the heuristic
    classifier/router so the pipeline never hard-fails.
    """
    pass
