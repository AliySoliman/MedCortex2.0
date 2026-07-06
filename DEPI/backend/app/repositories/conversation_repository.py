from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    """Repository for Conversation data access operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        title: str = "New Conversation",
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=title,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_active_at=datetime.utcnow(),
            metadata_json=metadata_json,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def list_by_user(
        self,
        user_id: int,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.status == status,
            )
            .order_by(Conversation.last_active_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update(
        self,
        conversation_id: int,
        title: Optional[str] = None,
        status: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Optional[Conversation]:
        conversation = self.get_by_id(conversation_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if status is not None:
            conversation.status = status
        if metadata_json is not None:
            conversation.metadata_json = metadata_json

        conversation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def soft_delete(self, conversation_id: int) -> bool:
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.status = "deleted"
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def archive(self, conversation_id: int) -> bool:
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.status = "archived"
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def restore(self, conversation_id: int) -> bool:
        conversation = self.get_by_id(conversation_id)
        if conversation:
            conversation.status = "active"
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def search(
        self,
        user_id: int,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        # Search in conversation titles or message contents
        like_query = f"%{query}%"
        return (
            self.db.query(Conversation)
            .outerjoin(Message, Conversation.id == Message.conversation_id)
            .filter(
                Conversation.user_id == user_id,
                Conversation.status != "deleted",
                or_(
                    Conversation.title.like(like_query),
                    Message.content.like(like_query),
                ),
            )
            .distinct()
            .order_by(Conversation.last_active_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_stats(self, user_id: int) -> Dict[str, Any]:
        stats = (
            self.db.query(
                Conversation.status,
                func.count(Conversation.id).label("count"),
            )
            .filter(Conversation.user_id == user_id)
            .group_by(Conversation.status)
            .all()
        )
        stats_dict = {status: count for status, count in stats}
        
        # Add message count
        msg_count = (
            self.db.query(func.count(Message.id))
            .join(Conversation, Conversation.id == Message.conversation_id)
            .filter(Conversation.user_id == user_id)
            .scalar()
        ) or 0

        return {
            "active_conversations": stats_dict.get("active", 0),
            "archived_conversations": stats_dict.get("archived", 0),
            "total_messages": msg_count,
        }

    def update_last_active(self, conversation_id: int) -> bool:
        conversation = self.get_by_id(conversation_id)
        if conversation:
            now = datetime.utcnow()
            conversation.last_active_at = now
            conversation.updated_at = now
            self.db.commit()
            return True
        return False
