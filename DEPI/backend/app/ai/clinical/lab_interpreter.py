# backend/app/ai/clinical/lab_interpreter.py
# ─────────────────────────────────────────────────────────────────────────────
# Lab Interpreter
# Interprets laboratory values against evidence-based reference ranges.
# ─────────────────────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class LabResult(BaseModel):
    """Interpreted laboratory result."""
    name: str
    value: float
    unit: str
    flag: str  # NORMAL | HIGH | LOW | CRITICAL_HIGH | CRITICAL_LOW
    reference_min: float
    reference_max: float
    clinical_significance: str


# Reference ranges: {test_name: {min, max, unit, critical_low, critical_high}}
REFERENCE_RANGES: Dict[str, Dict[str, Any]] = {
    "glucose": {"min": 70, "max": 99, "unit": "mg/dL", "critical_low": 40, "critical_high": 500, "fasting": True},
    "hba1c": {"min": 4.0, "max": 5.6, "unit": "%", "critical_low": None, "critical_high": 14.0},
    "creatinine": {"min": 0.7, "max": 1.3, "unit": "mg/dL", "critical_low": None, "critical_high": 10.0},
    "bun": {"min": 7, "max": 20, "unit": "mg/dL", "critical_low": None, "critical_high": 100},
    "bun/creatinine ratio": {"min": 6, "max": 20, "unit": "", "critical_low": None, "critical_high": 40},
    "sodium": {"min": 136, "max": 145, "unit": "mEq/L", "critical_low": 120, "critical_high": 160},
    "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L", "critical_low": 2.5, "critical_high": 6.5},
    "chloride": {"min": 98, "max": 107, "unit": "mEq/L", "critical_low": 80, "critical_high": 120},
    "bicarbonate": {"min": 22, "max": 29, "unit": "mEq/L", "critical_low": 10, "critical_high": 40},
    "calcium": {"min": 8.5, "max": 10.2, "unit": "mg/dL", "critical_low": 6.0, "critical_high": 13.0},
    "magnesium": {"min": 1.7, "max": 2.2, "unit": "mg/dL", "critical_low": 1.0, "critical_high": 4.9},
    "total cholesterol": {"min": 0, "max": 200, "unit": "mg/dL", "critical_low": None, "critical_high": 240},
    "triglycerides": {"min": 30, "max": 150, "unit": "mg/dL", "critical_low": None, "critical_high": 500},
    "hdl cholesterol": {"min": 40, "max": 80, "unit": "mg/dL", "critical_low": 35, "critical_high": None},
    "ldl cholesterol": {"min": 0, "max": 130, "unit": "mg/dL", "critical_low": None, "critical_high": 190},
    "vldl cholesterol": {"min": 5, "max": 40, "unit": "mg/dL", "critical_low": None, "critical_high": 60},
    "cholesterol hdl ratio": {"min": 0, "max": 3.5, "unit": "", "critical_low": None, "critical_high": 6.0},
    "risk ratio": {"min": 0, "max": 3.5, "unit": "", "critical_low": None, "critical_high": 6.0},
    "wbc": {"min": 4.5, "max": 11.0, "unit": "x10^3/uL", "critical_low": 2.0, "critical_high": 30.0},
    "rbc": {"min": 4.2, "max": 5.8, "unit": "x10^6/uL", "critical_low": 2.0, "critical_high": None},
    "hemoglobin": {"min": 13.5, "max": 17.5, "unit": "g/dL", "critical_low": 7.0, "critical_high": 20.0},
    "hematocrit": {"min": 41, "max": 53, "unit": "%", "critical_low": 20, "critical_high": 60},
    "mcv": {"min": 80, "max": 100, "unit": "fL", "critical_low": None, "critical_high": None},
    "mch": {"min": 27, "max": 33, "unit": "pg", "critical_low": None, "critical_high": None},
    "mchc": {"min": 32, "max": 36, "unit": "g/dL", "critical_low": None, "critical_high": None},
    "platelets": {"min": 150, "max": 400, "unit": "x10^3/uL", "critical_low": 50, "critical_high": 1000},
    "tsh": {"min": 0.4, "max": 4.0, "unit": "mIU/L", "critical_low": 0.01, "critical_high": 10.0},
    "t4": {"min": 0.8, "max": 1.8, "unit": "ng/dL", "critical_low": None, "critical_high": None},
    "alt": {"min": 7, "max": 56, "unit": "U/L", "critical_low": None, "critical_high": 200},
    "ast": {"min": 10, "max": 40, "unit": "U/L", "critical_low": None, "critical_high": 200},
    "alp": {"min": 44, "max": 147, "unit": "U/L", "critical_low": None, "critical_high": 500},
    "total bilirubin": {"min": 0.1, "max": 1.2, "unit": "mg/dL", "critical_low": None, "critical_high": 15.0},
    "albumin": {"min": 3.5, "max": 5.0, "unit": "g/dL", "critical_low": 1.5, "critical_high": None},
}

