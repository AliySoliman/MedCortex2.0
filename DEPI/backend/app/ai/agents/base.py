# backend/app/ai/agents/base.py
# ─────────────────────────────────────────────────────────────────────────────
# Agent Base Classes
# Abstract interface for all MedCortex agents.
# ─────────────────────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentContext(BaseModel):
    """
    Shared context object passed between agents.
    Agents can read and write to this context to share intermediate results.
    """
    session_id: str
    user_id: Optional[str] = None
    conversation_id: Optional[int] = None
    query: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)

    # Multimodal context — populated after upload processing
    unified_context: Optional[Dict[str, Any]] = None

    # Clinical reasoning results
    extracted_symptoms: List[str] = Field(default_factory=list)
    differential_diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    risk_assessment: Optional[Dict[str, Any]] = None
    drug_interactions: List[Dict[str, Any]] = Field(default_factory=list)
    contraindications: List[Dict[str, Any]] = Field(default_factory=list)
    lab_interpretations: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_findings: Dict[str, Any] = Field(default_factory=dict)

    # Retrieval results
    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    rag_answer: Optional[str] = None
    citations: List[str] = Field(default_factory=list)

    # Memory
    patient_memory_summary: Optional[str] = None
    clinical_memory_summary: Optional[str] = None

    # Safety
    safety_validated: bool = False
    safety_issues: List[str] = Field(default_factory=list)

    # Report
    generated_report: Optional[str] = None

    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    agent_trace: List[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """
    Standard result returned by every agent invocation.
    """
    agent_name: str
    success: bool
    context: AgentContext
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class BaseAgent(ABC):
    """
    Abstract base class for all MedCortex agents.

    Agents are responsible for a single reasoning concern.
    They receive an AgentContext, perform their work, update the context,
    and return an AgentResult.
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"medcortex.agents.{name}")

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute this agent's logic.

        Args:
            context: The shared AgentContext.

        Returns:
            AgentResult with updated context and output.
        """
        pass

    def _trace(self, context: AgentContext, message: str) -> None:
        """Append a trace message to the agent trace log."""
        entry = f"[{self.name}] {message}"
        context.agent_trace.append(entry)
        self.logger.debug(entry)

    def _success(self, context: AgentContext, output: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0) -> AgentResult:
        """Helper to build a successful AgentResult."""
        return AgentResult(
            agent_name=self.name,
            success=True,
            context=context,
            output=output,
            duration_ms=duration_ms,
        )

    def _failure(self, context: AgentContext, error: str, duration_ms: float = 0.0) -> AgentResult:
        """Helper to build a failed AgentResult."""
        self.logger.error(f"[{self.name}] failed: {error}")
        return AgentResult(
            agent_name=self.name,
            success=False,
            context=context,
            error=error,
            duration_ms=duration_ms,
        )
