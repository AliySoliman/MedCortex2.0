from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.favorite import Favorite
from app.models.feedback import Feedback


class HistoryService:
    """Service for handling historical search, feedback, and favorites."""

    def __init__(self, db: Session):
        self.db = db

    def search_history(
        self,
        user_id: int,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search across conversation titles and message contents."""
        like_query = f"%{query}%"
        # Find matching conversations
        conversations = (
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
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for conv in conversations:
            # Get latest matching message or just the conversation title
            matched_msg = (
                self.db.query(Message)
                .filter(
                    Message.conversation_id == conv.id,
                    Message.content.like(like_query),
                )
                .first()
            )
            
            results.append({
                "conversation_id": conv.id,
                "title": conv.title,
                "last_active_at": conv.last_active_at,
                "matched_text": matched_msg.content if matched_msg else None,
                "matched_role": matched_msg.role if matched_msg else None,
            })
            
        return results

    def add_favorite(self, user_id: int, message_id: int, note: Optional[str] = None) -> Favorite:
        # Check if already favorited
        existing = (
            self.db.query(Favorite)
            .filter(Favorite.user_id == user_id, Favorite.message_id == message_id)
            .first()
        )
        if existing:
            if note is not None:
                existing.note = note
                self.db.commit()
                self.db.refresh(existing)
            return existing

        fav = Favorite(
            user_id=user_id,
            message_id=message_id,
            note=note,
            created_at=datetime.utcnow(),
        )
        self.db.add(fav)
        self.db.commit()
        self.db.refresh(fav)
        return fav

    def add_feedback(
        self,
        user_id: int,
        message_id: int,
        rating: int,
        comment: Optional[str] = None,
    ) -> Feedback:
        existing = (
            self.db.query(Feedback)
            .filter(Feedback.user_id == user_id, Feedback.message_id == message_id)
            .first()
        )
        if existing:
            existing.rating = rating
            existing.comment = comment
            existing.created_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        fb = Feedback(
            user_id=user_id,
            message_id=message_id,
            rating=rating,
            comment=comment,
            created_at=datetime.utcnow(),
        )
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb
