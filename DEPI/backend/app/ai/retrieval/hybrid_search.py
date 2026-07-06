# backend/app/ai/retrieval/hybrid_search.py
# ─────────────────────────────────────────────────────────────────────────────
# Hybrid Search
# Combined keyword and semantic search
# ─────────────────────────────────────────────────────────────────────────────

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class HybridSearchEngine(ABC):
    """Abstract base class for hybrid search engines."""
    
    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (keyword + semantic).
        
        Placeholder for future implementation.
        """
        pass


class HybridSearchService:
    """Service for hybrid search operations."""
    
    def __init__(self, engine: Optional[HybridSearchEngine] = None):
        self.engine = engine
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        
        Placeholder for future implementation.
        """
        return []
