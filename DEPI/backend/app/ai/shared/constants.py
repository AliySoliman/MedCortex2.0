# backend/app/ai/shared/constants.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared Constants
# Application-wide constants for AI operations
# ─────────────────────────────────────────────────────────────────────────────

# Provider names
PROVIDER_GROQ = "groq"
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_HUGGINGFACE = "huggingface"

# Task types
TASK_CHAT = "chat"
TASK_REASONING = "reasoning"
TASK_VISION = "vision"
TASK_REWRITE = "rewrite"
TASK_OCR = "ocr"
TASK_EMBEDDING = "embedding"

# Workflow names
WORKFLOW_CHAT = "chat"
WORKFLOW_VISION = "vision"
WORKFLOW_DIAGNOSIS = "diagnosis"
WORKFLOW_PRESCRIPTION = "prescription"
WORKFLOW_LAB = "lab"
WORKFLOW_REPORT = "report"

# Confidence thresholds
CONFIDENCE_HIGH = 0.8
CONFIDENCE_MEDIUM = 0.5
CONFIDENCE_LOW = 0.3

# Execution time thresholds (seconds)
EXECUTION_TIME_WARNING = 5.0
EXECUTION_TIME_CRITICAL = 10.0

# Memory limits
CONVERSATION_MEMORY_LIMIT = 50
SUMMARY_MEMORY_LIMIT = 1000

# Retrieval settings
DEFAULT_RETRIEVAL_K = 5
DEFAULT_RETRIEVAL_FETCH_K = 12

# Model context lengths
CONTEXT_LENGTH_SHORT = 4096
CONTEXT_LENGTH_MEDIUM = 8192
CONTEXT_LENGTH_LONG = 32768
CONTEXT_LENGTH_VERY_LONG = 131072

# Temperature settings
TEMPERATURE_PRECISE = 0.0
TEMPERATURE_BALANCED = 0.3
TEMPERATURE_CREATIVE = 0.7
