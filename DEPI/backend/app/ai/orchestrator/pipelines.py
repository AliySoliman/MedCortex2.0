# backend/app/ai/orchestrator/pipelines.py
# ─────────────────────────────────────────────────────────────────────────────
# MedCortex Pipeline Constants and Enums
# ─────────────────────────────────────────────────────────────────────────────

from enum import Enum


class Pipeline(str, Enum):
    """Available AI pipelines in MedCortex."""
    RAG = "rag"
    VISION = "vision"
    DRUG_RAG = "drug_rag"
    DOCTOR_FINDER = "doctor_finder"
    LIFESTYLE = "lifestyle"
    WOUND_VISION = "wound_vision"
    STT_PASSTHROUGH = "stt_passthrough"


class Urgency(str, Enum):
    """Clinical urgency levels."""
    ROUTINE = "routine"
    SOON = "soon"
    URGENT = "urgent"


class ImageType(str, Enum):
    """Types of medical images."""
    LAB_REPORT = "lab_report"
    PRESCRIPTION = "prescription"
    WOUND = "wound"
    XRAY = "xray"
    MRI = "mri"
    CT_SCAN = "ct_scan"
    ULTRASOUND = "ultrasound"
    SKIN_LESION = "skin_lesion"
    OTHER_MEDICAL = "other_medical"


# Urgent symptoms that trigger immediate doctor referral
URGENT_SYMPTOMS = {
    "chest pain",
    "chest pressure",
    "heart attack",
    "stroke",
    "difficulty breathing",
    "shortness of breath",
    "severe bleeding",
    "unconscious",
    "fainting",
    "severe headache",
    "sudden vision loss",
    "paralysis",
    "numbness",
    "slurred speech",
    "severe abdominal pain",
    "suicidal",
    "overdose",
    "anaphylaxis",
    "severe allergic reaction",
}

# Soon urgency symptoms
SOON_SYMPTOMS = {
    "fever",
    "infection",
    "wound",
    "cut",
    "burn",
    "rash",
    "skin lesion",
    "broken bone",
    "fracture",
    "sprain",
    "severe pain",
    "persistent pain",
    "vomiting",
    "diarrhea",
    "dehydration",
}

# Drug-related keywords
DRUG_KEYWORDS = {
    "drug",
    "medication",
    "medicine",
    "interaction",
    "interact",
    "side effect",
    "dosage",
    "contraindication",
    "prescription",
    "pill",
    "tablet",
    "capsule",
    "inject",
    "injection",
}

# Lifestyle-related keywords
LIFESTYLE_KEYWORDS = {
    "diet",
    "eat",
    "food",
    "exercise",
    "workout",
    "fitness",
    "sleep",
    "rest",
    "lifestyle",
    "avoid",
    "nutrition",
    "weight",
    "smoking",
    "alcohol",
}

# Doctor/specialist keywords
DOCTOR_KEYWORDS = {
    "doctor",
    "specialist",
    "clinic",
    "hospital",
    "physician",
    "find a doctor",
    "referral",
    "appointment",
}

# Image type keywords mapping
IMAGE_TYPE_KEYWORDS = {
    ImageType.LAB_REPORT: ["lab", "blood test", "cbc", "metabolic", "lipid", "hba1c", "reference range"],
    ImageType.PRESCRIPTION: ["prescription", "medication list", "rx", "pharmacy"],
    ImageType.WOUND: ["wound", "cut", "burn", "injury", "bleeding"],
    ImageType.XRAY: ["xray", "x-ray", "radiograph"],
    ImageType.MRI: ["mri", "magnetic resonance"],
    ImageType.CT_SCAN: ["ct", "cat scan", "computed tomography"],
    ImageType.ULTRASOUND: ["ultrasound", "sonogram"],
    ImageType.SKIN_LESION: ["rash", "lesion", "mole", "spot", "skin condition"],
}
