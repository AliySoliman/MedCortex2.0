# backend/app/ai/memory/memory_manager.py
# ─────────────────────────────────────────────────────────────────────────────
# Memory Manager
# Manages conversation memory and context for AI interactions
# ─────────────────────────────────────────────────────────────────────────────

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryMessage:
    """A single message in conversation memory."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """Manages conversation memory with configurable window size."""
    
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.messages: List[MemoryMessage] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to memory."""
        message = MemoryMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        
        # Trim to max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get messages in format suitable for LLM."""
        messages = self.messages[-limit:] if limit else self.messages
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    def clear(self):
        """Clear all messages from memory."""
        self.messages.clear()
    
    def get_context_summary(self) -> str:
        """Get a summary of the conversation context."""
        if not self.messages:
            return "No conversation history."
        
        return f"Conversation has {len(self.messages)} messages, " \
               f"last message from {self.messages[-1].role}."

    def inject(
        self,
        user_preferences: Optional[Dict[str, Any]] = None,
        persistent_memory: Optional[List[str]] = None,
        conversation_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Inject various memory context pieces into a structured dictionary.
        This provides all required sections for the PromptBuilder in a structured format.
        """
        # Format user preferences
        prefs_str = ""
        if user_preferences:
            prefs_list = []
            if "language" in user_preferences:
                prefs_list.append(f"Preferred Language: {user_preferences['language']}")
            if "response_style" in user_preferences:
                prefs_list.append(f"Preferred Response Style: {user_preferences['response_style']}")
            prefs_str = "\n".join(prefs_list)

        # Format persistent memory
        mem_str = ""
        if persistent_memory:
            mem_str = "\n".join([f"- {item}" for item in persistent_memory])

        return {
            "user_preferences": prefs_str,
            "persistent_memory": mem_str,
            "conversation_summary": conversation_summary or "",
            "recent_messages": self.get_messages(),
        }
