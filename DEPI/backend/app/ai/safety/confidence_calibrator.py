"""
confidence_calibrator.py
========================
Confidence score calibration for the MedCortex AI Safety subsystem.

Transforms a raw model confidence score into a calibrated value that accounts
for hallucination risk and the quantity of supporting evidence, then maps the
result to a human-readable tier.
"""

from __future__ import annotations

import math
from typing import List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CalibratedConfidence(BaseModel):
    """The output of a confidence calibration pass.

    Attributes:
        raw_score: The original, uncalibrated confidence from the model.
        calibrated_score: The adjusted confidence after safety penalties and
            evidence boosts, clamped to ``[0.0, 1.0]``.
        tier: Qualitative tier label derived from *calibrated_score*.
        explanation: Human-readable summary of the adjustments applied.
    """

    raw_score: float = Field(..., ge=0.0, le=1.0)
    calibrated_score: float = Field(..., ge=0.0, le=1.0)
    tier: str = Field(..., pattern=r"^(very_low|low|medium|high|very_high)$")
    explanation: str


# ---------------------------------------------------------------------------
# Tier thresholds (lower-inclusive)
# ---------------------------------------------------------------------------

_TIER_THRESHOLDS: List[tuple[float, str]] = [
    (0.85, "very_high"),
    (0.70, "high"),
    (0.50, "medium"),
    (0.30, "low"),
    (0.00, "very_low"),
]

# ---------------------------------------------------------------------------
# Calibration parameters
# ---------------------------------------------------------------------------

#: Maximum penalty applied when hallucination_risk == 1.0.
_MAX_HALLUCINATION_PENALTY = 0.40

#: Maximum boost applied when evidence_count reaches the saturation point.
_MAX_EVIDENCE_BOOST = 0.15

#: Number of evidence documents at which the boost saturates.
_EVIDENCE_SATURATION = 10


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class ConfidenceCalibrator:
    """Calibrate raw model confidence scores for medical safety requirements.

    The calibration formula applies three sequential adjustments:

    1. **Hallucination penalty** – reduces confidence proportionally to the
       detected hallucination risk score.
    2. **Evidence boost** – increases confidence proportionally to the
       logarithm of the number of supporting evidence documents, saturating
       at :data:`_EVIDENCE_SATURATION` sources.
    3. **Clamping** – the result is forced into ``[0.0, 1.0]`` before mapping
       to a qualitative :attr:`~CalibratedConfidence.tier`.

    Usage::

        calibrator = ConfidenceCalibrator()
        result = calibrator.calibrate(
            raw_confidence=0.82,
            evidence_count=5,
            hallucination_risk=0.3,
        )
        print(result.tier)          # "medium" or "high" depending on inputs
        print(result.calibrated_score)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calibrate(
        self,
        raw_confidence: float,
        evidence_count: int,
        hallucination_risk: float,
    ) -> CalibratedConfidence:
        """Produce a calibrated confidence given model output and safety signals.

        Args:
            raw_confidence: Confidence reported by the model, in ``[0.0, 1.0]``.
            evidence_count: Number of retrieved source documents that support
                the response.  Must be ≥ 0.
            hallucination_risk: Continuous hallucination risk score in
                ``[0.0, 1.0]`` as produced by
                :class:`~safety.hallucination_detector.HallucinationDetector`.

        Returns:
            A :class:`CalibratedConfidence` with the adjusted score, tier, and
            a plain-English explanation of each adjustment.
        """
        raw_confidence = float(max(0.0, min(1.0, raw_confidence)))
        hallucination_risk = float(max(0.0, min(1.0, hallucination_risk)))
        evidence_count = max(0, int(evidence_count))

        notes: List[str] = [f"Started with raw score {raw_confidence:.3f}."]

        # 1. Hallucination penalty
        penalty = hallucination_risk * _MAX_HALLUCINATION_PENALTY
        adjusted = raw_confidence - penalty
        if penalty > 0:
            notes.append(
                f"Applied hallucination penalty of {penalty:.3f} "
                f"(risk={hallucination_risk:.2f})."
            )

        # 2. Evidence boost – logarithmic saturation
        if evidence_count > 0:
            boost_factor = math.log(1 + evidence_count) / math.log(1 + _EVIDENCE_SATURATION)
            boost = boost_factor * _MAX_EVIDENCE_BOOST
            adjusted += boost
            notes.append(
                f"Applied evidence boost of {boost:.3f} "
                f"({evidence_count} source(s))."
            )
        else:
            notes.append("No evidence documents available; no boost applied.")

        # 3. Clamp
        calibrated = max(0.0, min(1.0, adjusted))
        if calibrated != adjusted:
            notes.append(f"Clamped result from {adjusted:.3f} to {calibrated:.3f}.")

        tier = self._score_to_tier(calibrated)
        explanation = " ".join(notes) + f" Final tier: {tier}."

        return CalibratedConfidence(
            raw_score=round(raw_confidence, 4),
            calibrated_score=round(calibrated, 4),
            tier=tier,
            explanation=explanation,
        )

    def propagate(self, upstream_scores: List[float]) -> float:
        """Combine multiple upstream confidence scores via geometric mean.

        The geometric mean is preferable to the arithmetic mean in confidence
        propagation because a single very low score appropriately drags down
        the combined value, reflecting the weakest-link nature of medical
        evidence chains.

        Args:
            upstream_scores: A non-empty list of confidence scores in
                ``[0.0, 1.0]``.

        Returns:
            The geometric mean, clamped to ``[0.0, 1.0]``.  Returns ``0.0``
            if the list is empty or contains a zero.
        """
        if not upstream_scores:
            return 0.0
        scores = [max(0.0, min(1.0, float(s))) for s in upstream_scores]
        # If any score is exactly zero the product is zero.
        if 0.0 in scores:
            return 0.0
        log_sum = sum(math.log(s) for s in scores)
        geo_mean = math.exp(log_sum / len(scores))
        return round(max(0.0, min(1.0, geo_mean)), 4)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_to_tier(score: float) -> str:
        """Map a continuous calibrated score to a qualitative tier label."""
        for threshold, label in _TIER_THRESHOLDS:
            if score >= threshold:
                return label
        return "very_low"
