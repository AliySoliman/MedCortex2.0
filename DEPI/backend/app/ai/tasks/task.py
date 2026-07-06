# backend/app/ai/tasks/task.py
# ─────────────────────────────────────────────────────────────────────────────
# AI Task Abstraction
# Base task representation for all AI interactions
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime
from app.ai.shared.types import TaskType, Provider


class AITask(ABC):
    """
    Abstract base class for AI tasks.
    
    Every future interaction should be represented as a task.
    Examples: Chat, Medical Image Analysis, Prescription Analysis, 
    Lab Interpretation, PDF Analysis, Drug Interaction, Report Generation.
    """
    
    def __init__(
        self,
        task_type: TaskType,
        input_data: Dict[str, Any],
        provider: Optional[Provider] = None,
        model: Optional[str] = None,
    ):
        self.task_type = task_type
        self.input_data = input_data
        self.provider = provider or Provider.GROQ
        self.model = model
        self.created_at = datetime.utcnow()
        self.execution_time: Optional[float] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
    
    @abstractmethod
    def validate_input(self) -> bool:
        """
        Validate input data for the task.
        
        Placeholder for future implementation.
        """
        pass
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the task.
        
        Placeholder for future implementation.
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_type": self.task_type.value,
            "input_data": self.input_data,
            "provider": self.provider.value,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "execution_time": self.execution_time,
            "result": self.result,
            "error": self.error,
        }
