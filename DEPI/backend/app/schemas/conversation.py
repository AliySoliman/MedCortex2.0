from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ConfigDict


class ConversationBase(BaseModel):
    title: Optional[str] = "New Conversation"
    metadata_json: Optional[Dict[str, Any]] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None  # active, archived, deleted
    metadata_json: Optional[Dict[str, Any]] = None


class ConversationOut(ConversationBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationListOut(BaseModel):
    conversations: List[ConversationOut]
    total: int


class ConversationStats(BaseModel):
    active_conversations: int
    archived_conversations: int
    total_messages: int
