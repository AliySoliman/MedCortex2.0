# backend/app/ai/tasks/report_task.py
# ─────────────────────────────────────────────────────────────────────────────
# Report Task
# Task representation for report generation
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from app.ai.tasks.task import AITask
from app.ai.shared.types import TaskType, Provider


class ReportTask(AITask):
    """Task for medical report generation."""
    
    def __init__(
        self,
        report_type: str,
        data: Dict[str, Any],
        provider: Optional[Provider] = None,
        model: Optional[str] = None,
    ):
        input_data = {
            "report_type": report_type,
            "data": data,
        }
        super().__init__(TaskType.CHAT, input_data, provider, model)
        self.report_type = report_type
        self.data = data
    
    def validate_input(self) -> bool:
        """Validate report input data."""
        return bool(self.report_type and self.data)
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute report task.
        
        Placeholder for future implementation.
        """
        return {
            "status": "not_implemented",
            "report_type": self.report_type,
        }
