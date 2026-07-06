# backend/app/ai/providers/model_registry.py
# ─────────────────────────────────────────────────────────────────────────────
# Model Registry
# Central registry for AI models across providers
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, List, Optional
from enum import Enum


class ModelType(Enum):
    """Types of AI models."""
    CHAT = "chat"
    REASONING = "reasoning"
    VISION = "vision"
    REWRITE = "rewrite"
    OCR = "ocr"
    EMBEDDING = "embedding"
    COMPLETION = "completion"
    ORCHESTRATION = "orchestration"


class ModelInfo:
    """Information about a specific model."""
    
    def __init__(
        self,
        name: str,
        provider: str,
        model_type: ModelType,
        context_length: int = 4096,
        description: str = "",
    ):
        self.name = name
        self.provider = provider
        self.model_type = model_type
        self.context_length = context_length
        self.description = description
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "provider": self.provider,
            "type": self.model_type.value,
            "context_length": self.context_length,
            "description": self.description,
        }


class ModelRegistry:
    """Central registry for AI models."""
    
    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._register_default_models()
    
    def _register_default_models(self):
        """Register default models from supported providers."""
        # Chat Models
        self.register_model(
            ModelInfo(
                name="llama-3.3-70b-versatile",
                provider="groq",
                model_type=ModelType.CHAT,
                context_length=131072,
                description="Llama 3.3 70B - High performance chat model",
            )
        )
        self.register_model(
            ModelInfo(
                name="llama-3.3-70b-versatile",
                provider="groq",
                model_type=ModelType.ORCHESTRATION,
                context_length=131072,
                description="Llama 3.3 70B - Primary multimodal orchestration brain (classify + route)",
            )
        )
        self.register_model(
            ModelInfo(
                name="llama-3.1-70b-versatile",
                provider="groq",
                model_type=ModelType.CHAT,
                context_length=131072,
                description="Llama 3.1 70B - High performance chat model",
            )
        )
        
        # Reasoning Models
        self.register_model(
            ModelInfo(
                name="qwen-3.6-27b",
                provider="groq",
                model_type=ModelType.REASONING,
                context_length=32768,
                description="Qwen 3.6 27B - Advanced reasoning model",
            )
        )
        
        # Vision Models
        self.register_model(
            ModelInfo(
                name="gemini-3.5-flash",
                provider="gemini",
                model_type=ModelType.VISION,
                context_length=1048576,
                description="Gemini 3.5 Flash - Primary multimodal vision model",
            )
        )
        self.register_model(
            ModelInfo(
                name="gemini-2.5-pro",
                provider="gemini",
                model_type=ModelType.VISION,
                context_length=1048576,
                description="Gemini 2.5 Pro - Multimodal document and image understanding",
            )
        )
        self.register_model(
            ModelInfo(
                name="gemini-2.5-flash",
                provider="gemini",
                model_type=ModelType.VISION,
                context_length=1048576,
                description="Gemini 2.5 Flash - Faster multimodal fallback",
            )
        )
        self.register_model(
            ModelInfo(
                name="llama-4-scout",
                provider="groq",
                model_type=ModelType.VISION,
                context_length=8192,
                description="Llama 4 Scout - Groq fallback vision-capable model",
            )
        )
        
        # Rewrite Models
        self.register_model(
            ModelInfo(
                name="llama-3.1-8b-instant",
                provider="groq",
                model_type=ModelType.REWRITE,
                context_length=131072,
                description="Llama 3.1 8B - Fast rewrite model",
            )
        )
        
        # OCR Models
        self.register_model(
            ModelInfo(
                name="paddleocr",
                provider="huggingface",
                model_type=ModelType.OCR,
                context_length=0,
                description="PaddleOCR - Optical character recognition",
            )
        )
        
        # Embedding Models
        self.register_model(
            ModelInfo(
                name="BAAI/bge-large-en-v1.5",
                provider="huggingface",
                model_type=ModelType.EMBEDDING,
                context_length=512,
                description="BGE Large - High quality English embeddings",
            )
        )
    
    def register_model(self, model_info: ModelInfo):
        """Register a model in the registry."""
        self._models[model_info.name] = model_info
    
    def get_model(self, name: str) -> Optional[ModelInfo]:
        """Get model information by name."""
        return self._models.get(name)
    
    def list_models(self, provider: Optional[str] = None, model_type: Optional[ModelType] = None) -> List[ModelInfo]:
        """List models, optionally filtered by provider or type."""
        models = list(self._models.values())
        
        if provider:
            models = [m for m in models if m.provider == provider]
        
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        
        return models
    
    def get_default_chat_model(self) -> str:
        """Get the default chat model name."""
        return "llama-3.3-70b-versatile"

    def get_default_orchestration_model(self) -> str:
        """Get the default orchestration model name."""
        return "llama-3.3-70b-versatile"
    
    def get_default_embedding_model(self) -> str:
        """Get the default embedding model name."""
        return "BAAI/bge-large-en-v1.5"


# Global registry instance
_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    return _registry
