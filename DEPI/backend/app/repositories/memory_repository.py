from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.memory_entry import MemoryEntry
from app.models.conversation_summary import ConversationSummary


class MemoryRepository:
    """Repository for Memory Entry and Conversation Summary data access operations."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_entry(
        self,
        user_id: int,
        entry_type: str,
        content: str,
        source_conversation_id: Optional[int] = None,
    ) -> MemoryEntry:
        # Check if identical content exists for user and type
        existing = (
            self.db.query(MemoryEntry)
            .filter(
                MemoryEntry.user_id == user_id,
                MemoryEntry.entry_type == entry_type,
                MemoryEntry.content == content,
            )
            .first()
        )
        if existing:
            existing.updated_at = datetime.utcnow()
            if source_conversation_id:
                existing.source_conversation_id = source_conversation_id
            self.db.commit()
            self.db.refresh(existing)
            return existing

        entry = MemoryEntry(
            user_id=user_id,
            entry_type=entry_type,
            content=content,
            source_conversation_id=source_conversation_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_by_user(self, user_id: int) -> List[MemoryEntry]:
        return (
            self.db.query(MemoryEntry)
            .filter(MemoryEntry.user_id == user_id)
            .order_by(MemoryEntry.updated_at.desc())
            .all()
        )

    def list_by_type(self, user_id: int, entry_type: str) -> List[MemoryEntry]:
        return (
            self.db.query(MemoryEntry)
            .filter(
                MemoryEntry.user_id == user_id,
                MemoryEntry.entry_type == entry_type,
            )
            .order_by(MemoryEntry.updated_at.desc())
            .all()
        )

    def delete_entry(self, entry_id: int) -> bool:
        entry = self.db.query(MemoryEntry).filter(MemoryEntry.id == entry_id).first()
        if entry:
            self.db.delete(entry)
            self.db.commit()
            return True
        return False

    def get_summary_for_conversation(self, conversation_id: int) -> Optional[ConversationSummary]:
        return (
            self.db.query(ConversationSummary)
            .filter(ConversationSummary.conversation_id == conversation_id)
            .order_by(ConversationSummary.created_at.desc())
            .first()
        )

    def create_summary(
        self,
        conversation_id: int,
        summary: str,
        message_count_at_summary: int,
    ) -> ConversationSummary:
        conv_summary = ConversationSummary(
            conversation_id=conversation_id,
            summary=summary,
            message_count_at_summary=message_count_at_summary,
            created_at=datetime.utcnow(),
        )
        self.db.add(conv_summary)
        self.db.commit()
        self.db.refresh(conv_summary)
        return conv_summary
