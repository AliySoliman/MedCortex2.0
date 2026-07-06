from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    role: str
    content: str
    provider: Optional[str] = None
    model: Optional[str] = None
    execution_time: Optional[float] = None
    token_usage: Optional[Dict[str, Any]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    workflow: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class MessageOut(MessageCreate):
    id: int
    conversation_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListOut(BaseModel):
    messages: List[MessageOut]
    total: int
