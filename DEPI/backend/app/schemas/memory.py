from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ConfigDict


class MemoryEntryOut(BaseModel):
    id: int
    user_id: int
    entry_type: str
    content: str
    source_conversation_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryContext(BaseModel):
    user_preferences: str
    persistent_memory: str
    conversation_summary: str
    recent_messages: List[Dict[str, str]]
