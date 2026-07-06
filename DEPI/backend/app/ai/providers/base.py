# backend/app/ai/providers/base.py
# ─────────────────────────────────────────────────────────────────────────────
# AI Provider Abstraction Layer
# Base interface for all AI providers (Groq, OpenAI, etc.)
# ─────────────────────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def get_llm(self, model: str, temperature: float = 0.0, max_tokens: int = 1024, **kwargs) -> Any:
        """Get a language model instance."""
        pass
    
    @abstractmethod
    def get_embeddings(self, model: str, **kwargs) -> Any:
        """Get an embeddings model instance."""
        pass
    
    @abstractmethod
    def get_chat_model(self, model: str, **kwargs) -> Any:
        """Get a chat model instance."""
        pass
    
    @abstractmethod
    def available_models(self) -> List[str]:
        """Return list of available models for this provider."""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate the API key is working."""
        pass


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        pass


class BaseChatProvider(ABC):
    """Abstract base class for chat providers."""
    
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from messages."""
        pass
    
    @abstractmethod
    def generate_stream(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a streaming response from messages."""
        pass
    
    def transcribe_audio(self, audio_file: bytes, filename: str = "audio.webm", **kwargs) -> str:
        """Transcribe audio using provider's transcription model. Default implementation raises NotImplementedError."""
        raise NotImplementedError(f"{self.__class__.__name__} does not support audio transcription")
