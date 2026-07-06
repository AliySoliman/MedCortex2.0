# backend/app/ai/multimodal/interfaces.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Interfaces
# Abstract base classes for pipeline stages
# ─────────────────────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from typing import Tuple
from app.ai.multimodal.schemas import ProcessingContext
from app.ai.multimodal.decision import OrchestrationDecision
from app.ai.multimodal.enums import DocumentType, ModalityType, ProcessorType


class BaseOrchestratorBrain(ABC):
    """
    The pluggable decision-making brain of the multimodal orchestrator.

    Implementations decide both the document classification and the processor
    routing for an upload in a single step. The default implementation is an
    LLM (GroqOrchestratorBrain using Llama 3.3 70B), but any backend
    (another LLM, a local model, a rules engine) can be supplied by
    implementing this interface.
    """

    @abstractmethod
    async def decide(self, context: ProcessingContext) -> OrchestrationDecision:
        """
        Inspect the upload context and return a structured decision.

        Raises:
            OrchestrationDecisionError: if no usable decision can be produced.
        """
        pass


class BaseClassifier(ABC):
    """Classifies the input file into Modality and DocumentType."""

    @abstractmethod
    async def classify(self, context: ProcessingContext) -> Tuple[ModalityType, DocumentType, float]:
        """
        Returns: (ModalityType, DocumentType, confidence_score)
        """
        pass


class BaseRouter(ABC):
    """Determines which processor (OCR/Vision) should handle the file."""
    
    @abstractmethod
    def route(self, context: ProcessingContext) -> ProcessorType:
        """
        Returns the ProcessorType (OCR or VISION) to route to.
        """
        pass


class BasePreprocessor(ABC):
    """Prepares the file for extraction (e.g. resizing, conversion)."""
    
    @abstractmethod
    async def preprocess(self, context: ProcessingContext) -> bytes:
        """
        Returns the preprocessed file bytes.
        """
        pass


class BaseMedicalParser(ABC):
    """Parses raw text (from OCR/Vision) into structured entities."""
    
    @abstractmethod
    async def parse(self, text: str, context: ProcessingContext) -> None:
        """
        Modifies context.unified_context in-place with structured entities
        and clinical findings.
        """
        pass
