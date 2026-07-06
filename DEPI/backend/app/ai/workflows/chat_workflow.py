# backend/app/ai/workflows/chat_workflow.py
# ─────────────────────────────────────────────────────────────────────────────
# Chat Workflow
# Chat-based medical consultation workflow
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class ChatWorkflow(ABC):
    """Abstract base class for chat workflows."""
    
    @abstractmethod
    def execute(
        self,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute chat workflow.
        
        Placeholder for future implementation.
        """
        pass


class ChatWorkflowService:
    """Service for chat workflow operations."""
    
    def __init__(self, workflow: Optional[ChatWorkflow] = None):
        self.workflow = workflow
    
    def run(
        self,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run chat workflow.
        
        Placeholder for future implementation.
        """
        return {
            "status": "not_implemented",
            "message": message,
        }
