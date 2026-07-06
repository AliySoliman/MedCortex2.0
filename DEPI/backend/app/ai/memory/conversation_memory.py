from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime


class ConversationMemory(ABC):
    """Abstract base class for conversation memory engines."""
    
    @abstractmethod
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a message to conversation memory."""
        pass
    
    @abstractmethod
    def get_messages(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Get conversation messages."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear conversation memory."""
        pass


class InMemoryConversationMemory(ConversationMemory):
    """In-memory concrete implementation of ConversationMemory."""

    def __init__(self):
        self.messages: List[Dict[str, Any]] = []

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.messages.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        })

    def get_messages(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        msgs = self.messages
        if limit:
            msgs = msgs[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    def clear(self):
        self.messages.clear()


class DBConversationMemory(ConversationMemory):
    """Database-backed implementation of ConversationMemory."""

    def __init__(self, db_session, conversation_id: int):
        self.db = db_session
        self.conversation_id = conversation_id

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        from app.models.message import Message
        msg = Message(
            conversation_id=self.conversation_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata_json=metadata
        )
        self.db.add(msg)
        self.db.commit()

    def get_messages(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        from app.models.message import Message
        query = (
            self.db.query(Message)
            .filter(Message.conversation_id == self.conversation_id)
            .order_by(Message.timestamp.asc())
        )
        if limit:
            # Get latest limit, but still ordered ascending
            # SQLite / sqlalchemy doesn't directly support LIMIT on subquery without sorting desc first
            subquery = (
                self.db.query(Message)
                .filter(Message.conversation_id == self.conversation_id)
                .order_by(Message.timestamp.desc())
                .limit(limit)
                .subquery()
            )
            # Re-order ascending
            from sqlalchemy import select
            stmt = select(subquery).order_by(subquery.c.timestamp.asc())
            results = self.db.execute(stmt).all()
            return [{"role": r.role, "content": r.content} for r in results]
        
        results = query.all()
        return [{"role": r.role, "content": r.content} for r in results]

    def clear(self):
        from app.models.message import Message
        self.db.query(Message).filter(Message.conversation_id == self.conversation_id).delete()
        self.db.commit()


class ConversationMemoryService:
    """Service for conversation memory operations."""
    
    def __init__(self, memory: Optional[ConversationMemory] = None):
        self.memory = memory or InMemoryConversationMemory()
    
    def add(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.memory.add_message(role, content, metadata)
    
    def get(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        return self.memory.get_messages(limit)

    def clear(self):
        self.memory.clear()
