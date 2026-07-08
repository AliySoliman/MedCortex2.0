# backend/app/config/settings.py
# ─────────────────────────────────────────────────────────────────────────────
# Settings
# Centralized application configuration — no hardcoded values elsewhere.
# All subsystems must read from this module via get_settings().
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Optional, List
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings — single source of truth for all configuration."""
    
    ENV: str = "development" # development | production

    # ── API Keys ──────────────────────────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./medcortex.db"

    # ── AI Models ─────────────────────────────────────────────────────────────
    MODEL_CHAT: str = "llama-3.3-70b-versatile"
    MODEL_REASONING: str = "qwen-3.6-27b"
    MODEL_VISION: str = "gemini-3.5-flash"
    MODEL_VISION_FALLBACK: str = "gemini-2.5-flash"
    MODEL_DOCUMENT: str = "gemini-2.5-flash"
    MODEL_REWRITE: str = "llama-3.3-70b-versatile"
    MODEL_OCR: str = "paddleocr"
    MODEL_EMBEDDING: str = "BAAI/bge-large-en-v1.5"

    # Legacy compatibility aliases
    DEFAULT_LLM_MODEL: str = "llama-3.3-70b-versatile"
    DEFAULT_EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"

    # ── AI Providers ──────────────────────────────────────────────────────────
    DEFAULT_PROVIDER: str = "groq"
    PROVIDER_CHAT: str = "groq"
    PROVIDER_REASONING: str = "groq"
    PROVIDER_VISION: str = "gemini"
    PROVIDER_DOCUMENT: str = "gemini"
    PROVIDER_EMBEDDING: str = "huggingface"

    # ── Pinecone ──────────────────────────────────────────────────────────────
    PINECONE_INDEX: str = "medical-assistant"
    PINECONE_NAMESPACE: str = "medical_textbooks_base"

    # ── Doctor Lookup ─────────────────────────────────────────────────────────
    DOCTOR_LOOKUP_DEFAULT_CITY: str = "Cairo"
    DOCTOR_LOOKUP_COUNTRY: str = "Egypt"

    # ── JWT / Auth ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    # ── Timeouts (seconds) ────────────────────────────────────────────────────
    AI_TIMEOUT_CHAT: float = 30.0
    AI_TIMEOUT_REASONING: float = 60.0
    AI_TIMEOUT_VISION: float = 45.0
    AI_TIMEOUT_EMBEDDING: float = 10.0
    AI_TIMEOUT_RETRIEVAL: float = 15.0
    AI_TIMEOUT_OCR: float = 30.0
    AI_TIMEOUT_CLINICAL: float = 10.0
    AI_TIMEOUT_SAFETY: float = 5.0

    # ── OCR ───────────────────────────────────────────────────────────────────
    OCR_MAX_RETRIES: int = 3
    OCR_RETRY_DELAY_SECONDS: float = 1.0
    OCR_FALLBACK_ENABLED: bool = True
    OCR_PRIMARY_PROVIDER: str = "paddleocr"
    OCR_FALLBACK_PROVIDER: str = "easyocr"

    # ── Upload ────────────────────────────────────────────────────────────────
    UPLOAD_MAX_SIZE_MB: int = 20
    UPLOAD_ALLOWED_MIME_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "image/bmp", "image/tiff",
        "application/pdf",
    ]
    UPLOAD_ALLOWED_EXTENSIONS: List[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".pdf"
    ]

    # ── AI Temperature ────────────────────────────────────────────────────────
    AI_TEMPERATURE_CHAT: float = 0.3
    AI_TEMPERATURE_REASONING: float = 0.0
    AI_TEMPERATURE_CREATIVE: float = 0.7

    # ── Context Lengths ───────────────────────────────────────────────────────
    AI_CONTEXT_LENGTH_SHORT: int = 4096
    AI_CONTEXT_LENGTH_MEDIUM: int = 8192
    AI_CONTEXT_LENGTH_LONG: int = 32768

    # ── Vision Generation ─────────────────────────────────────────────────────
    # Output-token budget for the vision model. Gemini 3.x/2.5 Flash are
    # "thinking" models whose maxOutputTokens budget is shared between internal
    # reasoning and the visible answer, so this must be generous to allow a full
    # doctor-grade lab/prescription report to complete.
    AI_MAX_TOKENS_VISION: int = 16384
    # Hard upper bound (seconds) applied on top of AI_TIMEOUT_VISION to avoid
    # waiting indefinitely on a single vision generation.
    AI_MAX_TIMEOUT_VISION: float = 90.0

    # ── Retrieval ─────────────────────────────────────────────────────────────
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_FETCH_K: int = 12
    RETRIEVAL_SCORE_THRESHOLD: float = 0.7
    RETRIEVAL_RERANKER_ENABLED: bool = False
    RETRIEVAL_HYBRID_ENABLED: bool = False

    # ── Memory ────────────────────────────────────────────────────────────────
    MEMORY_CONVERSATION_LIMIT: int = 50
    MEMORY_SUMMARY_LIMIT: int = 1000
    MEMORY_ENABLED: bool = True
    MEMORY_PATIENT_ENABLED: bool = True
    MEMORY_CLINICAL_ENABLED: bool = True

    # ── Confidence Thresholds ─────────────────────────────────────────────────
    CONFIDENCE_THRESHOLD_HIGH: float = 0.8
    CONFIDENCE_THRESHOLD_MEDIUM: float = 0.5
    CONFIDENCE_THRESHOLD_LOW: float = 0.3

    # ── Safety Layer ──────────────────────────────────────────────────────────
    SAFETY_ENABLED: bool = True
    SAFETY_HALLUCINATION_THRESHOLD: float = 0.7
    SAFETY_MIN_CONFIDENCE_TO_RESPOND: float = 0.2
    SAFETY_REQUIRE_DISCLAIMER: bool = True
    SAFETY_BLOCK_UNSAFE_REQUESTS: bool = True

    # ── Performance Budgets (seconds) ─────────────────────────────────────────
    PERF_BUDGET_UPLOAD_CLASSIFY_S: float = 0.5
    PERF_BUDGET_MEMORY_RETRIEVAL_S: float = 0.5
    PERF_BUDGET_CHAT_RESPONSE_S: float = 3.0
    PERF_BUDGET_OCR_S: float = 5.0
    PERF_BUDGET_VISION_S: float = 8.0
    PERF_BUDGET_REPORT_S: float = 10.0
    EXECUTION_TIME_WARNING: float = 5.0
    EXECUTION_TIME_CRITICAL: float = 10.0

    # ── Observability ─────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # 'json' | 'text'
    TRACING_ENABLED: bool = False
    METRICS_ENABLED: bool = True

    # ── Feature Flags ─────────────────────────────────────────────────────────
    FEATURE_OCR_ENABLED: bool = True
    FEATURE_VISION_ENABLED: bool = True
    FEATURE_CLINICAL_INTELLIGENCE_ENABLED: bool = True
    FEATURE_AGENTS_ENABLED: bool = True
    FEATURE_SAFETY_ENABLED: bool = True
    FEATURE_EVALUATION_ENABLED: bool = False
    FEATURE_DIAGNOSIS_ENABLED: bool = True
    FEATURE_PRESCRIPTION_ENABLED: bool = True
    FEATURE_LAB_ENABLED: bool = True
    FEATURE_REPORT_ENABLED: bool = True
    FEATURE_DRUG_CHECK_ENABLED: bool = True
    FEATURE_LONGITUDINAL_MEMORY_ENABLED: bool = True

    model_config = SettingsConfigDict(
    env_file=".env",
    case_sensitive=True,
    )
    @field_validator("GROQ_API_KEY", "PINECONE_API_KEY", "DATABASE_URL")
    @classmethod
    def enforce_production_keys(cls, value, info: ValidationInfo):
        env = info.data.get("ENV") if info.data else "development"

        if env == "production" and not value:
            raise ValueError(f"{info.field_name} must be set in production.")

        return value


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
