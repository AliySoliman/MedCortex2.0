"""
guardrails.py
=============
Medical response guardrails for the MedCortex AI Safety subsystem.

Provides rule-based validation of AI-generated medical responses to prevent
harmful content such as unsolicited diagnoses, prescribing attempts, and
dangerously absolute medical claims.
"""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class GuardrailViolation(BaseModel):
    """Represents a single rule violation detected by the guardrail engine.

    Attributes:
        rule: Identifier of the rule that was violated.
        severity: How serious the violation is – 'warning', 'error', or 'critical'.
        message: Human-readable description of the violation.
    """

    rule: str
    severity: str = Field(..., pattern=r"^(warning|error|critical)$")
    message: str


class GuardrailResult(BaseModel):
    """The complete outcome of a guardrail check.

    Attributes:
        passed: True when no *error* or *critical* violations were found.
        violations: All violations detected (warnings + errors + criticals).
        modified_response: If auto-fix was applied, the cleaned response text;
            ``None`` when the original response required no modification.
    """

    passed: bool
    violations: List[GuardrailViolation] = Field(default_factory=list)
    modified_response: Optional[str] = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Phrases that constitute an improper definitive diagnosis claim.
_DIAGNOSIS_PATTERNS: List[str] = [
    r"\byou\s+definitely\s+have\b",
    r"\byou\s+have\s+(?:cancer|diabetes|hypertension|depression|anxiety|a\s+tumor|an?\s+infection|a\s+disease|a\s+condition|the\s+virus|the\s+bacteria|the\s+fungus)\b",
    r"\bthe\s+diagnosis\s+is\s+(?:definitely|certainly|clearly)\b",
    r"\byou\s+are\s+(?:definitely|certainly)\s+suffering\s+from\b",
]

#: Queries asking for self-treatment dosage schedules.
_PRESCRIBING_PATTERNS: List[str] = [
    r"\bhow\s+(?:much|many)\s+\w+\s+(?:should|can|do)\s+i\s+take\b",
    r"\bwhat\s+(?:dose|dosage|amount)\s+of\s+\w+\s+(?:should|can)\s+i\s+(?:take|use|consume)\b",
    r"\bcan\s+i\s+take\s+\d+\s*(?:mg|mcg|ml|g|tablets?|pills?)\b",
    r"\bhow\s+do\s+i\s+(?:self[- ]?(?:medicate|treat|prescribe))\b",
    r"\bprescribe\s+(?:myself|me)\b",
]

#: Response phrases that must be blocked outright (critical severity).
_BLOCKED_PHRASES: List[tuple[str, str]] = [
    (r"\bguaranteed\s+cure\b", "Response claims a 'guaranteed cure', which is prohibited."),
    (r"\bdefinitely\s+(?:have\s+)?cancer\b", "Response makes a definitive cancer assertion."),
    (r"\byou\s+will\s+(?:definitely\s+)?die\b", "Response contains life-threatening language."),
    (r"\b100\s*%\s+effective\b", "Response makes an absolute efficacy claim."),
    (r"\bno\s+side\s+effects\b", "Response falsely claims no side effects exist."),
]

#: Common medication keywords used to detect medication mentions.
_MEDICATION_KEYWORDS: List[str] = [
    "ibuprofen", "acetaminophen", "paracetamol", "aspirin", "amoxicillin",
    "metformin", "lisinopril", "atorvastatin", "omeprazole", "antibiotic",
    "antidepressant", "statin", "beta[- ]blocker", "insulin", "vaccine",
    "medication", "medicine", "drug", "tablet", "capsule", "pill", "dose",
    "prescription", "over[- ]the[- ]counter", "otc",
]

