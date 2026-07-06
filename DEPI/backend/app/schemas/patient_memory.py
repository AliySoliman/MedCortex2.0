# backend/app/schemas/patient_memory.py
# ─────────────────────────────────────────────────────────────────────────────
# Longitudinal Patient Memory Schemas
# Pydantic models for patient memory, clinical memory, and timelines.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MedicationHistoryEntry(BaseModel):
    """A single medication record in a patient's longitudinal history."""
    medication_name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    status: str = "active"  # active | discontinued | completed
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None


class AllergyEntry(BaseModel):
    """A recorded patient allergy."""
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = None  # mild | moderate | severe | anaphylaxis
    reported_at: Optional[str] = None
    confirmed: bool = False


class LabHistoryEntry(BaseModel):
    """A single lab result stored in the patient's longitudinal lab history."""
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None  # H | L | A | CRITICAL
    performed_at: Optional[str] = None
    source: Optional[str] = None  # e.g. 'lab_report_upload'


class DiagnosisHistoryEntry(BaseModel):
    """A recorded diagnosis in the patient's history."""
    condition: str
    icd10_code: Optional[str] = None
    status: str = "active"  # active | resolved | chronic | suspected
    diagnosed_at: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None


class ClinicalTimelineEvent(BaseModel):
    """A single event on the patient's clinical timeline."""
    event_type: str  # diagnosis | medication_started | lab_result | visit | upload
    description: str
    date: Optional[str] = None
    source: str  # e.g. 'chat', 'upload', 'api'
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PatientMemory(BaseModel):
    """
    Complete longitudinal patient memory record.
    Populated and updated across sessions by the MemoryAgent.
    """
    patient_id: str
    user_id: str

    # Active Medications
    medications: List[MedicationHistoryEntry] = Field(default_factory=list)

    # Allergies
    allergies: List[AllergyEntry] = Field(default_factory=list)

    # Lab History
    lab_history: List[LabHistoryEntry] = Field(default_factory=list)

    # Diagnosis History
    diagnoses: List[DiagnosisHistoryEntry] = Field(default_factory=list)

    # Timeline
    timeline: List[ClinicalTimelineEvent] = Field(default_factory=list)

    # Archive of uploaded report IDs
    report_archive: List[str] = Field(default_factory=list)

    # Free-text clinical summary (LLM-generated)
    clinical_summary: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ClinicalMemory(BaseModel):
    """
    Clinical session memory — tracks per-session clinical reasoning.
    Separate from PatientMemory (which is longitudinal).
    """
    session_id: str
    user_id: str

    # Extracted in this session
    extracted_symptoms: List[str] = Field(default_factory=list)
    differential_diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    risk_assessment: Optional[Dict[str, Any]] = None
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)

    # Conversation context
    query_count: int = 0
    last_query: Optional[str] = None
    session_summary: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
