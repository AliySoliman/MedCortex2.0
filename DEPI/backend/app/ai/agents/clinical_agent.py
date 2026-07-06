# backend/app/ai/agents/clinical_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# Clinical Reasoning Agent
# Coordinates clinical intelligence subsystems: symptom extraction,
# differential diagnosis, risk assessment, drug interactions, lab interpretation.
# ─────────────────────────────────────────────────────────────────────────────

import time
import logging
from typing import Optional

from app.ai.agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


class ClinicalReasoningAgent(BaseAgent):
    """
    Orchestrates the Clinical Intelligence subsystem.

    Reads the query and unified_context from AgentContext,
    runs clinical reasoning, and writes findings back to context:
        - extracted_symptoms
        - differential_diagnoses
        - risk_assessment
        - drug_interactions
        - lab_interpretations
        - recommendations
    """

    def __init__(self) -> None:
        super().__init__(name="clinical_reasoning_agent")

    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the clinical reasoning pipeline."""
        start = time.monotonic()
        self._trace(context, "Starting clinical reasoning pipeline.")

        try:
            unified_context = _normalize_context(context.unified_context)

            # ── Symptom Extraction ────────────────────────────────────────────
            from app.ai.clinical.diagnosis import SymptomMapper, DifferentialDiagnosisEngine
            mapper = SymptomMapper()
            symptoms = mapper.map_symptoms(context.query)
            context.extracted_symptoms = symptoms
            self._trace(context, f"Extracted {len(symptoms)} symptoms: {symptoms}")

            # Also extract from clinical findings in unified_context if present
            if unified_context:
                uc_findings = unified_context.get("clinical_findings", [])
                for finding in uc_findings:
                    extra = mapper.map_symptoms(finding)
                    for s in extra:
                        if s not in context.extracted_symptoms:
                            context.extracted_symptoms.append(s)

            # ── Differential Diagnosis ────────────────────────────────────────
            ddx_engine = DifferentialDiagnosisEngine()
            differential = ddx_engine.get_differential_diagnosis(context.extracted_symptoms, top_k=5)
            context.differential_diagnoses = differential
            self._trace(context, f"Generated {len(differential)} differential diagnoses.")

            # ── Risk Assessment ───────────────────────────────────────────────
            from app.ai.clinical.risk_engine import RiskEngine
            risk_engine = RiskEngine()
            lab_values = {}
            if unified_context:
                raw_labs = unified_context.get("lab_values", [])
                lab_values = {lv.get("name", ""): lv.get("value", "") for lv in raw_labs}

            diag_names = [d.get("condition", "") for d in differential]
            risk_assessment = risk_engine.assess(
                symptoms=context.extracted_symptoms,
                lab_values=lab_values,
                diagnoses=diag_names,
            )
            context.risk_assessment = risk_assessment.model_dump()
            self._trace(context, f"Risk level: {risk_assessment.level.value}")

            # ── Drug Interactions ─────────────────────────────────────────────
            if unified_context:
                meds_raw = unified_context.get("medications", [])
                med_names = [m.get("name", "") for m in meds_raw if m.get("name")]

                if len(med_names) >= 2:
                    from app.ai.clinical.interaction_checker import InteractionChecker
                    checker = InteractionChecker()
                    interactions = checker.check(med_names)
                    context.drug_interactions = [i.model_dump() for i in interactions]
                    self._trace(context, f"Found {len(interactions)} drug interactions.")

            # ── Lab Interpretation ────────────────────────────────────────────
            if lab_values:
                from app.ai.clinical.lab_interpreter import StandardLabInterpreter
                interpreter = StandardLabInterpreter()
                abnormalities = interpreter.identify_abnormalities(
                    {k: float(v) for k, v in lab_values.items() if _is_numeric(v)}
                )
                context.lab_interpretations = abnormalities
                self._trace(context, f"Identified {len(abnormalities)} lab abnormalities.")

            # ── Recommendations ───────────────────────────────────────────────
            from app.ai.clinical.recommendation_engine import RecommendationEngine
            rec_engine = RecommendationEngine()
            recs = rec_engine.generate(
                risk_level=risk_assessment.level.value,
                diagnoses=diag_names,
                findings=context.extracted_symptoms,
            )
            context.recommendations = [r.model_dump() for r in recs]
            context.clinical_findings = {
                "symptoms": context.extracted_symptoms,
                "differential_diagnoses": context.differential_diagnoses,
                "risk_assessment": context.risk_assessment,
                "drug_interactions": context.drug_interactions,
                "lab_interpretations": context.lab_interpretations,
                "recommendations": context.recommendations,
            }
            self._trace(context, f"Generated {len(recs)} recommendations.")

            duration_ms = (time.monotonic() - start) * 1000
            return self._success(
                context,
                output={
                    "symptoms": context.extracted_symptoms,
                    "diagnoses_count": len(differential),
                    "risk_level": risk_assessment.level.value,
                    "interactions_count": len(context.drug_interactions),
                },
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            logger.exception("ClinicalReasoningAgent failed")
            return self._failure(context, error=str(exc), duration_ms=duration_ms)


def _is_numeric(value: str) -> bool:
    """Check if a string can be parsed as a float."""
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _normalize_context(value: Optional[object]) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {}
