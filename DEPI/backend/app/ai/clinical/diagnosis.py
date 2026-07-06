# backend/app/ai/clinical/diagnosis.py
# ─────────────────────────────────────────────────────────────────────────────
# Diagnosis Engine
# Differential diagnosis generation from symptoms using an evidence-based map.
# ─────────────────────────────────────────────────────────────────────────────

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DifferentialResult(BaseModel):
    condition: str
    confidence: float
    matching_symptoms: List[str]
    icd10_hint: Optional[str] = None


# Symptom -> possible conditions mapping (evidence-informed)
SYMPTOM_CONDITION_MAP: Dict[str, List[Dict[str, Any]]] = {
    "chest pain": [
        {"condition": "Myocardial Infarction", "weight": 0.9, "icd10": "I21"},
        {"condition": "Angina Pectoris", "weight": 0.7, "icd10": "I20"},
        {"condition": "GERD", "weight": 0.5, "icd10": "K21"},
        {"condition": "Costochondritis", "weight": 0.4, "icd10": "M94.0"},
        {"condition": "Pulmonary Embolism", "weight": 0.6, "icd10": "I26"},
    ],
    "shortness of breath": [
        {"condition": "Asthma", "weight": 0.7, "icd10": "J45"},
        {"condition": "Heart Failure", "weight": 0.7, "icd10": "I50"},
        {"condition": "Pulmonary Embolism", "weight": 0.6, "icd10": "I26"},
        {"condition": "COPD", "weight": 0.7, "icd10": "J44"},
        {"condition": "Pneumonia", "weight": 0.6, "icd10": "J18"},
        {"condition": "Anxiety", "weight": 0.5, "icd10": "F41"},
    ],
    "fever": [
        {"condition": "Viral Upper Respiratory Infection", "weight": 0.7, "icd10": "J06"},
        {"condition": "Influenza", "weight": 0.7, "icd10": "J10"},
        {"condition": "Pneumonia", "weight": 0.6, "icd10": "J18"},
        {"condition": "Urinary Tract Infection", "weight": 0.5, "icd10": "N39.0"},
        {"condition": "Sepsis", "weight": 0.5, "icd10": "A41"},
    ],
    "headache": [
        {"condition": "Tension Headache", "weight": 0.8, "icd10": "G44.2"},
        {"condition": "Migraine", "weight": 0.7, "icd10": "G43"},
        {"condition": "Hypertensive Headache", "weight": 0.5, "icd10": "R51"},
        {"condition": "Meningitis", "weight": 0.3, "icd10": "G03"},
        {"condition": "Subarachnoid Hemorrhage", "weight": 0.2, "icd10": "I60"},
    ],
    "cough": [
        {"condition": "Viral Upper Respiratory Infection", "weight": 0.8, "icd10": "J06"},
        {"condition": "Asthma", "weight": 0.6, "icd10": "J45"},
        {"condition": "GERD", "weight": 0.5, "icd10": "K21"},
        {"condition": "Pneumonia", "weight": 0.5, "icd10": "J18"},
        {"condition": "COPD", "weight": 0.5, "icd10": "J44"},
        {"condition": "Bronchitis", "weight": 0.6, "icd10": "J40"},
    ],
    "abdominal pain": [
        {"condition": "Irritable Bowel Syndrome", "weight": 0.6, "icd10": "K58"},
        {"condition": "Peptic Ulcer Disease", "weight": 0.5, "icd10": "K27"},
        {"condition": "Appendicitis", "weight": 0.4, "icd10": "K37"},
        {"condition": "Gastroenteritis", "weight": 0.6, "icd10": "K52"},
        {"condition": "Cholecystitis", "weight": 0.4, "icd10": "K81"},
        {"condition": "GERD", "weight": 0.5, "icd10": "K21"},
    ],
    "nausea": [
        {"condition": "Gastroenteritis", "weight": 0.7, "icd10": "K52"},
        {"condition": "Peptic Ulcer Disease", "weight": 0.5, "icd10": "K27"},
        {"condition": "Migraine", "weight": 0.5, "icd10": "G43"},
        {"condition": "Pregnancy", "weight": 0.4, "icd10": "O21"},
        {"condition": "Medication Side Effect", "weight": 0.4, "icd10": "T88.7"},
    ],
    "fatigue": [
        {"condition": "Anemia", "weight": 0.6, "icd10": "D64"},
        {"condition": "Hypothyroidism", "weight": 0.5, "icd10": "E03"},
        {"condition": "Depression", "weight": 0.5, "icd10": "F32"},
        {"condition": "Diabetes Mellitus", "weight": 0.4, "icd10": "E11"},
        {"condition": "Sleep Apnea", "weight": 0.5, "icd10": "G47.3"},
    ],
    "dizziness": [
        {"condition": "Benign Paroxysmal Positional Vertigo", "weight": 0.6, "icd10": "H81.1"},
        {"condition": "Orthostatic Hypotension", "weight": 0.5, "icd10": "I95.1"},
        {"condition": "Meniere's Disease", "weight": 0.4, "icd10": "H81.0"},
        {"condition": "Anemia", "weight": 0.4, "icd10": "D64"},
        {"condition": "Hypoglycemia", "weight": 0.4, "icd10": "E16.0"},
    ],
    "back pain": [
        {"condition": "Lumbar Muscle Strain", "weight": 0.7, "icd10": "S39.0"},
        {"condition": "Lumbar Disc Herniation", "weight": 0.6, "icd10": "M51.1"},
        {"condition": "Lumbar Spondylosis", "weight": 0.5, "icd10": "M47.8"},
        {"condition": "Kidney Stone", "weight": 0.3, "icd10": "N20"},
        {"condition": "Osteoporosis", "weight": 0.3, "icd10": "M81"},
    ],
    "joint pain": [
        {"condition": "Osteoarthritis", "weight": 0.7, "icd10": "M19"},
        {"condition": "Rheumatoid Arthritis", "weight": 0.5, "icd10": "M06"},
        {"condition": "Gout", "weight": 0.5, "icd10": "M10"},
        {"condition": "Reactive Arthritis", "weight": 0.3, "icd10": "M02"},
    ],
    "palpitations": [
        {"condition": "Atrial Fibrillation", "weight": 0.6, "icd10": "I48"},
        {"condition": "Supraventricular Tachycardia", "weight": 0.5, "icd10": "I47.1"},
        {"condition": "Anxiety", "weight": 0.6, "icd10": "F41"},
        {"condition": "Hyperthyroidism", "weight": 0.4, "icd10": "E05"},
        {"condition": "Anemia", "weight": 0.3, "icd10": "D64"},
    ],
    "rash": [
        {"condition": "Contact Dermatitis", "weight": 0.6, "icd10": "L23"},
        {"condition": "Eczema", "weight": 0.6, "icd10": "L20"},
        {"condition": "Psoriasis", "weight": 0.5, "icd10": "L40"},
        {"condition": "Drug Reaction", "weight": 0.4, "icd10": "L27"},
        {"condition": "Urticaria", "weight": 0.5, "icd10": "L50"},
    ],
    "urinary burning": [
        {"condition": "Urinary Tract Infection", "weight": 0.8, "icd10": "N39.0"},
        {"condition": "Urethritis", "weight": 0.5, "icd10": "N34"},
        {"condition": "Kidney Stone", "weight": 0.3, "icd10": "N20"},
    ],
    "swelling": [
        {"condition": "Heart Failure", "weight": 0.5, "icd10": "I50"},
        {"condition": "Deep Vein Thrombosis", "weight": 0.5, "icd10": "I82"},
        {"condition": "Cellulitis", "weight": 0.4, "icd10": "L03"},
        {"condition": "Lymphedema", "weight": 0.3, "icd10": "I89.0"},
    ],
    "weight loss": [
        {"condition": "Diabetes Mellitus", "weight": 0.5, "icd10": "E11"},
        {"condition": "Hyperthyroidism", "weight": 0.5, "icd10": "E05"},
        {"condition": "Malignancy", "weight": 0.4, "icd10": "C80"},
        {"condition": "Crohn's Disease", "weight": 0.3, "icd10": "K50"},
    ],
    "numbness": [
        {"condition": "Peripheral Neuropathy", "weight": 0.6, "icd10": "G60"},
        {"condition": "Carpal Tunnel Syndrome", "weight": 0.5, "icd10": "G56.0"},
        {"condition": "Lumbar Disc Herniation", "weight": 0.4, "icd10": "M51.1"},
        {"condition": "Stroke", "weight": 0.3, "icd10": "I63"},
        {"condition": "Multiple Sclerosis", "weight": 0.2, "icd10": "G35"},
    ],
}

