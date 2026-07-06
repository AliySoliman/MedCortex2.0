from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.message import Message


class MessageRepository:
    """Repository for Message data access operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: int,
        role: str,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        execution_time: Optional[float] = None,
        token_usage: Optional[Dict[str, Any]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        workflow: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            provider=provider,
            model=model,
            execution_time=execution_time,
            token_usage=token_usage,
            citations=citations,
            attachments=attachments,
            workflow=workflow,
            metadata_json=metadata_json,
            timestamp=datetime.utcnow(),
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_id(self, message_id: int) -> Optional[Message]:
        return self.db.query(Message).filter(Message.id == message_id).first()

    def list_by_conversation(
        self,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def bulk_create(self, messages: List[Message]) -> List[Message]:
        self.db.add_all(messages)
        self.db.commit()
        for msg in messages:
            self.db.refresh(msg)
        return messages

    def get_recent(self, conversation_id: int, limit: int = 10) -> List[Message]:
        # Return recent messages, but ordered chronologically (asc) for PromptBuilder consumption
        recent = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(recent))
