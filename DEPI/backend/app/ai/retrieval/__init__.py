# backend/app/ai/retrieval/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Retrieval Module
# RAG (Retrieval-Augmented Generation) functionality
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.retrieval.rag_pipeline import run_rag

__all__ = ["run_rag"]
