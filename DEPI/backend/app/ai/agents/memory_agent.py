# backend/app/ai/agents/memory_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# Memory Agent
# Retrieves and updates longitudinal patient memory from the database.
# ─────────────────────────────────────────────────────────────────────────────

import time
import logging
from typing import Optional

from app.ai.agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """
    Responsible for reading longitudinal patient and clinical memory,
    summarising it, and writing it back to the AgentContext for downstream
    agents to consume.
    """

    def __init__(self) -> None:
        super().__init__(name="memory_agent")

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Load patient and clinical memory summaries for the current user.

        Updates context.patient_memory_summary and context.clinical_memory_summary.
        """
        start = time.monotonic()
        self._trace(context, f"Loading memory for user_id={context.user_id}")

        try:
            if not context.user_id:
                self._trace(context, "No user_id — skipping longitudinal memory.")
                return self._success(context, output={"skipped": True}, duration_ms=0.0)

            from app.services.memory_service import MemoryService
            from app.database.database import SessionLocal

            db = SessionLocal()
            try:
                service = MemoryService(db)
                memory_context = service.inject_memory(
                    user_id=int(context.user_id),
                    conversation_id=context.conversation_id,
                )

                context.patient_memory_summary = memory_context.get("persistent_memory", "") or ""
                context.clinical_memory_summary = memory_context.get("conversation_summary", "") or ""

                self._trace(context, "Memory loaded successfully.")
            finally:
                db.close()

            duration_ms = (time.monotonic() - start) * 1000
            return self._success(
                context,
                output={
                    "patient_memory_length": len(context.patient_memory_summary),
                    "clinical_memory_length": len(context.clinical_memory_summary),
                },
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            logger.warning(f"MemoryAgent failed (non-fatal): {exc}")
            # Memory failure is non-fatal — the pipeline continues
            return self._success(
                context,
                output={"warning": str(exc)},
                duration_ms=duration_ms,
            )
