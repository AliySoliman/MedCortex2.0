from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.ai_task import AITask


class TaskRepository:
    """Repository for AI Task data access operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: int,
        task_type: str,
        message_id: Optional[int] = None,
        status: str = "pending",
    ) -> AITask:
        task = AITask(
            conversation_id=conversation_id,
            message_id=message_id,
            task_type=task_type,
            status=status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_status(
        self,
        task_id: int,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[AITask]:
        task = self.get_by_id(task_id)
        if not task:
            return None

        task.status = status
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        task.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: int) -> Optional[AITask]:
        return self.db.query(AITask).filter(AITask.id == task_id).first()

    def list_by_conversation(self, conversation_id: int) -> List[AITask]:
        return (
            self.db.query(AITask)
            .filter(AITask.conversation_id == conversation_id)
            .order_by(AITask.created_at.desc())
            .all()
        )
