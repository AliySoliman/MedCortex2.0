# backend/app/ai/graph/orchestration_builder.py
# ─────────────────────────────────────────────────────────────────────────────
# Orchestration Graph Builder
# Builds the LangGraph workflow for the Orchestration Engine
# ─────────────────────────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END
from app.ai.graph.orchestration_state import OrchestrationState
from app.ai.graph.orchestration_nodes import orchestrator_node, pipeline_dispatcher_node


def build_orchestration_graph():
    """
    Build the LangGraph workflow for the Orchestration Engine.
    
    Graph Structure:
    ┌─────────────────────────────────────────────────────────────────┐
    │                        USER INPUT                                 │
    │  user_message, has_image, image_description,                     │
    │  conversation_history, user_profile, from_audio                  │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    ORCHESTRATOR NODE                              │
    │  - Analyzes user input using OrchestratorEngine                 │
    │  - Determines which pipelines to activate                        │
    │  - Assesses urgency (routine/soon/urgent)                        │
    │  - Identifies appropriate specialist                             │
    │  - Classifies image type (if applicable)                         │
    │  Outputs: pipelines, primary_pipeline, urgency,                   │
    │           specialist_hint, routing_reason, image_type           │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                 PIPELINE DISPATCHER NODE                         │
    │  - Routes to specialized pipelines based on orchestration        │
    │  - Executes pipelines in correct order                           │
    │  - Aggregates results from all activated pipelines               │
    │  Outputs: rag_answer, vision_output, drug_info,                 │
    │           doctor_results, lifestyle_recommendations, etc.        │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                           END                                     │
    │  Final response with all pipeline results                        │
    └─────────────────────────────────────────────────────────────────┘
    
    Available Pipelines:
    - rag: Medical knowledge retrieval from clinical textbooks
    - vision: Multimodal image analysis (lab reports, prescriptions, etc.)
    - drug_rag: Drug interaction and recommendation retrieval
    - doctor_finder: Physician and specialist lookup
    - lifestyle: Diet, exercise, sleep, and wellness recommendations
    - wound_vision: Specialized wound and dermatology analysis
    - stt_passthrough: Speech-to-text passthrough flag
    
    Returns:
        Compiled LangGraph workflow ready for execution
    """
    workflow = StateGraph(OrchestrationState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("pipeline_dispatcher", pipeline_dispatcher_node)
    
    # Define edges
    workflow.set_entry_point("orchestrator")
    workflow.add_edge("orchestrator", "pipeline_dispatcher")
    workflow.add_edge("pipeline_dispatcher", END)
    
    # Compile graph
    return workflow.compile()


def get_orchestration_graph():
    """Get the compiled orchestration graph instance."""
    return build_orchestration_graph()
