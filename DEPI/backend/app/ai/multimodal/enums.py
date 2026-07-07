# backend/app/ai/multimodal/enums.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Enums
# Defines input types, document types, and pipeline statuses
# ─────────────────────────────────────────────────────────────────────────────

from enum import Enum


class ModalityType(str, Enum):
    """The high-level modality of the input."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class DocumentType(str, Enum):
    """Specific document types supported by the system."""
    PRESCRIPTION = "Prescription"
    LAB_REPORT = "Laboratory Report"
    REFERRAL = "Referral Letter"
    INSURANCE = "Insurance Form"
    DISCHARGE_SUMMARY = "Discharge Summary"
    RADIOLOGY_REPORT = "Radiology Report"
    ECG = "ECG"
    SKIN_IMAGE = "Skin Image"
    EYE_IMAGE = "Eye Image"
    WOUND = "WOUND"
    XRAY = "X-Ray"
    CT_SCAN = "CT Scan"
    MRI = "MRI"
    ULTRASOUND = "Ultrasound"
    UNKNOWN = "Unknown"


class PipelineStage(str, Enum):
    """Stages of the Multimodal pipeline."""
    UPLOAD_RECEIVED = "UPLOAD_RECEIVED"
    UPLOAD_VALIDATED = "UPLOAD_VALIDATED"
    CLASSIFICATION_STARTED = "CLASSIFICATION_STARTED"
    CLASSIFICATION_COMPLETED = "CLASSIFICATION_COMPLETED"
    PREPROCESSING_STARTED = "PREPROCESSING_STARTED"
    PREPROCESSING_COMPLETED = "PREPROCESSING_COMPLETED"
    OCR_STARTED = "OCR_STARTED"
    OCR_COMPLETED = "OCR_COMPLETED"
    VISION_STARTED = "VISION_STARTED"
    VISION_COMPLETED = "VISION_COMPLETED"
    PARSER_STARTED = "PARSER_STARTED"
    PARSER_COMPLETED = "PARSER_COMPLETED"
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    REPORT_GENERATED = "REPORT_GENERATED"
    PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
    PIPELINE_FAILED = "PIPELINE_FAILED"


class ConfidenceLevel(str, Enum):
    """Categorized confidence levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ProcessorType(str, Enum):
    """Available processors for routing."""
    OCR = "OCR"
    VISION = "VISION"
    TEXT = "TEXT"
    MEDICAL_IMAGE = "MEDICAL_IMAGE"
    UNKNOWN = "UNKNOWN"
