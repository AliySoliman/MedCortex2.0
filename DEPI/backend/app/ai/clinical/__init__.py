# backend/app/ai/clinical/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Clinical Module
# Clinical decision support and medical reasoning
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.clinical.lifestyle import get_lifestyle_recommendations
from app.ai.clinical.doctor_finder import find_doctors
from app.ai.clinical.diagnosis import DiagnosisEngine, DiagnosisService
from app.ai.clinical.drug_checker import DrugChecker, DrugInteractionService
from app.ai.clinical.lab_interpreter import LabInterpreter, LabInterpretationService
from app.ai.clinical.medical_reasoner import MedicalReasoner, ClinicalReasoningService
from app.ai.clinical.calculator_engine import CalculatorEngine, MedicalCalculatorService

__all__ = [
    "get_lifestyle_recommendations",
    "find_doctors",
    "DiagnosisEngine",
    "DiagnosisService",
    "DrugChecker",
    "DrugInteractionService",
    "LabInterpreter",
    "LabInterpretationService",
    "MedicalReasoner",
    "ClinicalReasoningService",
    "CalculatorEngine",
    "MedicalCalculatorService",
]
