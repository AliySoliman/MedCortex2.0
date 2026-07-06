# backend/app/ai/tasks/chat_task.py
# ─────────────────────────────────────────────────────────────────────────────
# Chat Task
# Task representation for chat interactions
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from app.ai.tasks.task import AITask
from app.ai.shared.types import TaskType, Provider


class ChatTask(AITask):
    """Task for chat-based medical consultations."""
    
    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[Provider] = None,
        model: Optional[str] = None,
    ):
        input_data = {
            "message": message,
            "user_id": user_id,
            "context": context or {},
        }
        super().__init__(TaskType.CHAT, input_data, provider, model)
        self.message = message
        self.user_id = user_id
        self.context = context or {}
    
    def validate_input(self) -> bool:
        """Validate chat input data."""
        return bool(self.message and isinstance(self.message, str))
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute chat task.
        
        Placeholder for future implementation.
        """
        return {
            "status": "not_implemented",
            "message": self.message,
        }
