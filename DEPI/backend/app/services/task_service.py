from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.task_repository import TaskRepository
from app.models.ai_task import AITask


class TaskService:
    """Service for managing AI Task workflows."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TaskRepository(db)

    def create_task(
        self,
        conversation_id: int,
        task_type: str,
        message_id: Optional[int] = None,
        status: str = "pending",
    ) -> AITask:
        return self.repo.create(conversation_id, task_type, message_id, status)

    def update_task_status(
        self,
        task_id: int,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[AITask]:
        return self.repo.update_status(task_id, status, result, error)

    def get_task(self, task_id: int) -> Optional[AITask]:
        return self.repo.get_by_id(task_id)

    def list_tasks_by_conversation(self, conversation_id: int) -> List[AITask]:
        return self.repo.list_by_conversation(conversation_id)
