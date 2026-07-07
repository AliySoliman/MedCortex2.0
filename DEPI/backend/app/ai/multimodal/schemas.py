# backend/app/ai/multimodal/schemas.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Schemas
# Defines the UnifiedMedicalContext and ProcessingContext
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.ai.multimodal.enums import (
    ModalityType,
    DocumentType,
    ConfidenceLevel,
    PipelineStage,
    ProcessorType,
)


class PipelineMetadata(BaseModel):
    """Metadata regarding the pipeline execution."""
    processing_time_ms: float = 0.0
    provider: Optional[str] = None
    model_name: Optional[str] = None
    version: Optional[str] = None
    fallback_used: bool = False
    warnings: List[str] = Field(default_factory=list)
    history: List[PipelineStage] = Field(default_factory=list)


class ClinicalEntity(BaseModel):
    name: str
    code: Optional[str] = None
    system: Optional[str] = None
    confidence: float = 0.0


class ProviderInformation(BaseModel):
    provider_id: Optional[str] = None
    name: Optional[str] = None
    specialty: Optional[str] = None
    organization: Optional[str] = None
    confidence: float = 0.0


class Medication(ClinicalEntity):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    status: Optional[str] = "active"

class Diagnosis(ClinicalEntity):
    status: Optional[str] = "active"
    severity: Optional[str] = None


class LabValue(ClinicalEntity):
    value: Optional[str | int | float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None # 'H', 'L', 'A' (Abnormal), etc.


class Allergy(ClinicalEntity):
    reaction: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = "active"


class Procedure(ClinicalEntity):
    performed_at: Optional[str] = None
    status: Optional[str] = None


class VitalSign(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None
    recorded_at: Optional[str] = None
    confidence: float = 0.0


class ProcessingHistoryEntry(BaseModel):
    stage: PipelineStage
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    provider: Optional[str] = None
    model_name: Optional[str] = None
    message: Optional[str] = None

class PatientInformation(BaseModel):
    patient_id: Optional[str] = None
    name: Optional[str] = None
    age: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None

class DocumentInformation(BaseModel):
    document_id: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None
    author: Optional[str] = None

class ConfidenceScores(BaseModel):
    overall: float = 0.0
    ocr: Optional[float] = None
    vision: Optional[float] = None
    classification: Optional[float] = None
    parser: Optional[float] = None

class UnifiedMedicalContext(BaseModel):
    """
    The unified context output by the Multimodal Engine.
    Every downstream workflow must consume this object.
    """
    # Core Identity
    upload_id: str
    filename: str
    mime_type: str
    
    # Information Blocks
    patient_information: PatientInformation = Field(default_factory=PatientInformation)
    provider_information: ProviderInformation = Field(default_factory=ProviderInformation)
    document_information: DocumentInformation = Field(default_factory=DocumentInformation)
    
    # Modality & Routing
    classification: DocumentType = DocumentType.UNKNOWN
    modality: ModalityType = ModalityType.UNKNOWN
    classification_confidence: float = 0.0
    ocr_confidence: float = 0.0
    vision_confidence: float = 0.0
    parser_confidence: float = 0.0
    overall_confidence: float = 0.0
    
    # Raw outputs
    ocr_output: Optional[str] = None
    vision_output: Optional[str] = None
    
    # Structured Clinical Data
    structured_entities: Dict[str, Any] = Field(default_factory=dict)
    medications: List[Medication] = Field(default_factory=list)
    diagnoses: List[Diagnosis] = Field(default_factory=list)
    lab_values: List[LabValue] = Field(default_factory=list)
    allergies: List[Allergy] = Field(default_factory=list)
    procedures: List[Procedure] = Field(default_factory=list)
    vital_signs: List[VitalSign] = Field(default_factory=list)
    clinical_findings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Quality & Safety
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    confidence_scores: ConfidenceScores = Field(default_factory=ConfidenceScores)
    warnings: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    processing_history: List[ProcessingHistoryEntry] = Field(default_factory=list)
    
    # Operational Metadata
    processing_metadata: PipelineMetadata = Field(default_factory=PipelineMetadata)
    attachments: List[str] = Field(default_factory=list)


class ProcessingContext(BaseModel):
    """
    Internal context used during the pipeline execution.
    Passed between Orchestrator -> Classifier -> Router -> Preprocessor -> Extractor
    """
    upload_id: str
    filename: str
    mime_type: str
    file_bytes: bytes
    upload_type: str = "document"  # "document" or "medical_image"
    
    modality: ModalityType = ModalityType.UNKNOWN
    document_type: DocumentType = DocumentType.UNKNOWN
    classification_confidence: float = 0.0
    processor_type: ProcessorType = ProcessorType.UNKNOWN
    
    preprocessed_bytes: Optional[bytes] = None
    
    unified_context: UnifiedMedicalContext
