import pytest
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.memory_repository import MemoryRepository


def test_conversation_repository(db_session, test_user):
    conv_repo = ConversationRepository(db_session)
    
    # 1. Create
    conv = conv_repo.create(user_id=test_user.id, title="Test Conversation")
    assert conv.id is not None
    assert conv.title == "Test Conversation"
    assert conv.status == "active"
    
    # 2. Get by ID
    fetched = conv_repo.get_by_id(conv.id)
    assert fetched.id == conv.id
    
    # 3. Update Title
    updated = conv_repo.update(conv.id, title="Updated Title")
    assert updated.title == "Updated Title"
    
    # 4. List by user
    lst = conv_repo.list_by_user(test_user.id)
    assert len(lst) == 1
    assert lst[0].id == conv.id

    # 5. Archive
    conv_repo.archive(conv.id)
    assert conv_repo.get_by_id(conv.id).status == "archived"

    # 6. Restore
    conv_repo.restore(conv.id)
    assert conv_repo.get_by_id(conv.id).status == "active"

    # 7. Soft delete
    conv_repo.soft_delete(conv.id)
    assert conv_repo.get_by_id(conv.id).status == "deleted"


def test_message_repository(db_session, test_user):
    conv_repo = ConversationRepository(db_session)
    msg_repo = MessageRepository(db_session)
    
    conv = conv_repo.create(user_id=test_user.id)
    
    # Create message
    msg = msg_repo.create(
        conversation_id=conv.id,
        role="user",
        content="I have symptoms",
        provider="groq",
        model="llama3",
    )
    assert msg.id is not None
    assert msg.content == "I have symptoms"
    
    # List messages
    msgs = msg_repo.list_by_conversation(conv.id)
    assert len(msgs) == 1
    assert msgs[0].id == msg.id
    
    # Get recent
    recent = msg_repo.get_recent(conv.id, limit=5)
    assert len(recent) == 1
    assert recent[0].id == msg.id


def test_memory_repository(db_session, test_user):
    mem_repo = MemoryRepository(db_session)
    
    # 1. Upsert memory entry
    entry = mem_repo.upsert_entry(
        user_id=test_user.id,
        entry_type="allergy",
        content="Pollen",
    )
    assert entry.id is not None
    assert entry.content == "Pollen"
    
    # 2. List entries by user
    entries = mem_repo.list_by_user(test_user.id)
    assert len(entries) == 1
    assert entries[0].content == "Pollen"
    
    # 3. Create summary
    conv_repo = ConversationRepository(db_session)
    conv = conv_repo.create(user_id=test_user.id)
    summary = mem_repo.create_summary(
        conversation_id=conv.id,
        summary="Summary test text",
        message_count_at_summary=5,
    )
    assert summary.id is not None
    assert summary.summary == "Summary test text"

    # 4. Get latest summary
    fetched_summary = mem_repo.get_summary_for_conversation(conv.id)
    assert fetched_summary.id == summary.id
