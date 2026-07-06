# backend/app/ai/multimodal/exceptions.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Exceptions
#
# Centralized exception hierarchy for the entire multimodal subsystem.
# Every OCR, Vision, Classification, Routing, Parsing and Processing
# component should raise one of these exceptions.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Optional, Dict, Any

from app.ai.shared.exceptions import AIBaseException


# ============================================================================
# Base Exception
# ============================================================================

class MultimodalError(AIBaseException):
    """
    Base exception for the entire Multimodal subsystem.
    """
    pass


# ============================================================================
# Validation
# ============================================================================

class ValidationError(MultimodalError):
    """
    Raised when uploaded files fail validation.
    """
    pass


# ============================================================================
# Classification
# ============================================================================

class ClassificationError(MultimodalError):
    """
    Raised when the classifier cannot determine the file type.
    """
    pass


# ============================================================================
# Routing
# ============================================================================

class RoutingError(MultimodalError):
    """
    Raised when the router cannot determine the correct processing pipeline.
    """
    pass


# ============================================================================
# Preprocessing
# ============================================================================

class PreprocessingError(MultimodalError):
    """
    Raised when image/document preprocessing fails.
    """
    pass


# ============================================================================
# OCR
# ============================================================================

class OCRError(MultimodalError):
    """
    Raised when an OCR provider fails.
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}

        if provider:
            details["provider"] = provider

        super().__init__(message, details)


# ============================================================================
# Vision
# ============================================================================

class VisionError(MultimodalError):
    """
    Raised when a Vision provider fails.
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}

        if provider:
            details["provider"] = provider

        super().__init__(message, details)


# ============================================================================
# Parsing
# ============================================================================

class ParsingError(MultimodalError):
    """
    Raised when extracted OCR/Vision output cannot be parsed into structured
    medical data.
    """
    pass


# ============================================================================
# Extraction
# ============================================================================

class ExtractionError(MultimodalError):
    """
    Generic extraction failure.

    Used when the failure source is unknown or shared between OCR and Vision.
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}

        if provider:
            details["provider"] = provider

        super().__init__(message, details)


# ============================================================================
# Provider
# ============================================================================

class ProviderError(MultimodalError):
    """
    Raised when a provider fails to initialize or execute.
    """
    pass


# ============================================================================
# Timeout
# ============================================================================

class TimeoutError(MultimodalError):
    """
    Raised when a multimodal operation exceeds the configured timeout.
    """
    pass


# ============================================================================
# Unsupported File
# ============================================================================

class UnsupportedFileError(MultimodalError):
    """
    Raised when the uploaded file type is unsupported.
    """
    pass