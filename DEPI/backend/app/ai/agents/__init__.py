# backend/app/ai/agents/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Medical Agent Layer
# Specialized agents that coordinate context, tools, and reasoning.
# Agents complement LangGraph — they do NOT replace it.
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.agents.base import BaseAgent, AgentResult, AgentContext
from app.ai.agents.coordinator import MedicalCoordinatorAgent
from app.ai.agents.retrieval_agent import RetrievalAgent
from app.ai.agents.clinical_agent import ClinicalReasoningAgent
from app.ai.agents.memory_agent import MemoryAgent
from app.ai.agents.reporting_agent import ReportingAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "AgentContext",
    "MedicalCoordinatorAgent",
    "RetrievalAgent",
    "ClinicalReasoningAgent",
    "MemoryAgent",
    "ReportingAgent",
]
