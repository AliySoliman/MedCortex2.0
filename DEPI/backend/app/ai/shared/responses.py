# backend/app/ai/shared/responses.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared Response Models
# Standard AI response schema for all workflows
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class AIResponse(BaseModel):
    """
    Standard AI response model.
    
    Every future workflow must return this format.
    """
    success: bool = Field(..., description="Whether the operation succeeded")
    workflow: str = Field(..., description="Name of the workflow executed")
    provider: str = Field(default="groq", description="AI provider used")
    model: str = Field(..., description="Model used for the task")
    execution_time: float = Field(..., description="Execution time in seconds")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations for sources")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    data: Dict[str, Any] = Field(default_factory=dict, description="Primary response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "workflow": "chat",
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "execution_time": 1.5,
                "confidence": 0.85,
                "citations": [],
                "metadata": {},
                "data": {"answer": "Sample response"},
                "error": None,
            }
        }


class ChatResponse(AIResponse):
    """Response model for chat workflows."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chat-specific data including answer, symptoms, conditions"
    )


class VisionResponse(AIResponse):
    """Response model for vision workflows."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Vision-specific data including analysis results"
    )


class DiagnosisResponse(AIResponse):
    """Response model for diagnosis workflows."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnosis-specific data including conditions and confidence"
    )


class PrescriptionResponse(AIResponse):
    """Response model for prescription workflows."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Prescription-specific data including interactions and warnings"
    )


class LabResponse(AIResponse):
    """Response model for lab workflows."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Lab-specific data including interpretations and abnormalities"
    )


class ReportResponse(AIResponse):
    """Response model for report workflows."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Report-specific data including generated content"
    )
