# backend/app/ai/clinical/lifestyle.py
# ─────────────────────────────────────────────────────────────────────────────
# MedCortex Lifestyle Recommender
# Takes suspected conditions + symptoms → returns structured JSON recommendations
# for food, drinks, exercise, and required doctor specialties
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import re
from typing import List, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.ai.providers.provider_factory import get_default_llm


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE SCHEMA (what we guarantee back to the route)
# ─────────────────────────────────────────────────────────────────────────────
EMPTY_RECOMMENDATIONS: Dict[str, Any] = {
    "foods_to_eat":           [],
    "foods_to_avoid":         [],
    "drinks_to_have":         [],
    "drinks_to_avoid":        [],
    "exercises_recommended":  [],
    "exercises_to_avoid":     [],
    "rest_recommendation":    "",
    "doctor_specialties":     [],
}


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are a clinical lifestyle advisor AI.
Given a list of suspected medical conditions and symptoms, return ONLY a valid JSON object.
No markdown. No explanation. No extra text. Just the raw JSON.

The JSON must follow this exact structure:
{{
  "foods_to_eat":          ["item1", "item2", ...],
  "foods_to_avoid":        ["item1", "item2", ...],
  "drinks_to_have":        ["item1", "item2", ...],
  "drinks_to_avoid":       ["item1", "item2", ...],
  "exercises_recommended": ["item1", "item2", ...],
  "exercises_to_avoid":    ["item1", "item2", ...],
  "rest_recommendation":   "A single concise sentence about rest/sleep.",
  "doctor_specialties":    ["Specialty1", "Specialty2", ...]
}}

Rules:
- Each list should have 3–6 specific, practical items.
- doctor_specialties must use standard US medical specialty names 
  (e.g. "General Practitioner", "Pulmonologist", "Cardiologist").
- If conditions are unclear, give general wellness advice.
- Return ONLY the JSON object — absolutely nothing else.
"""

_USER_PROMPT = """Suspected conditions: {conditions}
Symptoms: {symptoms}"""


def _fallback_doctor_specialties(
    suspected_conditions: List[str],
    symptoms: List[str],
) -> List[str]:
    haystack = " ".join([*suspected_conditions, *symptoms]).lower()
    specialties: List[str] = []

    keyword_map = [
        (("chest pain", "heart", "palpitations", "blood pressure"), "Cardiologist"),
        (("shortness of breath", "cough", "wheezing", "breathing"), "Pulmonologist"),
        (("rash", "itching", "skin", "acne"), "Dermatologist"),
        (("headache", "migraine", "dizziness", "seizure"), "Neurologist"),
        (("stomach", "abdominal", "nausea", "vomiting", "diarrhea"), "Gastroenterologist"),
        (("urine", "kidney", "burning urination"), "Urologist"),
        (("joint", "back pain", "knee", "shoulder"), "Orthopedic Surgeon"),
    ]

    for keywords, specialty in keyword_map:
        if any(keyword in haystack for keyword in keywords):
            specialties.append(specialty)

    if not specialties:
        specialties.append("General Practitioner")

    return specialties


def _fallback_recommendations(
    suspected_conditions: List[str],
    symptoms: List[str],
) -> Dict[str, Any]:
    rest = "Rest, hydrate, and monitor symptoms closely."
    if symptoms:
        rest = "Rest, stay hydrated, and seek medical care if symptoms worsen."

    return {
        **EMPTY_RECOMMENDATIONS,
        "rest_recommendation": rest,
        "doctor_specialties": _fallback_doctor_specialties(suspected_conditions, symptoms),
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def get_lifestyle_recommendations(
    suspected_conditions: List[str],
    symptoms: List[str],
) -> Dict[str, Any]:
    """
    Calls Groq/Llama to generate structured lifestyle recommendations.

    Args:
        suspected_conditions: e.g. ["Influenza", "Upper Respiratory Infection"]
        symptoms:             e.g. ["fever", "sore throat", "fatigue"]

    Returns:
        Dict matching EMPTY_RECOMMENDATIONS schema above.
    """
    # Guard — nothing to work with
    if not suspected_conditions and not symptoms:
        return _fallback_recommendations(suspected_conditions, symptoms)

    raw = ""
    try:
        llm = get_default_llm(
            model="llama-3.3-70b-versatile",
            temperature=0.2,      # slight creativity for variety in recommendations
            max_tokens=1024,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human",  _USER_PROMPT),
        ])

        chain = prompt | llm | StrOutputParser()

        raw = chain.invoke({
            "conditions": ", ".join(suspected_conditions) if suspected_conditions else "Unknown",
            "symptoms":   ", ".join(symptoms)             if symptoms             else "Not specified",
        })

        # ── Parse the JSON response ───────────────────────────────────────────────
        # Strip any accidental markdown fences
        cleaned = raw.strip()
        cleaned = re.sub(r'^```(?:json)?', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'```$',          '', cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        data = json.loads(cleaned)

        # Ensure all expected keys are present, fall back to empty
        result = {}
        for key, default in EMPTY_RECOMMENDATIONS.items():
            result[key] = data.get(key, default)
        return result

    except (json.JSONDecodeError, Exception) as e:
        print(f"[lifestyle_model] JSON parse error: {e}\nRaw output: {raw[:300]}")
        return _fallback_recommendations(suspected_conditions, symptoms)
