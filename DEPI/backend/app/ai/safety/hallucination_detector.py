"""
hallucination_detector.py
=========================
Hallucination detection for AI-generated medical responses.

Analyses a model response against its retrieved source context to identify
signs of fabricated information – absolute certainty language, statistics
not grounded in sources, and named entities absent from the context.
"""

from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class HallucinationRisk(BaseModel):
    """Structured result of a hallucination detection pass.

    Attributes:
        risk_level: Qualitative risk tier – ``'low'``, ``'medium'``, or ``'high'``.
        risk_score: Continuous score in ``[0.0, 1.0]`` where 1.0 is maximum risk.
        indicators: Short labels describing each detected risk signal.
        flagged_claims: The exact response excerpts that raised concerns.
    """

    risk_level: str = Field(..., pattern=r"^(low|medium|high)$")
    risk_score: float = Field(..., ge=0.0, le=1.0)
    indicators: List[str] = Field(default_factory=list)
    flagged_claims: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Words that signal unwarranted certainty in medical claims.
_CERTAINTY_TERMS: List[str] = [
    "definitely", "certainly", "guaranteed", "always", "never",
    "absolutely", "without a doubt", "100%", "proven to", "undoubtedly",
    "will always", "is always", "are always",
]

#: Compiled pattern that matches any certainty term as a whole phrase.
_CERTAINTY_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in _CERTAINTY_TERMS) + r")\b",
    re.IGNORECASE,
)

#: Pattern to detect numeric statistics in the response text.
_STAT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|percent|in\s+\d+|out\s+of\s+\d+|per\s+\d+|patients?|cases?|studies?)\b",
    re.IGNORECASE,
)

#: Common drug name suffixes/prefixes for named-entity approximation.
_DRUG_SUFFIX_RE = re.compile(
    r"\b\w+(?:mab|nib|pril|sartan|statin|olol|oxacin|mycin|cycline|cillin|vir|ine|ol|ide|ate)\b",
    re.IGNORECASE,
)

#: Common medical condition keywords.
_CONDITION_KEYWORDS: List[str] = [
    "cancer", "diabetes", "hypertension", "depression", "anxiety",
    "alzheimer", "parkinson", "arthritis", "asthma", "copd", "hiv", "aids",
    "hepatitis", "tuberculosis", "malaria", "cholera", "typhoid", "ebola",
    "covid", "influenza", "pneumonia", "stroke", "myocardial infarction",
    "heart attack", "heart failure", "kidney disease", "liver disease",
    "obesity", "anemia", "leukemia", "lymphoma", "melanoma",
]

