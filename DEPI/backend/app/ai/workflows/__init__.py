# backend/app/ai/workflows/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Workflows Module
# Predefined AI workflows for common medical tasks
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.workflows.workflow_manager import WorkflowManager

__all__ = ["WorkflowManager"]