# Common symptom terms for extraction
_SYMPTOM_TERMS = sorted(SYMPTOM_CONDITION_MAP.keys(), key=len, reverse=True) + [
    "pain", "ache", "hurt", "sore", "burning", "bleeding", "vomiting",
    "weakness", "tired", "insomnia", "anxiety", "depression", "tremor",
    "confusion", "loss of appetite",
]


class SymptomMapper:
    """Extracts symptom terms from free-form clinical text using regex matching."""

    def map_symptoms(self, text: str) -> List[str]:
        """
        Extract symptom strings from natural language text.

        Args:
            text: User query or clinical note text.

        Returns:
            List of identified symptom strings (deduplicated, lowercased).
        """
        if not text:
            return []
        text_lower = text.lower()
        found: List[str] = []
        seen: set = set()

        for term in _SYMPTOM_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", text_lower):
                if term not in seen:
                    found.append(term)
                    seen.add(term)
        return found


class DiagnosisEngine(ABC):
    """Abstract base class for diagnosis engines."""

    @abstractmethod
    def diagnose(
        self,
        symptoms: List[str],
        patient_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_differential_diagnosis(
        self,
        symptoms: List[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        pass


class DifferentialDiagnosisEngine(DiagnosisEngine):
    """
    Generates differential diagnoses by scoring conditions against symptom overlap.
    Deterministic — no LLM dependency.
    """

    def diagnose(
        self,
        symptoms: List[str],
        patient_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        differential = self.get_differential_diagnosis(symptoms, top_k=5)
        return {
            "symptoms_analyzed": symptoms,
            "differential_diagnoses": differential,
            "top_diagnosis": differential[0] if differential else None,
        }

    def get_differential_diagnosis(
        self,
        symptoms: List[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rank conditions by how many provided symptoms they match, weighted by confidence.

        Returns:
            List of {condition, confidence, matching_symptoms, icd10_hint} dicts.
        """
        condition_scores: Dict[str, Dict[str, Any]] = {}

        for symptom in symptoms:
            sym_lower = symptom.lower().strip()
            for mapped_symptom, conditions in SYMPTOM_CONDITION_MAP.items():
                if mapped_symptom in sym_lower or sym_lower in mapped_symptom:
                    for cond_data in conditions:
                        cname = cond_data["condition"]
                        if cname not in condition_scores:
                            condition_scores[cname] = {
                                "condition": cname,
                                "score": 0.0,
                                "matching_symptoms": [],
                                "icd10_hint": cond_data.get("icd10"),
                            }
                        condition_scores[cname]["score"] += cond_data["weight"]
                        if symptom not in condition_scores[cname]["matching_symptoms"]:
                            condition_scores[cname]["matching_symptoms"].append(symptom)

        # Normalize scores to 0-1 confidence
        max_score = max((v["score"] for v in condition_scores.values()), default=1.0)
        results = []
        for cname, data in condition_scores.items():
            results.append({
                "condition": cname,
                "confidence": round(min(data["score"] / max_score, 1.0), 3),
                "matching_symptoms": data["matching_symptoms"],
                "icd10_hint": data["icd10_hint"],
            })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:top_k]


class DiagnosisService:
    """Service for medical diagnosis operations — uses DifferentialDiagnosisEngine by default."""

    def __init__(self, engine: Optional[DiagnosisEngine] = None):
        self.engine = engine or DifferentialDiagnosisEngine()

    def analyze_symptoms(
        self,
        symptoms: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze symptoms and return differential diagnoses."""
        return self.engine.diagnose(symptoms, patient_data=context)
