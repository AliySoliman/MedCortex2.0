from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.conversation_repository import ConversationRepository
from app.models.conversation import Conversation


class ConversationService:
    """Service for managing Conversation workflows."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepository(db)

    def create_conversation(
        self,
        user_id: int,
        title: str = "New Conversation",
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        return self.repo.create(user_id, title, metadata_json)

    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        return self.repo.get_by_id(conversation_id)

    def list_conversations(
        self,
        user_id: int,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        return self.repo.list_by_user(user_id, status, limit, offset)

    def rename_conversation(self, conversation_id: int, new_title: str) -> Optional[Conversation]:
        return self.repo.update(conversation_id, title=new_title)

    def archive_conversation(self, conversation_id: int) -> bool:
        return self.repo.archive(conversation_id)

    def restore_conversation(self, conversation_id: int) -> bool:
        return self.repo.restore(conversation_id)

    def delete_conversation(self, conversation_id: int) -> bool:
        return self.repo.soft_delete(conversation_id)

    def search_conversations(
        self,
        user_id: int,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        return self.repo.search(user_id, query, limit, offset)

    def get_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        return self.repo.get_stats(user_id)

    def update_last_active(self, conversation_id: int) -> bool:
        return self.repo.update_last_active(conversation_id)
