"""
unsafe_request_handler.py
=========================
Unsafe request detection for the MedCortex AI Safety subsystem.

Screens incoming user queries against a catalogue of unsafe patterns before
any AI processing begins, preventing the system from generating harmful
responses to dangerous requests.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class UnsafeRequestResult(BaseModel):
    """The outcome of an unsafe request check.

    Attributes:
        is_unsafe: ``True`` when the query matched at least one unsafe pattern.
        category: Short identifier for the matched unsafe category, or
            ``None`` if the request is safe.
        reason: Human-readable explanation for the determination.
        safe_response: A pre-crafted, safe reply that can be returned to the
            user without AI processing, or ``None`` for safe requests.
    """

    is_unsafe: bool
    category: Optional[str] = None
    reason: str
    safe_response: Optional[str] = None


# ---------------------------------------------------------------------------
# Unsafe pattern catalogue
# ---------------------------------------------------------------------------

#: Each entry: (compiled_pattern, category, safe_response_text)
_UNSAFE_PATTERN_DEFINITIONS: List[Tuple[str, str, str]] = [
    # ------------------------------------------------------------------ #
    # 1. Self-prescribing requests                                        #
    # ------------------------------------------------------------------ #
    (
        r"\b(?:prescribe|self[- ]?prescrib|self[- ]?medic|give\s+me\s+a\s+prescription)\b",
        "self_prescribing",
        (
            "I'm unable to prescribe medications or create a prescription for you. "
            "Prescriptions must be issued by a licensed healthcare provider who can "
            "evaluate your specific medical history and current condition. Please "
            "consult your doctor or visit an urgent care clinic."
        ),
    ),
    (
        r"\bhow\s+(?:much|many)\s+\w+\s+(?:should|can)\s+i\s+(?:take|use|inject|administer)\b",
        "self_prescribing",
        (
            "Specific medication dosing for self-treatment falls outside what I can "
            "safely provide. Dosages depend on your age, weight, kidney function, "
            "other medications, and medical history — factors only your healthcare "
            "provider can properly assess. Please seek professional medical advice."
        ),
    ),
    (
        r"\bwhat(?:'s|\s+is)\s+the\s+(?:right|correct|safe|maximum|minimum)\s+(?:dose|dosage|amount)\s+(?:of\s+)?\w+\s+(?:for\s+me|i\s+should\s+take)\b",
        "self_prescribing",
        (
            "I cannot recommend specific drug dosages for personal use. Dosage "
            "decisions are highly individualised and must be made with the guidance "
            "of a licensed medical professional who knows your complete health profile."
        ),
    ),

    # ------------------------------------------------------------------ #
    # 2. Substance harm requests                                          #
    # ------------------------------------------------------------------ #
    (
        r"\bhow\s+(?:to|do\s+i|can\s+i)\s+(?:get\s+)?(?:high|overdose)\s+on\b",
        "substance_harm",
        (
            "I'm not able to provide information on how to misuse medications or "
            "substances. If you or someone you know is struggling with substance use, "
            "please reach out to a substance abuse helpline (e.g., SAMHSA National "
            "Helpline: 1-800-662-4357 in the US) or seek immediate medical help."
        ),
    ),
    (
        r"\b(?:lethal|deadly|fatal)\s+dose\s+of\b",
        "substance_harm",
        (
            "I cannot provide information about lethal doses of substances. "
            "If you are in crisis or having thoughts of self-harm, please contact "
            "the 988 Suicide & Crisis Lifeline (call or text 988 in the US), "
            "or call emergency services immediately."
        ),
    ),
    (
        r"\bwhich\s+(?:drugs?|medications?|pills?|substances?)\s+(?:can|will|would)\s+(?:kill|harm)\b",
        "substance_harm",
        (
            "I'm unable to provide information that could be used to harm yourself "
            "or others. Please contact a crisis helpline or emergency services if "
            "you or someone else is in danger."
        ),
    ),

    # ------------------------------------------------------------------ #
    # 3. Definitive diagnosis requests                                    #
    # ------------------------------------------------------------------ #
    (
        r"\bdo\s+i\s+(?:definitely|certainly|for\s+sure)\s+have\b",
        "definitive_diagnosis",
        (
            "I cannot provide a definitive medical diagnosis. Diagnosing conditions "
            "requires a physical examination, a complete medical history, and "
            "potentially laboratory or imaging tests — all performed by a qualified "
            "healthcare professional. Please consult your doctor."
        ),
    ),
    (
        r"\btell\s+me\s+(?:exactly|definitively|for\s+sure)\s+what\s+(?:disease|condition|illness|disorder)\s+i\s+have\b",
        "definitive_diagnosis",
        (
            "Providing an exact diagnosis is beyond my capabilities. AI systems "
            "cannot replace clinical evaluation. Please schedule an appointment "
            "with your primary care physician or a specialist for a proper diagnosis."
        ),
    ),
    (
        r"\bdiagnose\s+me\b",
        "definitive_diagnosis",
        (
            "I'm not able to diagnose medical conditions. Diagnosis requires "
            "professional clinical assessment. I can share general health "
            "information, but for any personal health concerns please see a doctor."
        ),
    ),

    # ------------------------------------------------------------------ #
    # 4. Self / other harm requests                                       #
    # ------------------------------------------------------------------ #
    (
        r"\bhow\s+(?:to|can\s+i|do\s+i)\s+(?:kill|hurt|harm|injure)\s+(?:myself|my\s+self|someone|a\s+person|people)\b",
        "self_other_harm",
        (
            "I cannot and will not provide information on how to harm yourself or "
            "others. If you are experiencing thoughts of self-harm or harming others, "
            "please seek immediate help: call 988 (Suicide & Crisis Lifeline in the "
            "US), text HOME to 741741 (Crisis Text Line), or call 911 / your local "
            "emergency number."
        ),
    ),
    (
        r"\bsuicid(?:e|al)\s+(?:method|plan|way|how)\b",
        "self_other_harm",
        (
            "I'm unable to provide information related to suicide methods. "
            "If you're struggling, please reach out immediately: "
            "📞 988 Suicide & Crisis Lifeline (US) – call or text 988, "
            "📞 International Association for Suicide Prevention: "
            "https://www.iasp.info/resources/Crisis_Centres/"
        ),
    ),
    (
        r"\bwant\s+to\s+(?:end\s+(?:my|it\s+all|everything)|kill\s+myself|die)\b",
        "self_other_harm",
        (
            "It sounds like you may be going through an incredibly difficult time. "
            "Your life has value and help is available right now. Please contact "
            "the 988 Suicide & Crisis Lifeline by calling or texting 988, or "
            "go to your nearest emergency room."
        ),
    ),
]

# Compile all patterns once at import time.
UNSAFE_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(pat, re.IGNORECASE), category, response)
    for pat, category, response in _UNSAFE_PATTERN_DEFINITIONS
]


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class UnsafeRequestHandler:
    """Screen user queries for unsafe content before AI processing.

    The handler applies a catalogue of pre-compiled regular-expression patterns
    to the incoming query.  On first match it returns an
    :class:`UnsafeRequestResult` with ``is_unsafe=True`` and a ready-made safe
    response that can be delivered to the user without further AI processing.

    Usage::

        handler = UnsafeRequestHandler()
        result = handler.check("How do I overdose on ibuprofen?")
        if result.is_unsafe:
            return result.safe_response
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, query: str) -> UnsafeRequestResult:
        """Check *query* against all known unsafe patterns.

        Patterns are evaluated in order; the first match wins.

        Args:
            query: The raw user query string to evaluate.

        Returns:
            An :class:`UnsafeRequestResult` indicating whether the query is
            unsafe and, if so, which category matched along with a safe reply.
        """
        for pattern, category, safe_response in UNSAFE_PATTERNS:
            match = pattern.search(query)
            if match:
                matched_text = match.group(0)
                return UnsafeRequestResult(
                    is_unsafe=True,
                    category=category,
                    reason=(
                        f"Query matched unsafe pattern in category "
                        f"'{category}': matched text was '{matched_text}'."
                    ),
                    safe_response=safe_response,
                )

        return UnsafeRequestResult(
            is_unsafe=False,
            category=None,
            reason="No unsafe patterns detected in the query.",
            safe_response=None,
        )
