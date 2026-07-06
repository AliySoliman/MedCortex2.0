from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.models.message import Message


class MessageService:
    """Service for managing Message workflows."""

    def __init__(self, db: Session):
        self.db = db
        self.message_repo = MessageRepository(db)
        self.conversation_repo = ConversationRepository(db)

    def store_message(
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
        message = self.message_repo.create(
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
        )
        # Update last active timestamp on the conversation
        self.conversation_repo.update_last_active(conversation_id)
        return message

    def list_messages(
        self,
        conversation_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Message]:
        return self.message_repo.list_by_conversation(conversation_id, limit, offset)

    def get_recent_messages(self, conversation_id: int, limit: int = 10) -> List[Message]:
        return self.message_repo.get_recent(conversation_id, limit)
