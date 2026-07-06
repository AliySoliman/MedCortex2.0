# backend/app/ai/clinical/medical_reasoner.py
# ─────────────────────────────────────────────────────────────────────────────
# Medical Reasoner
# ClinicalReasoningEngine coordinates all clinical intelligence subsystems.
# This is the single entry point into Clinical Intelligence from other layers.
# ─────────────────────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

from app.ai.clinical.diagnosis import SymptomMapper, DifferentialDiagnosisEngine
from app.ai.clinical.risk_engine import RiskEngine
from app.ai.clinical.interaction_checker import InteractionChecker
from app.ai.clinical.contraindication_checker import ContraindicationChecker
from app.ai.clinical.lab_interpreter import StandardLabInterpreter
from app.ai.clinical.recommendation_engine import RecommendationEngine
from app.ai.clinical.evidence_ranker import EvidenceRanker

logger = logging.getLogger(__name__)


class MedicalReasoner(ABC):
    """Abstract base class for medical reasoning engines."""

    @abstractmethod
    def reason(self, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Perform full clinical reasoning on a query."""

    @abstractmethod
    def generate_recommendations(self, patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate clinical recommendations from patient data."""


class ClinicalReasoningEngine(MedicalReasoner):
    """
    Coordinates the full clinical reasoning pipeline:
    1. Symptom extraction
    2. Differential diagnosis
    3. Risk assessment
    4. Drug interaction checking
    5. Contraindication checking
    6. Lab interpretation
    7. Recommendation generation
    """

    def __init__(self) -> None:
        self._symptom_mapper = SymptomMapper()
        self._ddx_engine = DifferentialDiagnosisEngine()
        self._risk_engine = RiskEngine()
        self._interaction_checker = InteractionChecker()
        self._contraindication_checker = ContraindicationChecker()
        self._lab_interpreter = StandardLabInterpreter()
        self._rec_engine = RecommendationEngine()
        self._evidence_ranker = EvidenceRanker()

    def reason(self, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Run the full clinical reasoning pipeline.

        Args:
            context: Serialized UnifiedMedicalContext or patient data dict.
            query: The user's clinical query.

        Returns:
            Dict with all reasoning outputs.
        """
        result: Dict[str, Any] = {}

        # 1. Extract symptoms from query + clinical findings
        symptoms = self._symptom_mapper.map_symptoms(query)
        for finding in context.get("clinical_findings", []):
            extra = self._symptom_mapper.map_symptoms(finding)
            for s in extra:
                if s not in symptoms:
                    symptoms.append(s)
        result["symptoms"] = symptoms

        # 2. Differential diagnosis
        differential = self._ddx_engine.get_differential_diagnosis(symptoms, top_k=5)
        result["differential_diagnoses"] = differential
        diag_names = [d["condition"] for d in differential]

        # 3. Risk assessment
        lab_values = {}
        for lab in context.get("lab_values", []):
            try:
                lab_values[lab.get("name", "")] = float(lab.get("value", 0))
            except (TypeError, ValueError):
                pass

        conditions = [d.get("name", "") for d in context.get("diagnoses", [])]
        risk = self._risk_engine.assess(symptoms, lab_values, diag_names + conditions)
        result["risk_assessment"] = risk.model_dump()

        # 4. Drug interactions
        med_names = [m.get("name", "") for m in context.get("medications", []) if m.get("name")]
        if len(med_names) >= 2:
            interactions = self._interaction_checker.check(med_names)
            result["drug_interactions"] = [i.model_dump() for i in interactions]
        else:
            result["drug_interactions"] = []

        # 5. Contraindications
        if med_names and conditions:
            contras = self._contraindication_checker.check(med_names, conditions)
            result["contraindications"] = [c.model_dump() for c in contras]
        else:
            result["contraindications"] = []

        # 6. Lab interpretation
        if lab_values:
            abnormalities = self._lab_interpreter.identify_abnormalities(lab_values)
            result["lab_abnormalities"] = abnormalities
        else:
            result["lab_abnormalities"] = []

        # 7. Recommendations
        recs = self._rec_engine.generate(
            risk_level=risk.level.value,
            diagnoses=diag_names,
            findings=symptoms,
        )
        result["recommendations"] = [r.model_dump() for r in recs]

        return result

    def generate_recommendations(self, patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate clinical recommendations from patient data dict."""
        risk_level = patient_data.get("risk_level", "LOW")
        diagnoses = patient_data.get("diagnoses", [])
        findings = patient_data.get("symptoms", [])
        recs = self._rec_engine.generate(risk_level, diagnoses, findings)
        return [r.model_dump() for r in recs]


class ClinicalReasoningService:
    """Service layer for clinical reasoning — uses ClinicalReasoningEngine by default."""

    def __init__(self, reasoner: Optional[MedicalReasoner] = None):
        self.reasoner = reasoner or ClinicalReasoningEngine()

    def analyze_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a clinical case and return full reasoning output."""
        query = case_data.get("query", "")
        context = case_data.get("context", {})
        try:
            return self.reasoner.reason(context, query)
        except Exception as exc:
            logger.exception("ClinicalReasoningService failed")
            return {"status": "error", "error": str(exc)}
