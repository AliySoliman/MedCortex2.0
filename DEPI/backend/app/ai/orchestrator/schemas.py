# backend/app/ai/orchestrator/schemas.py
# ─────────────────────────────────────────────────────────────────────────────
# MedCortex Orchestration Engine Schemas
# ─────────────────────────────────────────────────────────────────────────────

from typing import Optional, List
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Patient profile information for context-aware routing."""
    age: Optional[int] = None
    gender: Optional[str] = None
    known_conditions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)


class ConversationTurn(BaseModel):
    """A single turn in the conversation history."""
    user_message: str
    has_image: bool = False
    image_description: Optional[str] = None


class OrchestratorInput(BaseModel):
    """Input to the MedCortex Orchestration Engine."""
    user_message: str
    has_image: bool = False
    image_description: Optional[str] = None
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    user_profile: UserProfile = Field(default_factory=UserProfile)
    from_audio: bool = False


class OrchestratorOutput(BaseModel):
    """Output from the MedCortex Orchestration Engine."""
    pipelines: List[str]
    primary_pipeline: str
    urgency: str  # "routine" | "soon" | "urgent"
    specialist_hint: Optional[str]
    routing_reason: str
    requires_doctor_finder: bool
    image_type: Optional[str]
