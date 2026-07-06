# backend/app/ai/retrieval/embedder.py
# ─────────────────────────────────────────────────────────────────────────────
# Embedder
# Text embedding for semantic search
# ─────────────────────────────────────────────────────────────────────────────

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class Embedder(ABC):
    """Abstract base class for embedding engines."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text.
        
        Placeholder for future implementation.
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts.
        
        Placeholder for future implementation.
        """
        pass


class EmbeddingService:
    """Service for embedding operations."""
    
    def __init__(self, embedder: Optional[Embedder] = None):
        self.embedder = embedder
    
    def embed(self, text: str) -> List[float]:
        """
        Embed text.
        
        Placeholder for future implementation.
        """
        return []
