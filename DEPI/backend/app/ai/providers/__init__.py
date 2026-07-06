# backend/app/ai/providers/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# AI Providers Module
# Provider abstraction layer for AI services
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.providers.base import BaseAIProvider, BaseEmbeddingProvider, BaseChatProvider
from app.ai.providers.groq_provider import GroqProvider, get_groq_provider
from app.ai.providers.model_registry import ModelRegistry, get_model_registry, ModelInfo, ModelType
from app.ai.providers.provider_factory import ProviderFactory, get_provider, get_default_llm, get_default_embeddings

__all__ = [
    "BaseAIProvider",
    "BaseEmbeddingProvider", 
    "BaseChatProvider",
    "GroqProvider",
    "get_groq_provider",
    "ModelRegistry",
    "get_model_registry",
    "ModelInfo",
    "ModelType",
    "ProviderFactory",
    "get_provider",
    "get_default_llm",
    "get_default_embeddings",
]
