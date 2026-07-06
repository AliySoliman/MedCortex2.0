# backend/app/ai/router/workflow_router.py
# ─────────────────────────────────────────────────────────────────────────────
# Workflow Router
# Routes requests to specific workflow implementations
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional, Callable
from enum import Enum


class WorkflowType(Enum):
    """Available workflow types."""
    CHAT = "chat"
    VISION = "vision"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    LAB = "lab"
    REPORT = "report"


class WorkflowRouter:
    """Routes requests to workflow implementations."""
    
    def __init__(self):
        self._workflows: Dict[WorkflowType, Callable] = {}
    
    def register_workflow(self, workflow_type: WorkflowType, handler: Callable):
        """Register a workflow handler."""
        self._workflows[workflow_type] = handler
    
    def route(self, workflow_type: WorkflowType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to appropriate workflow.
        
        Placeholder for future implementation.
        """
        handler = self._workflows.get(workflow_type)
        if not handler:
            return {
                "success": False,
                "error": f"Workflow {workflow_type} not implemented"
            }
        
        return handler(input_data)
    
    def get_available_workflows(self) -> list[str]:
        """Get list of available workflow types."""
        return [w.value for w in WorkflowType]
