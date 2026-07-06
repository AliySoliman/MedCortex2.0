# backend/app/ai/shared/exceptions.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared Exceptions
# Custom exceptions for AI operations
# ─────────────────────────────────────────────────────────────────────────────

from typing import Optional, Dict, Any


class AIBaseException(Exception):
    """Base exception for AI operations."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ProviderError(AIBaseException):
    """Exception raised when AI provider fails."""
    pass


class ModelNotFoundError(AIBaseException):
    """Exception raised when requested model is not found."""
    pass


class PromptError(AIBaseException):
    """Exception raised when prompt construction fails."""
    pass


class WorkflowError(AIBaseException):
    """Exception raised when workflow execution fails."""
    pass


class RetrievalError(AIBaseException):
    """Exception raised when retrieval operation fails."""
    pass


class MemoryError(AIBaseException):
    """Exception raised when memory operation fails."""
    pass


class VisionError(AIBaseException):
    """Exception raised when vision operation fails."""
    pass


class ClinicalError(AIBaseException):
    """Exception raised when clinical operation fails."""
    pass


class ConfigurationError(AIBaseException):
    """Exception raised when configuration is invalid."""
    pass


class ValidationError(AIBaseException):
    """Exception raised when input validation fails."""
    pass
