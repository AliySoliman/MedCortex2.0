# backend/app/ai/agents/coordinator.py
# ─────────────────────────────────────────────────────────────────────────────
# Medical Coordinator Agent
# Orchestrates the agent execution pipeline.
# Determines execution order, shares context, and aggregates outputs.
# Does NOT replace LangGraph — it complements it for dynamic reasoning.
# ─────────────────────────────────────────────────────────────────────────────

import time
import logging
import uuid
from typing import Optional, Dict, Any

from app.ai.agents.base import BaseAgent, AgentContext, AgentResult
from app.ai.agents.memory_agent import MemoryAgent
from app.ai.agents.clinical_agent import ClinicalReasoningAgent
from app.ai.agents.retrieval_agent import RetrievalAgent
from app.ai.agents.reporting_agent import ReportingAgent
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class MedicalCoordinatorAgent(BaseAgent):
    """
    The Medical Coordinator is the entry point for the Agent Layer.

    Execution order:
        1. MemoryAgent           — load longitudinal patient context
        2. ClinicalReasoningAgent — extract symptoms, risk, DDx, interactions
        3. RetrievalAgent        — RAG retrieval + evidence
        4. ReportingAgent        — synthesise final structured report

    Each agent receives the shared AgentContext and can read/write freely.
    The coordinator enforces the execution order and handles partial failures.
    """

    def __init__(self) -> None:
        super().__init__(name="medical_coordinator")
        settings = get_settings()
        self._memory_agent = MemoryAgent()
        self._clinical_agent = ClinicalReasoningAgent()
        self._retrieval_agent = RetrievalAgent()
        self._reporting_agent = ReportingAgent()

    async def coordinate(
        self,
        query: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[int] = None,
        unified_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[list] = None,
    ) -> AgentContext:
        """
        Coordinate the full agent pipeline for a given query.

        Args:
            query: The user's question or message.
            user_id: Authenticated user ID (optional).
            unified_context: Parsed UnifiedMedicalContext from a document upload (optional).
            conversation_history: Recent conversation turns (optional).

        Returns:
            The fully populated AgentContext after all agents have run.
        """
        session_id = str(uuid.uuid4())
        context = AgentContext(
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            query=query,
            unified_context=unified_context,
            conversation_history=conversation_history or [],
        )

        self._trace(context, f"Pipeline started. session_id={session_id}")

        pipeline = [
            self._memory_agent,
            self._clinical_agent,
            self._retrieval_agent,
            self._reporting_agent,
        ]

        for agent in pipeline:
            try:
                result = await agent.run(context)
                context = result.context  # Agents update context in-place via reference
                if not result.success:
                    self._trace(context, f"Agent '{agent.name}' failed: {result.error} — continuing.")
            except Exception as exc:
                logger.exception(f"Unhandled exception in agent '{agent.name}'")
                self._trace(context, f"Unhandled exception in '{agent.name}': {exc} — continuing.")

        self._trace(context, "Pipeline complete.")
        return context

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Implement BaseAgent.run() for compatibility when the coordinator
        itself is used as a sub-agent in a larger graph.
        """
        start = time.monotonic()
        try:
            final_context = await self.coordinate(
                query=context.query,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                unified_context=context.unified_context,
                conversation_history=context.conversation_history,
            )
            duration_ms = (time.monotonic() - start) * 1000
            return self._success(
                final_context,
                output={"report": final_context.generated_report},
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            return self._failure(context, error=str(exc), duration_ms=duration_ms)
