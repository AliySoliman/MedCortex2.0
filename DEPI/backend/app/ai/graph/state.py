# backend/app/ai/graph/state.py
# ─────────────────────────────────────────────────────────────────────────────
# Graph State
# State management for LangGraph workflows
# ─────────────────────────────────────────────────────────────────────────────

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from app.ai.multimodal.schemas import UnifiedMedicalContext, ProcessingContext
from app.ai.multimodal.enums import ProcessorType


class GraphState(TypedDict):
    """Base state for all AI workflow graphs."""
    
    # Input
    user_message: str
    user_id: Optional[str]
    unified_context: Optional[UnifiedMedicalContext]
    
    # Processing
    symptoms: List[str]
    suspected_conditions: List[str]
    
    # RAG
    rag_answer: str
    retrieved_context: List[Dict[str, Any]]
    
    # Clinical
    lifestyle_recommendations: Dict[str, Any]
    doctor_specialties: List[str]
    
    # Output
    doctors: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    
    # Metadata
    execution_time: float
    confidence: float
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ChatState(GraphState):
    """State for chat workflows."""
    conversation_history: List[Dict[str, str]]
    memory_summary: Optional[str]


class VisionState(GraphState):
    """State for vision/image analysis workflows."""
    image_data: bytes
    image_type: str
    ocr_results: Optional[Dict[str, Any]]
    image_features: Optional[List[float]]


class DiagnosisState(GraphState):
    """State for diagnosis workflows."""
    patient_data: Optional[Dict[str, Any]]
    lab_results: Optional[List[Dict[str, Any]]]
    medical_history: Optional[List[str]]


class PrescriptionState(GraphState):
    """State for prescription analysis workflows."""
    prescription_text: str
    drug_interactions: List[Dict[str, Any]]
    dosage_analysis: Dict[str, Any]


class LabState(GraphState):
    """State for lab interpretation workflows."""
    lab_values: Dict[str, Any]
    reference_ranges: Dict[str, Any]
    abnormalities: List[Dict[str, Any]]


class ReportState(GraphState):
    """State for report generation workflows."""
    report_type: str
    template_data: Dict[str, Any]
    generated_report: Optional[str]


class MultimodalPipelineState(TypedDict, total=False):
    """
    State for the multimodal upload execution graph.

    The graph receives a fully classified + preprocessed ProcessingContext
    (produced by MultimodalOrchestrator) and executes the appropriate
    extraction / enrichment nodes based on `processor` and document type.
    All nodes mutate the shared `context` in place.
    """

    # Input / shared mutable payload
    context: ProcessingContext

    # Routing decision (mirrors context.processor_type for conditional edges)
    processor: ProcessorType

    # Optional enrichment flags resolved during execution
    needs_lab_interpretation: bool
    needs_drug_interaction: bool

    # Error capture (non-fatal: graph continues to finalize)
    error: Optional[str]

    # Operational metadata
    metadata: Dict[str, Any]