REFERENCE_ALIASES: Dict[str, str] = {
    "buncreatinineratio": "bun/creatinine ratio",
    "buncratio": "bun/creatinine ratio",
    "buncr": "bun/creatinine ratio",
    "totalcholesterol": "total cholesterol",
    "cholesterol": "total cholesterol",
    "hdlchol": "hdl cholesterol",
    "hdlcholesterol": "hdl cholesterol",
    "ldlchol": "ldl cholesterol",
    "ldlcholesterol": "ldl cholesterol",
    "vldlchol": "vldl cholesterol",
    "vldlcholesterol": "vldl cholesterol",
    "cholesterolhdlratio": "cholesterol hdl ratio",
    "totalcholesterolhdlratio": "cholesterol hdl ratio",
    "riskratio": "risk ratio",
}

_CLINICAL_SIGNIFICANCE = {
    "CRITICAL_HIGH": "Critical elevation — requires immediate clinical attention.",
    "CRITICAL_LOW": "Critical decrease — requires immediate clinical attention.",
    "HIGH": "Elevated above reference range — clinical correlation recommended.",
    "LOW": "Below reference range — clinical correlation recommended.",
    "NORMAL": "Within normal reference range.",
}


class LabInterpreter(ABC):
    """Abstract base class for lab interpretation engines."""

    @abstractmethod
    def interpret_results(
        self,
        lab_values: Dict[str, float],
        reference_ranges: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[LabResult]:
        """Interpret lab results against reference ranges."""

    @abstractmethod
    def identify_abnormalities(self, lab_values: Dict[str, float]) -> List[Dict[str, Any]]:
        """Return only the abnormal values with clinical significance."""


class StandardLabInterpreter(LabInterpreter):
    """
    Standard implementation using the built-in REFERENCE_RANGES evidence base.
    """

    def interpret_results(
        self,
        lab_values: Dict[str, float],
        reference_ranges: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[LabResult]:
        """
        Interpret all provided lab values.

        Args:
            lab_values: Dict of {test_name: numeric_value}.
            reference_ranges: Optional override; uses built-in if None.

        Returns:
            List of LabResult with flags and significance.
        """
        ranges = reference_ranges or REFERENCE_RANGES
        results: List[LabResult] = []

        for name, value in lab_values.items():
            norm_name, ref = resolve_reference_range(name, ranges)
            if not ref:
                continue

            flag = self._flag(value, ref)
            results.append(LabResult(
                name=name,
                value=value,
                unit=ref.get("unit", ""),
                flag=flag,
                reference_min=ref["min"],
                reference_max=ref["max"],
                clinical_significance=_CLINICAL_SIGNIFICANCE.get(flag, ""),
            ))

        return results

    def identify_abnormalities(self, lab_values: Dict[str, float]) -> List[Dict[str, Any]]:
        """Return only abnormal results as plain dicts."""
        all_results = self.interpret_results(lab_values)
        return [
            r.model_dump()
            for r in all_results
            if r.flag != "NORMAL"
        ]

    def _flag(self, value: float, ref: Dict[str, Any]) -> str:
        """Determine the flag for a lab value given its reference."""
        crit_low = ref.get("critical_low")
        crit_high = ref.get("critical_high")

        if crit_high is not None and value >= crit_high:
            return "CRITICAL_HIGH"
        if crit_low is not None and value <= crit_low:
            return "CRITICAL_LOW"
        if value > ref["max"]:
            return "HIGH"
        if value < ref["min"]:
            return "LOW"
        return "NORMAL"


def normalize_lab_key(name: str) -> str:
    """Normalize lab names for comparison and alias matching."""
    return re.sub(r"[^a-z0-9]+", "", name.lower().strip())


def resolve_reference_range(
    name: str,
    reference_ranges: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Resolve a lab name to a canonical reference range entry.

    Returns:
        (canonical_name, reference_range) or (None, None) if no match exists.
    """
    ranges = reference_ranges or REFERENCE_RANGES
    normalized = normalize_lab_key(name)
    canonical = REFERENCE_ALIASES.get(normalized)
    if canonical and canonical in ranges:
        return canonical, ranges[canonical]

    for key, value in ranges.items():
        if normalize_lab_key(key) == normalized:
            return key, value

    return None, None


class LabInterpretationService:
    """Service for lab result interpretation — uses StandardLabInterpreter by default."""

    def __init__(self, interpreter: Optional[LabInterpreter] = None):
        self.interpreter = interpreter or StandardLabInterpreter()

    def analyze_lab_report(self, lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze lab report dict and return interpreted results.

        Args:
            lab_data: Dict with 'values' key containing {test_name: value} pairs.
        """
        values: Dict[str, float] = {}
        for k, v in lab_data.items():
            try:
                values[k] = float(v)
            except (TypeError, ValueError):
                continue

        interpretations = self.interpreter.interpret_results(values)
        abnormalities = self.interpreter.identify_abnormalities(values)

        return {
            "status": "success",
            "total_tests": len(interpretations),
            "abnormal_count": len(abnormalities),
            "interpretations": [r.model_dump() for r in interpretations],
            "abnormalities": abnormalities,
        }
