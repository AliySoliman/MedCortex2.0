from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class HistorySearchResult(BaseModel):
    conversation_id: int
    title: str
    last_active_at: datetime
    matched_text: Optional[str] = None
    matched_role: Optional[str] = None


class FavoriteCreate(BaseModel):
    message_id: int
    note: Optional[str] = None


class FavoriteOut(BaseModel):
    id: int
    user_id: int
    message_id: int
    note: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    message_id: int
    rating: int  # 1 to 5
    comment: Optional[str] = None


class FeedbackOut(BaseModel):
    id: int
    user_id: int
    message_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
