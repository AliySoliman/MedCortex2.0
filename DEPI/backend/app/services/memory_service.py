from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.repositories.memory_repository import MemoryRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.ai.memory.summary_memory import SummaryMemoryService
from app.ai.memory.user_memory import DBUserMemory


class MemoryService:
    """Service orchestrating various memory engines, summarization, and injection."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.memory_repo = MemoryRepository(db)
        self.message_repo = MessageRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.user_memory = DBUserMemory(db)
        self.summary_service = SummaryMemoryService()

    def inject_memory(self, user_id: int, conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Gathers user preferences, persistent medical facts, conversation summary,
        and recent messages to return a structured context for PromptBuilder.
        """
        # 1. Fetch user preferences and facts
        user_info = self.user_memory.get_user_info(str(user_id))
        user_prefs_str = ""
        persistent_mem_str = ""
        
        if user_info:
            # Format profile preferences
            pref_parts = []
            if user_info.get("age"):
                pref_parts.append(f"Age: {user_info['age']}")
            if user_info.get("gender"):
                pref_parts.append(f"Gender: {user_info['gender']}")
            if user_info.get("activity_level"):
                pref_parts.append(f"Activity Level: {user_info['activity_level']}")
            
            # Add database preferences
            pref_record = self.user_memory.get_user_info(str(user_id)) # We can fetch directly if needed
            
            user_prefs_str = ", ".join(pref_parts)

            # Format medical history facts
            facts_list = []
            if user_info.get("conditions"):
                facts_list.append(f"Conditions: {user_info['conditions']}")
            if user_info.get("allergies"):
                facts_list.append(f"Allergies: {user_info['allergies']}")
                
            db_facts = user_info.get("facts", {})
            for ftype, contents in db_facts.items():
                facts_list.append(f"{ftype.capitalize()}: {', '.join(contents)}")
                
            persistent_mem_str = "\n".join([f"- {fact}" for fact in facts_list])

        # 2. Fetch conversation summary (if conversation exists)
        summary_str = ""
        recent_messages = []
        
        if conversation_id:
            summary_record = self.memory_repo.get_summary_for_conversation(conversation_id)
            if summary_record:
                summary_str = summary_record.summary
            
            # 3. Fetch recent messages
            db_messages = self.message_repo.get_recent(conversation_id, limit=self.settings.MEMORY_CONVERSATION_LIMIT)
            recent_messages = [{"role": msg.role, "content": msg.content} for msg in db_messages]

        return {
            "user_preferences": user_prefs_str,
            "persistent_memory": persistent_mem_str,
            "conversation_summary": summary_str,
            "recent_messages": recent_messages,
        }

    def auto_summarize(self, conversation_id: int) -> Optional[str]:
        """
        Check if message count exceeds threshold, and automatically generate summary of conversation.
        """
        if not self.settings.MEMORY_ENABLED:
            return None

        # Fetch messages count
        messages = self.message_repo.list_by_conversation(conversation_id, limit=200)
        total_count = len(messages)
        
        if total_count == 0:
            return None

        # Get latest summary details
        latest_summary = self.memory_repo.get_summary_for_conversation(conversation_id)
        last_count = latest_summary.message_count_at_summary if latest_summary else 0
        
        # Trigger summary if new messages exceed threshold
        new_msgs_count = total_count - last_count
        if new_msgs_count >= self.settings.MEMORY_CONVERSATION_LIMIT:
            # Format message logs for summarizer
            msg_list = [{"role": m.role, "content": m.content} for m in messages]
            new_summary_text = self.summary_service.summarize(msg_list)
            
            if new_summary_text:
                self.memory_repo.create_summary(
                    conversation_id=conversation_id,
                    summary=new_summary_text,
                    message_count_at_summary=total_count
                )
                return new_summary_text
        return None

    def extract_and_store_facts(self, user_id: int, conversation_id: int):
        """
        Extract medical facts and store them in memory entry / user profile
        """
        messages = self.message_repo.list_by_conversation(conversation_id, limit=50)
        msg_list = [{"role": m.role, "content": m.content} for m in messages]
        
        extracted_info = self.summary_service.extract_info(msg_list)
        if extracted_info:
            extracted_info["source_conversation_id"] = conversation_id
            self.user_memory.store_user_info(str(user_id), extracted_info)