_CONDITION_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(c) for c in _CONDITION_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Sentence extractor (rough).
_SENTENCE_RE = re.compile(r"[^.!?]*(?:definitely|certainly|guaranteed|always)[^.!?]*[.!?]?", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class HallucinationDetector:
    """Detect potential hallucinations in AI-generated medical responses.

    The detector uses a heuristic, rule-based approach that does not require
    a secondary language model, making it suitable for low-latency safety
    pipelines.  It checks three orthogonal risk dimensions:

    1. **Certainty language** – absolute words in a medical context.
    2. **Unsupported statistics** – numbers and percentages absent from context.
    3. **Unknown named entities** – drugs or conditions not in source docs.

    Each dimension contributes independently to the final :attr:`risk_score`.
    """

    # Weight allocated to each dimension (must sum ≤ 1.0).
    _W_CERTAINTY = 0.35
    _W_STATISTICS = 0.35
    _W_ENTITIES = 0.30

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, response: str, source_context: str) -> HallucinationRisk:
        """Analyse *response* for hallucination signals relative to *source_context*.

        Args:
            response: The AI-generated answer text.
            source_context: The retrieved source passages that should ground the
                response.  An empty string means no context is available, which
                maximises entity-based risk scores.

        Returns:
            A :class:`HallucinationRisk` with risk level, score, and evidence.
        """
        indicators: List[str] = []
        flagged_claims: List[str] = []

        # --- Dimension 1: Certainty language ---
        certainty_score, certainty_claims = self._check_certainty_language(response)
        if certainty_score > 0:
            indicators.append("absolute_certainty_language")
            flagged_claims.extend(certainty_claims)

        # --- Dimension 2: Unsupported statistics ---
        stat_score, stat_claims = self._check_unsupported_statistics(response, source_context)
        if stat_score > 0:
            indicators.append("unsupported_statistics")
            flagged_claims.extend(stat_claims)

        # --- Dimension 3: Unknown named entities ---
        entity_score, entity_claims = self._check_unknown_entities(response, source_context)
        if entity_score > 0:
            indicators.append("unknown_named_entities")
            flagged_claims.extend(entity_claims)

        risk_score = self.get_risk_score(
            [certainty_score, stat_score, entity_score]
        )
        risk_level = self._score_to_level(risk_score)

        return HallucinationRisk(
            risk_level=risk_level,
            risk_score=round(risk_score, 4),
            indicators=indicators,
            flagged_claims=list(dict.fromkeys(flagged_claims)),  # deduplicate
        )

    def get_risk_score(self, indicators: List[float]) -> float:  # noqa: N802 – spec name
        """Combine per-dimension risk sub-scores into a single overall score.

        Args:
            indicators: A list of fractional scores, one per dimension, each
                in ``[0.0, 1.0]``.  Extra elements are averaged and capped.

        Returns:
            A combined risk score in ``[0.0, 1.0]``.
        """
        if not indicators:
            return 0.0
        weights = [self._W_CERTAINTY, self._W_STATISTICS, self._W_ENTITIES]
        total = 0.0
        for i, score in enumerate(indicators[:3]):
            weight = weights[i] if i < len(weights) else 0.1
            total += score * weight
        # Any extra dimensions are averaged and added with a small weight.
        if len(indicators) > 3:
            extra_avg = sum(indicators[3:]) / len(indicators[3:])
            total += extra_avg * 0.1
        return min(total, 1.0)

    # ------------------------------------------------------------------
    # Dimension checkers
    # ------------------------------------------------------------------

    def _check_certainty_language(
        self, response: str
    ) -> tuple[float, List[str]]:
        """Return a sub-score and flagged excerpts for certainty language."""
        matches = _CERTAINTY_RE.findall(response)
        if not matches:
            return 0.0, []

        # Extract surrounding sentence fragments for transparency.
        flagged: List[str] = []
        for sent_match in _SENTENCE_RE.finditer(response):
            excerpt = sent_match.group(0).strip()
            if excerpt:
                flagged.append(excerpt[:200])  # Truncate long excerpts

        # Score proportional to the number of certainty terms found, capped.
        score = min(len(matches) * 0.25, 1.0)
        return score, flagged[:5]

    def _check_unsupported_statistics(
        self, response: str, source_context: str
    ) -> tuple[float, List[str]]:
        """Return a sub-score for statistics in *response* absent from *source_context*."""
        stat_matches = _STAT_RE.findall(response)
        if not stat_matches:
            return 0.0, []

        unsupported: List[str] = []
        for stat in stat_matches:
            # Normalise whitespace for comparison.
            normalised = re.sub(r"\s+", " ", stat).strip()
            if normalised.lower() not in source_context.lower():
                unsupported.append(normalised)

        if not unsupported:
            return 0.0, []

        ratio = len(unsupported) / max(len(stat_matches), 1)
        score = min(ratio * 0.9, 1.0)
        return score, [f"Statistic not in source: '{s}'" for s in unsupported[:5]]

    def _check_unknown_entities(
        self, response: str, source_context: str
    ) -> tuple[float, List[str]]:
        """Return a sub-score for drugs/conditions in response absent from sources."""
        response_drugs = set(m.group(0) for m in _DRUG_SUFFIX_RE.finditer(response))
        response_conditions = set(m.group(0) for m in _CONDITION_RE.finditer(response))
        all_entities = response_drugs | response_conditions

        if not all_entities:
            return 0.0, []

        context_lower = source_context.lower()
        unknown: List[str] = [
            e for e in all_entities
            if e.lower() not in context_lower
        ]

        if not unknown:
            return 0.0, []

        ratio = len(unknown) / max(len(all_entities), 1)
        score = min(ratio * 0.8, 1.0)
        return score, [f"Entity not found in source: '{e}'" for e in sorted(unknown)[:5]]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_to_level(score: float) -> str:
        """Map a continuous score to a qualitative risk level."""
        if score >= 0.55:
            return "high"
        if score >= 0.25:
            return "medium"
        return "low"
