# backend/app/ai/multimodal/utils.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Utilities
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.multimodal.enums import ConfidenceLevel


def calculate_confidence_level(score: float, thresholds: dict) -> ConfidenceLevel:
    """
    Convert a float score (0.0 to 1.0) into a categorical ConfidenceLevel.
    `thresholds` should contain HIGH, MEDIUM, LOW keys (from settings).
    """
    if score >= thresholds.get("CONFIDENCE_THRESHOLD_HIGH", 0.8):
        return ConfidenceLevel.HIGH
    elif score >= thresholds.get("CONFIDENCE_THRESHOLD_MEDIUM", 0.5):
        return ConfidenceLevel.MEDIUM
    elif score >= thresholds.get("CONFIDENCE_THRESHOLD_LOW", 0.3):
        return ConfidenceLevel.LOW
    return ConfidenceLevel.UNKNOWN


def get_mime_modality(mime_type: str) -> str:
    """Basic helper to guess modality from MIME type."""
    if mime_type.startswith("image/"):
        return "image"
    if mime_type == "application/pdf":
        return "document"
    if mime_type.startswith("text/"):
        return "text"
    return "unknown"
