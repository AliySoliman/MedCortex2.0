# backend/app/ai/graph/orchestration_state.py
# ─────────────────────────────────────────────────────────────────────────────
# Orchestration Graph State
# State management for the Orchestration Engine graph
# ─────────────────────────────────────────────────────────────────────────────

from typing import TypedDict, List, Dict, Any, Optional


class OrchestrationState(TypedDict):
    """State for the Orchestration Engine graph."""
    
    # Input
    user_message: str
    has_image: bool
    image_description: Optional[str]
    conversation_history: List[Dict[str, str]]
    user_profile: Optional[Dict[str, Any]]
    from_audio: bool
    
    # Orchestration Output
    pipelines: List[str]
    primary_pipeline: str
    urgency: str
    specialist_hint: Optional[str]
    routing_reason: str
    requires_doctor_finder: bool
    image_type: Optional[str]
    
    # Metadata
    execution_time: float
    metadata: Dict[str, Any]
