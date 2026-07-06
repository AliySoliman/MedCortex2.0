# backend/app/ai/tasks/diagnosis_task.py
# ─────────────────────────────────────────────────────────────────────────────
# Diagnosis Task
# Task representation for medical diagnosis
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional, List
from app.ai.tasks.task import AITask
from app.ai.shared.types import TaskType, Provider


class DiagnosisTask(AITask):
    """Task for medical diagnosis."""
    
    def __init__(
        self,
        symptoms: List[str],
        patient_data: Optional[Dict[str, Any]] = None,
        provider: Optional[Provider] = None,
        model: Optional[str] = None,
    ):
        input_data = {
            "symptoms": symptoms,
            "patient_data": patient_data or {},
        }
        super().__init__(TaskType.REASONING, input_data, provider, model)
        self.symptoms = symptoms
        self.patient_data = patient_data or {}
    
    def validate_input(self) -> bool:
        """Validate diagnosis input data."""
        return bool(self.symptoms and isinstance(self.symptoms, list))
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute diagnosis task.
        
        Placeholder for future implementation.
        """
        return {
            "status": "not_implemented",
            "symptoms": self.symptoms,
        }
