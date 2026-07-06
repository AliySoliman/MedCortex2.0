from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.utils.security import get_current_user
from app.services.history_service import HistoryService
from app.schemas.history import (
    HistorySearchResult,
    FavoriteCreate,
    FavoriteOut,
    FeedbackCreate,
    FeedbackOut,
)


router = APIRouter(tags=["History, Favorites, & Feedback"])


@router.get("/history/search", response_model=List[HistorySearchResult])
def search_history(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[HistorySearchResult]:
    service = HistoryService(db)
    results = service.search_history(
        user_id=current_user.id, query=q, limit=limit, offset=offset
    )
    return [HistorySearchResult(**r) for r in results]


@router.post("/favorites", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteOut:
    # Verify the message belongs to a conversation owned by the current user
    from app.models.message import Message
    from app.models.conversation import Conversation
    msg = (
        db.query(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .filter(Message.id == payload.message_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied",
        )

    service = HistoryService(db)
    fav = service.add_favorite(
        user_id=current_user.id, message_id=payload.message_id, note=payload.note
    )
    return fav


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackOut:
    # Verify the message belongs to a conversation owned by the current user
    from app.models.message import Message
    from app.models.conversation import Conversation
    msg = (
        db.query(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .filter(Message.id == payload.message_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied",
        )

    if not (1 <= payload.rating <= 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5",
        )

    service = HistoryService(db)
    fb = service.add_feedback(
        user_id=current_user.id,
        message_id=payload.message_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    return fb
