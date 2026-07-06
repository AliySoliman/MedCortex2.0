# backend/app/ai/workflows/workflow_manager.py
# ─────────────────────────────────────────────────────────────────────────────
# Workflow Manager
# Manages predefined AI workflows for medical tasks
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional, Callable
from enum import Enum


class WorkflowType(Enum):
    """Types of available workflows."""
    FULL_CONSULTATION = "full_consultation"
    SYMPTOM_CHECK = "symptom_check"
    LIFESTYLE_ADVICE = "lifestyle_advice"
    DOCTOR_FINDER = "doctor_finder"


class WorkflowManager:
    """Manages and executes AI workflows."""
    
    def __init__(self):
        self._workflows: Dict[WorkflowType, Callable] = {}
    
    def register_workflow(self, workflow_type: WorkflowType, handler: Callable):
        """Register a workflow handler."""
        self._workflows[workflow_type] = handler
    
    def execute_workflow(
        self,
        workflow_type: WorkflowType,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a workflow by type.
        
        Placeholder for future implementation.
        Will integrate with LangGraph when available.
        """
        handler = self._workflows.get(workflow_type)
        if not handler:
            return {
                "status": "error",
                "message": f"Workflow {workflow_type} not implemented"
            }
        
        return handler(input_data)
    
    def get_available_workflows(self) -> list[str]:
        """Get list of available workflow names."""
        return [w.value for w in WorkflowType]
