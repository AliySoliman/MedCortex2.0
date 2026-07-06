# backend/app/ai/multimodal/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal AI Engine
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.multimodal.orchestrator import MultimodalOrchestrator
from app.ai.multimodal.schemas import UnifiedMedicalContext, ProcessingContext
from app.ai.multimodal.enums import ModalityType, DocumentType, PipelineStage, ProcessorType
from app.ai.multimodal.decision import OrchestrationDecision, OrchestrationDecisionError
from app.ai.multimodal.interfaces import BaseOrchestratorBrain
from app.ai.multimodal.llm_brain import GroqOrchestratorBrain
from app.ai.multimodal.logger import MultimodalLogger

__all__ = [
    "MultimodalOrchestrator",
    "UnifiedMedicalContext",
    "ProcessingContext",
    "ModalityType",
    "DocumentType",
    "PipelineStage",
    "ProcessorType",
    "OrchestrationDecision",
    "OrchestrationDecisionError",
    "BaseOrchestratorBrain",
    "GroqOrchestratorBrain",
    "MultimodalLogger",
]
