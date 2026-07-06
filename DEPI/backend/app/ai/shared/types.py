# backend/app/ai/shared/types.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared Types
# Common type definitions for AI operations
# ─────────────────────────────────────────────────────────────────────────────

from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum


class Provider(str, Enum):
    """AI provider types."""
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


class TaskType(str, Enum):
    """AI task types."""
    CHAT = "chat"
    REASONING = "reasoning"
    VISION = "vision"
    REWRITE = "rewrite"
    OCR = "ocr"
    EMBEDDING = "embedding"


class WorkflowType(str, Enum):
    """Workflow types."""
    CHAT = "chat"
    VISION = "vision"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    LAB = "lab"
    REPORT = "report"


class Message(TypedDict):
    """Chat message type."""
    role: str
    content: str
    timestamp: Optional[str]


class Citation(TypedDict):
    """Citation type."""
    source: str
    text: str
    page: Optional[int]
    confidence: Optional[float]


class RetrievedDocument(TypedDict):
    """Retrieved document type."""
    content: str
    metadata: Dict[str, Any]
    score: float
