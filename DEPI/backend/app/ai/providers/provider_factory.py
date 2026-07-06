# backend/app/ai/providers/provider_factory.py
# ─────────────────────────────────────────────────────────────────────────────
# Provider Factory
# Factory for creating AI provider instances
# ─────────────────────────────────────────────────────────────────────────────

from typing import Optional, Dict, Any

from app.ai.providers.base import BaseAIProvider
from app.ai.providers.groq_provider import GroqProvider
from app.ai.providers.gemini_provider import GeminiProvider


class ProviderFactory:
    """Factory for creating AI provider instances."""
    
    _providers: Dict[str, type] = {
        "groq": GroqProvider,
        "gemini": GeminiProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register a new provider class."""
        cls._providers[name.lower()] = provider_class
    
    @classmethod
    def create_provider(cls, provider_name: str, **kwargs) -> BaseAIProvider:
        """Create a provider instance by name."""
        provider_name = provider_name.lower()
        provider_class = cls._providers.get(provider_name)
        
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(cls._providers.keys())}")
        
        return provider_class(**kwargs)
    
    @classmethod
    def get_default_provider(cls) -> BaseAIProvider:
        """Get the default provider (Groq)."""
        return cls.create_provider("groq")

    @classmethod
    def get_provider(cls, provider_name: str = "groq", **kwargs) -> BaseAIProvider:
        """Backward-compatible alias used by older AI modules."""
        return cls.create_provider(provider_name, **kwargs)


_provider_cache: Dict[str, BaseAIProvider] = {}


def get_provider(provider_name: str = "groq", **kwargs) -> BaseAIProvider:
    """Get a cached provider instance by name. Caches per provider name (no kwargs)."""
    key = provider_name.lower()
    if key not in _provider_cache:
        _provider_cache[key] = ProviderFactory.create_provider(provider_name, **kwargs)
    return _provider_cache[key]


def get_default_llm(**kwargs):
    """Get the default LLM instance (Groq)."""
    provider = get_provider("groq")
    return provider.get_llm(**kwargs)


def get_default_embeddings(**kwargs):
    """Get the default embeddings instance (HuggingFace BGE model)."""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            **kwargs,
        )
    except ImportError:
        # Fallback: try sentence-transformers directly
        from langchain_community.embeddings import HuggingFaceEmbeddings as LegacyEmbeddings  # type: ignore
        return LegacyEmbeddings(model_name="BAAI/bge-large-en-v1.5", **kwargs)
