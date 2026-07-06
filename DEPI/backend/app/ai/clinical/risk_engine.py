# backend/app/ai/clinical/risk_engine.py
# ─────────────────────────────────────────────────────────────────────────────
# Clinical Risk Engine
# Estimates patient risk level from symptoms, lab values, and diagnoses.
# ─────────────────────────────────────────────────────────────────────────────

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAssessment(BaseModel):
    level: RiskLevel
    score: float  # 0.0 - 1.0
    factors: List[str]
    recommendation: str


# Emergency / red-flag symptoms — high weight
RED_FLAG_SYMPTOMS = {
    "chest pain", "chest tightness", "chest pressure",
    "shortness of breath", "difficulty breathing", "trouble breathing",
    "loss of consciousness", "fainting", "syncope",
    "sudden severe headache", "worst headache", "thunderclap headache",
    "stroke", "facial drooping", "arm weakness", "speech difficulty",
    "seizure", "convulsion",
    "severe bleeding", "coughing blood", "vomiting blood",
    "signs of shock", "altered mental status", "confusion",
    "anaphylaxis", "throat swelling", "severe allergic reaction",
    "severe abdominal pain",
}

# Moderate risk symptoms
MODERATE_RISK_SYMPTOMS = {
    "fever above 39", "high fever", "persistent fever",
    "severe pain", "unbearable pain", "intense pain",
    "back pain", "lower back pain",
    "numbness", "tingling", "weakness",
    "vomiting", "repeated vomiting",
    "diarrhea", "bloody stool",
    "urinary burning", "painful urination",
    "palpitations", "irregular heartbeat",
    "swelling", "edema",
    "rash", "skin rash",
    "dizziness", "vertigo",
}

# High-risk diagnoses
HIGH_RISK_DIAGNOSES = {
    "myocardial infarction", "heart attack", "cardiac arrest",
    "stroke", "pulmonary embolism", "deep vein thrombosis",
    "sepsis", "meningitis", "encephalitis",
    "pneumonia", "respiratory failure",
    "diabetic ketoacidosis", "dka",
    "acute kidney injury", "acute renal failure",
    "liver failure",
    "cancer", "malignancy", "tumor",
}


class RiskEngine:
    """
    Estimates clinical risk from a combination of symptoms, lab values, and diagnoses.
    Uses a weighted scoring system (deterministic, no LLM).
    """

    def assess(
        self,
        symptoms: List[str],
        lab_values: Dict[str, Any],
        diagnoses: List[str],
    ) -> RiskAssessment:
        """
        Compute a RiskAssessment for the patient.

        Args:
            symptoms: List of symptom strings.
            lab_values: Dict of {test_name: numeric_value}.
            diagnoses: List of suspected or confirmed diagnosis strings.

        Returns:
            RiskAssessment with level, score, factors, and recommendation.
        """
        score = 0.0
        factors: List[str] = []

        # Check red flag symptoms (weight: 0.4 each, capped)
        red_flags = self.get_red_flags(symptoms)
        for flag in red_flags:
            score += 0.4
            factors.append(f"Red flag symptom: {flag}")
        score = min(score, 0.8)

        # Check moderate risk symptoms (weight: 0.1 each, capped at 0.3)
        moderate_score = 0.0
        for sym in symptoms:
            sym_lower = sym.lower()
            if any(ms in sym_lower for ms in MODERATE_RISK_SYMPTOMS):
                moderate_score += 0.1
                factors.append(f"Concerning symptom: {sym}")
        score += min(moderate_score, 0.3)

        # Check diagnoses (weight: 0.3 each, capped)
        for dx in diagnoses:
            dx_lower = dx.lower()
            if any(hrd in dx_lower for hrd in HIGH_RISK_DIAGNOSES):
                score += 0.3
                factors.append(f"High-risk diagnosis: {dx}")
        score = min(score, 1.0)

        # Check critical lab values (weight: 0.35)
        critical_labs = self._check_critical_labs(lab_values)
        for lab_flag in critical_labs:
            score = min(score + 0.35, 1.0)
            factors.append(f"Critical lab: {lab_flag}")

        # Determine level
        if score >= 0.75 or red_flags or critical_labs:
            level = RiskLevel.CRITICAL
            recommendation = (
                "URGENT: Patient has critical risk indicators. "
                "Seek immediate emergency care or call emergency services."
            )
        elif score >= 0.5:
            level = RiskLevel.HIGH
            recommendation = (
                "HIGH RISK: Prompt medical evaluation recommended. "
                "Contact a healthcare provider today."
            )
        elif score >= 0.25:
            level = RiskLevel.MODERATE
            recommendation = (
                "MODERATE RISK: Schedule medical appointment soon. "
                "Monitor symptoms and seek care if worsening."
            )
        else:
            level = RiskLevel.LOW
            recommendation = (
                "LOW RISK: Continue monitoring. "
                "Maintain healthy lifestyle habits and routine check-ups."
            )

        return RiskAssessment(
            level=level,
            score=round(min(score, 1.0), 3),
            factors=factors,
            recommendation=recommendation,
        )

    def get_red_flags(self, symptoms: List[str]) -> List[str]:
        """Return list of emergency red-flag symptoms found in the symptom list."""
        found = []
        for sym in symptoms:
            sym_lower = sym.lower()
            if any(rf in sym_lower for rf in RED_FLAG_SYMPTOMS):
                found.append(sym)
        return found

    def _check_critical_labs(self, lab_values: Dict[str, Any]) -> List[str]:
        """Check for critical lab values using known critical thresholds."""
        from app.ai.clinical.lab_interpreter import resolve_reference_range
        critical: List[str] = []
        for name, raw_value in lab_values.items():
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue
            _, ref = resolve_reference_range(name)
            if not ref:
                continue
            crit_low = ref.get("critical_low")
            crit_high = ref.get("critical_high")
            if crit_high is not None and value >= crit_high:
                critical.append(f"{name}={value} (CRITICAL HIGH >{crit_high})")
            elif crit_low is not None and value <= crit_low:
                critical.append(f"{name}={value} (CRITICAL LOW <{crit_low})")
        return critical
