# backend/app/ai/graph/graph_factory.py
# ─────────────────────────────────────────────────────────────────────────────
# Graph Factory
# Factory for creating LangGraph workflow instances
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional, Type
from enum import Enum

from app.ai.graph.multimodal_builder import get_multimodal_graph


class GraphType(Enum):
    """Types of available graphs."""
    CHAT = "chat"
    VISION = "vision"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    LAB = "lab"
    REPORT = "report"
    MULTIMODAL = "multimodal"


class GraphFactory:
    """Factory for creating LangGraph workflow instances."""
    
    def __init__(self):
        self._graph_builders: Dict[GraphType, callable] = {}
        # Register the real, implemented graph (multimodal upload execution).
        self.register_builder(GraphType.MULTIMODAL, get_multimodal_graph)
    
    def register_builder(self, graph_type: GraphType, builder: callable):
        """Register a graph builder function."""
        self._graph_builders[graph_type] = builder
    
    def create_graph(self, graph_type: GraphType, **kwargs) -> Any:
        """
        Create a graph instance by type.
        
        Placeholder for future LangGraph implementation.
        """
        builder = self._graph_builders.get(graph_type)
        if not builder:
            raise ValueError(f"Graph type {graph_type} not registered")
        return builder(**kwargs)
    
    def get_available_graphs(self) -> list[str]:
        """Get list of available graph types."""
        return [g.value for g in GraphType]


# Global factory instance
_graph_factory = GraphFactory()


def get_graph_factory() -> GraphFactory:
    """Get the global graph factory instance."""
    return _graph_factory
