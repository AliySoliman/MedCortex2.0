# backend/app/ai/agents/retrieval_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# Retrieval Agent
# Handles document retrieval from vector stores and builds evidence context.
# ─────────────────────────────────────────────────────────────────────────────

import time
import logging
from typing import Optional, Dict, Any

from app.ai.agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


class RetrievalAgent(BaseAgent):
    """
    Responsible for retrieving relevant medical knowledge from the vector store
    and populating the AgentContext with retrieved documents, citations, and
    a RAG-generated answer.
    """

    def __init__(self) -> None:
        super().__init__(name="retrieval_agent")

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Execute RAG retrieval for the current query.

        Updates context.retrieved_documents, context.rag_answer,
        and context.citations.
        """
        start = time.monotonic()
        self._trace(context, f"Starting retrieval for query: {context.query[:80]}...")

        try:
            # Lazy import to avoid circular dependency and defer heavy model loading
            from app.ai.retrieval.rag_pipeline import run_rag

            result = run_rag(
                user_message=context.query,
                db=None,
                user_id=int(context.user_id) if context.user_id and str(context.user_id).isdigit() else None,
                conversation_id=context.conversation_id,
            )

            context.rag_answer = result.get("answer", "")
            context.retrieved_documents = result.get("sources", [])
            # Flatten sources into citation strings
            context.citations = [
                f"{s.get('book', 'Unknown')} — {s.get('section', '')}"
                for s in result.get("sources", [])
            ]

            self._trace(context, f"Retrieved {len(context.retrieved_documents)} documents.")
            duration_ms = (time.monotonic() - start) * 1000
            return self._success(
                context,
                output={
                    "answer": context.rag_answer,
                    "sources_count": len(context.retrieved_documents),
                },
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            return self._failure(context, error=str(exc), duration_ms=duration_ms)
