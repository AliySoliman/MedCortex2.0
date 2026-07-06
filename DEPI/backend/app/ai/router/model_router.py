# backend/app/ai/router/model_router.py
# ─────────────────────────────────────────────────────────────────────────────
# Model Router
# Routes requests to appropriate AI models based on task requirements
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from enum import Enum


class TaskType(Enum):
    """AI task types."""
    CHAT = "chat"
    REASONING = "reasoning"
    VISION = "vision"
    REWRITE = "rewrite"
    OCR = "ocr"
    EMBEDDING = "embedding"


class ModelRouter:
    """Routes tasks to appropriate AI models."""
    
    def __init__(self):
        self._task_model_mapping: Dict[TaskType, str] = {
            TaskType.CHAT: "llama-3.3-70b-versatile",
            TaskType.REASONING: "qwen-3.6-27b",
            TaskType.VISION: "llama-4-scout",
            TaskType.REWRITE: "llama-3.1-8b",
            TaskType.OCR: "paddleocr",
            TaskType.EMBEDDING: "bge-large-en-v1.5",
        }
    
    def get_model_for_task(self, task_type: TaskType) -> str:
        """Get the appropriate model for a task type."""
        return self._task_model_mapping.get(task_type, "llama-3.3-70b-versatile")
    
    def route(self, task_type: TaskType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route task to appropriate model.
        
        Placeholder for future implementation.
        """
        model = self.get_model_for_task(task_type)
        return {
            "task_type": task_type.value,
            "model": model,
            "input_data": input_data,
        }
