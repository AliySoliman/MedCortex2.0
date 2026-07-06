"""Compatibility helpers for lifestyle and doctor recommendations.

This module keeps older service imports working while delegating the actual
logic to the clinical intelligence layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.ai.clinical.doctor_finder import find_doctors
from app.ai.clinical.lifestyle import get_lifestyle_recommendations


def get_mock_recommendations(
    suspected_conditions: List[str] | None = None,
    symptoms: List[str] | None = None,
) -> Dict[str, Any]:
    """Return recommendation payloads using the canonical clinical helpers."""
    lifestyle = get_lifestyle_recommendations(
        suspected_conditions=suspected_conditions or [],
        symptoms=symptoms or [],
    )
    doctor_specialties = lifestyle.get("doctor_specialties", []) or []
    return {
        "lifestyle": lifestyle,
        "doctors": find_doctors(doctor_specialties),
    }
