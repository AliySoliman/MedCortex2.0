from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.utils.security import get_current_user
from app.services.message_service import MessageService
from app.services.conversation_service import ConversationService
from app.schemas.message import MessageCreate, MessageOut, MessageListOut


router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageOut:
    conv_service = ConversationService(db)
    conversation = conv_service.get_conversation(conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_service = MessageService(db)
    return msg_service.store_message(
        conversation_id=conversation_id,
        role=payload.role,
        content=payload.content,
        provider=payload.provider,
        model=payload.model,
        execution_time=payload.execution_time,
        token_usage=payload.token_usage,
        citations=payload.citations,
        attachments=payload.attachments,
        workflow=payload.workflow,
        metadata_json=payload.metadata_json,
    )


@router.get("", response_model=MessageListOut)
def list_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageListOut:
    conv_service = ConversationService(db)
    conversation = conv_service.get_conversation(conversation_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    msg_service = MessageService(db)
    messages = msg_service.list_messages(conversation_id, limit, offset)
    
    # Total message count
    from app.models.message import Message
    total = db.query(Message).filter(Message.conversation_id == conversation_id).count()
    
    return MessageListOut(messages=messages, total=total)
