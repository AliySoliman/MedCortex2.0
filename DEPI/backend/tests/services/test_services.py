import pytest
from unittest.mock import MagicMock, patch
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.memory_service import MemoryService


def test_conversation_service(db_session, test_user):
    service = ConversationService(db_session)
    
    # Create conversation
    conv = service.create_conversation(user_id=test_user.id, title="Consultation")
    assert conv.id is not None
    
    # Rename
    renamed = service.rename_conversation(conv.id, "New Name")
    assert renamed.title == "New Name"
    
    # Stats
    stats = service.get_conversation_stats(test_user.id)
    assert stats["active_conversations"] == 1
    assert stats["total_messages"] == 0


def test_message_service(db_session, test_user):
    conv_service = ConversationService(db_session)
    msg_service = MessageService(db_session)
    
    conv = conv_service.create_conversation(user_id=test_user.id)
    
    # Store message
    msg = msg_service.store_message(
        conversation_id=conv.id,
        role="user",
        content="I feel sick",
    )
    assert msg.id is not None
    assert msg.role == "user"
    
    # Conversation last active is updated
    db_session.refresh(conv)
    assert conv.last_active_at is not None


def test_memory_service_inject_memory(db_session, test_user):
    memory_service = MemoryService(db_session)
    conv_service = ConversationService(db_session)
    
    conv = conv_service.create_conversation(user_id=test_user.id)
    
    # Add some memory entries manually via DBUserMemory
    memory_service.user_memory.store_user_info(
        str(test_user.id),
        {"medications": ["Aspirin"], "source_conversation_id": conv.id}
    )
    
    # Inject memory
    injected = memory_service.inject_memory(test_user.id, conv.id)
    assert "user_preferences" in injected
    assert "persistent_memory" in injected
    assert "medications" in injected["persistent_memory"].lower()
