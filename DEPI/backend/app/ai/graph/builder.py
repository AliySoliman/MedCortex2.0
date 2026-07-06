# backend/app/ai/graph/builder.py
# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Builder
# Builds the Medical AI workflow graph.
# ─────────────────────────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END
from app.ai.graph.state import ChatState
from app.ai.graph.nodes import medical_coordinator_node, safety_node

def build_medical_graph():
    """
    Build the LangGraph workflow for medical AI.
    
    Nodes:
    1. coordinator: Runs the Agent Layer (MedicalCoordinatorAgent)
    2. safety: Runs the AI Safety Layer (ResponseValidator)
    """
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("coordinator", medical_coordinator_node)
    workflow.add_node("safety", safety_node)
    
    # Define edges
    workflow.set_entry_point("coordinator")
    workflow.add_edge("coordinator", "safety")
    workflow.add_edge("safety", END)
    
    # Compile graph
    return workflow.compile()
