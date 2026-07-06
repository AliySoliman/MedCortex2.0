# backend/app/ai/prompts/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Prompts Module
# Centralized prompt templates for AI interactions
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.prompts.rag_prompts import RAG_SYSTEM_PROMPT
from app.ai.prompts.symptom_prompts import SYMPTOM_EXTRACTOR_PROMPT
from app.ai.prompts.lifestyle_prompts import LIFESTYLE_SYSTEM_PROMPT, LIFESTYLE_USER_PROMPT

__all__ = [
    "RAG_SYSTEM_PROMPT",
    "SYMPTOM_EXTRACTOR_PROMPT",
    "LIFESTYLE_SYSTEM_PROMPT",
    "LIFESTYLE_USER_PROMPT",
]
