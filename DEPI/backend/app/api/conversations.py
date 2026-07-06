from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.utils.security import get_current_user
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationOut,
    ConversationListOut,
    ConversationStats,
)
from app.schemas.message import MessageOut


router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationOut:
    service = ConversationService(db)
    return service.create_conversation(
        user_id=current_user.id,
        title=payload.title or "New Conversation",
        metadata_json=payload.metadata_json,
    )


@router.get("", response_model=ConversationListOut)
def list_conversations(
    status: str = "active",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationListOut:
    service = ConversationService(db)
    conversations = service.list_conversations(
        user_id=current_user.id, status=status, limit=limit, offset=offset
    )
    # Total count calculation
    from app.models.conversation import Conversation
    total = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id, Conversation.status == status)
        .count()
    )
    return ConversationListOut(conversations=conversations, total=total)


@router.get("/stats", response_model=ConversationStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationStats:
    service = ConversationService(db)
    stats = service.get_conversation_stats(current_user.id)
    return ConversationStats(**stats)


@router.get("/{id}", response_model=ConversationOut)
def get_conversation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationOut:
    service = ConversationService(db)
    conversation = service.get_conversation(id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


@router.get("/{id}/messages", response_model=List[MessageOut])
def get_conversation_messages(
    id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MessageOut]:
    conv_service = ConversationService(db)
    conversation = conv_service.get_conversation(id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    msg_service = MessageService(db)
    return msg_service.list_messages(conversation_id=id, limit=limit, offset=offset)


@router.patch("/{id}", response_model=ConversationOut)
def update_conversation(
    id: int,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationOut:
    service = ConversationService(db)
    conversation = service.get_conversation(id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    updated = service.repo.update(
        conversation_id=id,
        title=payload.title,
        status=payload.status,
        metadata_json=payload.metadata_json,
    )
    return updated


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationService(db)
    conversation = service.get_conversation(id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    service.delete_conversation(id)
    return None