_MEDICATION_RE = re.compile(
    r"\b(?:" + "|".join(_MEDICATION_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

_DISCLAIMER_MARKER = "consult"  # Presence check for disclaimer language.

_MEDICATION_DISCLAIMER = (
    "\n\n⚕️ **Important**: Information about medications is provided for general "
    "educational purposes only. Always consult a qualified healthcare professional "
    "before starting, stopping, or changing any medication regimen."
)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class MedicalGuardrails:
    """Rule-based guardrail engine for medical AI responses.

    Applies a prioritised chain of safety rules to both the AI response text
    and the originating user query, then optionally auto-corrects violations
    that can be safely remediated without discarding the response.

    Usage::

        guardrails = MedicalGuardrails()
        result = guardrails.check(response_text, user_query)
        if not result.passed:
            safe_text = result.modified_response or "[Response blocked]"
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, response: str, query: str) -> GuardrailResult:
        """Evaluate *response* against all safety rules given the *query* context.

        Args:
            response: The raw text produced by the AI model.
            query: The original user query that triggered the response.

        Returns:
            A :class:`GuardrailResult` describing every violation found and,
            when fixable violations are present, an auto-corrected response.
        """
        violations: List[GuardrailViolation] = []

        violations.extend(self._rule_diagnosis_claim(response))
        violations.extend(self._rule_prescribing_attempt(query))
        violations.extend(self._rule_blocked_phrases(response))
        violations.extend(self._rule_medication_disclaimer(response))

        blocking_severities = {"error", "critical"}
        passed = not any(v.severity in blocking_severities for v in violations)

        modified: Optional[str] = None
        if violations:
            modified = self.auto_fix(response, violations)

        return GuardrailResult(
            passed=passed,
            violations=violations,
            modified_response=modified,
        )

    def auto_fix(self, response: str, violations: List[GuardrailViolation]) -> str:
        """Apply automatic corrections for all detectable violations.

        Critical/error violations that cannot be surgically corrected result in
        a replacement safety message.  Warning-level violations receive additive
        fixes (e.g., appending a disclaimer).

        Args:
            response: The original AI response text.
            violations: Violations identified by :meth:`check`.

        Returns:
            The best safe version of the response text.
        """
        has_critical = any(v.severity == "critical" for v in violations)
        has_error = any(v.severity == "error" for v in violations)

        fixed = response

        if has_critical:
            return (
                "⛔ I'm sorry, but I'm unable to provide this response as it "
                "contains content that may be harmful. Please consult a qualified "
                "healthcare professional for personalised medical advice."
            )

        if has_error:
            # Soften diagnosis language
            fixed = self._soften_diagnosis_language(fixed)

        # Always append medication disclaimer if that warning was raised
        medication_warnings = [
            v for v in violations
            if v.rule == "medication_disclaimer" and v.severity == "warning"
        ]
        if medication_warnings and _DISCLAIMER_MARKER not in fixed.lower():
            fixed = fixed.rstrip() + _MEDICATION_DISCLAIMER

        return fixed

    # ------------------------------------------------------------------
    # Private rule implementations
    # ------------------------------------------------------------------

    def _rule_diagnosis_claim(self, response: str) -> List[GuardrailViolation]:
        """Detect improper definitive diagnosis statements in the response."""
        violations: List[GuardrailViolation] = []
        for pattern in _DIAGNOSIS_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(
                    GuardrailViolation(
                        rule="diagnosis_claim",
                        severity="error",
                        message=(
                            "Response contains a definitive diagnosis claim. "
                            "AI systems must not diagnose conditions without "
                            "professional evaluation."
                        ),
                    )
                )
                break  # One violation per rule is sufficient
        return violations

    def _rule_prescribing_attempt(self, query: str) -> List[GuardrailViolation]:
        """Detect queries that request specific drug dosages for self-treatment."""
        violations: List[GuardrailViolation] = []
        for pattern in _PRESCRIBING_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                violations.append(
                    GuardrailViolation(
                        rule="prescribing_attempt",
                        severity="critical",
                        message=(
                            "Query requests specific medication dosage for "
                            "self-treatment. This constitutes a prescribing "
                            "attempt that must not be fulfilled."
                        ),
                    )
                )
                break
        return violations

    def _rule_blocked_phrases(self, response: str) -> List[GuardrailViolation]:
        """Block responses containing absolutely prohibited phrases."""
        violations: List[GuardrailViolation] = []
        for pattern, description in _BLOCKED_PHRASES:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(
                    GuardrailViolation(
                        rule="blocked_phrase",
                        severity="critical",
                        message=description,
                    )
                )
        return violations

    def _rule_medication_disclaimer(self, response: str) -> List[GuardrailViolation]:
        """Warn when the response mentions medications but lacks a disclaimer."""
        violations: List[GuardrailViolation] = []
        mentions_medication = bool(_MEDICATION_RE.search(response))
        has_disclaimer = _DISCLAIMER_MARKER in response.lower()
        if mentions_medication and not has_disclaimer:
            violations.append(
                GuardrailViolation(
                    rule="medication_disclaimer",
                    severity="warning",
                    message=(
                        "Response mentions medications but does not include "
                        "a disclaimer advising professional consultation."
                    ),
                )
            )
        return violations

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _soften_diagnosis_language(text: str) -> str:
        """Replace absolute diagnostic language with appropriately hedged phrasing."""
        replacements = [
            (r"\byou\s+definitely\s+have\b", "you may have"),
            (r"\byou\s+have\s+(cancer|diabetes|hypertension|depression|anxiety)\b",
             r"you might be experiencing symptoms associated with \1"),
            (r"\bthe\s+diagnosis\s+is\s+(?:definitely|certainly|clearly)\b",
             "the symptoms could potentially be consistent with"),
            (r"\byou\s+are\s+(?:definitely|certainly)\s+suffering\s+from\b",
             "you may be experiencing symptoms of"),
        ]
        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
