# backend/app/ai/prompts/prompt_builder.py
# ─────────────────────────────────────────────────────────────────────────────
# Prompt Builder
# Centralized prompt construction and template management
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional, List
from pathlib import Path


class PromptBuilder:
    """
    Centralized prompt construction class.
    
    This is the ONLY way prompts should be constructed in the system.
    Loads prompt templates from .md files and injects context.
    """
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize PromptBuilder with prompts directory."""
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent
        self.prompts_dir = prompts_dir
    
    def load_template(self, template_name: str) -> str:
        """
        Load prompt template from .md file.
        
        Args:
            template_name: Name of the template file (without .md extension)
        
        Returns:
            Template content as string
        """
        template_path = self.prompts_dir / f"{template_name}.md"
        if not template_path.exists():
            # Try load fallback from system.md or chat.md
            template_path = self.prompts_dir / "system.md"
            if not template_path.exists():
                return "You are MedCortex, an elite Clinical AI Assistant."
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def build_prompt(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        conversation: Optional[List[Dict[str, str]]] = None,
        memory: Optional[str] = None,
        retrieved_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Build final prompt by injecting context into template.
        """
        template = self.load_template(template_name)
        
        # Build injection context
        injection_context = {
            "context": retrieved_context or "",
            "conversation": self._format_conversation(conversation or []),
            "memory": memory or "",
            "system_prompt": system_prompt or "",
            "citations": self._format_citations(citations or []),
        }
        
        # Add any additional context
        if context:
            injection_context.update(context)
        
        # Inject variables into template
        final_prompt = template
        for key, value in injection_context.items():
            placeholder = f"{{{key}}}"
            final_prompt = final_prompt.replace(placeholder, str(value))
        
        return final_prompt
    
    def build_chat_prompt(
        self,
        system_prompt: str,
        user_preferences: Optional[str] = None,
        persistent_memory: Optional[str] = None,
        conversation_summary: Optional[str] = None,
        recent_messages: Optional[List[Dict[str, str]]] = None,
        retrieved_context: Optional[str] = None,
        current_question: str = "",
        formatting_instructions: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Builds the messages array in the exact required order:
        1. System Prompt
        2. User Preferences
        3. Persistent Memory
        4. Conversation Summary
        5. Recent Messages (appended sequentially)
        6. Retrieved Context (injected with current question or preceding it)
        7. Current Question
        8. Formatting Instructions
        """
        system_parts = []
        
        # 1. System Prompt
        system_parts.append(system_prompt)
        
        # 2. User Preferences
        if user_preferences:
            system_parts.append(f"## User Preferences\n{user_preferences}")
            
        # 3. Persistent Memory
        if persistent_memory:
            system_parts.append(f"## Persistent User Memory (Extracted Medical Facts)\n{persistent_memory}")
            
        # 4. Conversation Summary
        if conversation_summary:
            system_parts.append(f"## Conversation Summary\n{conversation_summary}")

        # 6. Retrieved Context
        if retrieved_context:
            system_parts.append(f"## Retrieved Medical Context\n{retrieved_context}")

        # 8. Formatting Instructions
        if formatting_instructions:
            system_parts.append(f"## Formatting Instructions\n{formatting_instructions}")

        compiled_system = "\n\n".join(system_parts)
        
        messages = [{"role": "system", "content": compiled_system}]
        
        # 5. Recent Messages
        if recent_messages:
            for msg in recent_messages:
                # Add only user and assistant messages to history
                if msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
                    
        # 7. Current Question
        messages.append({"role": "user", "content": current_question})
        
        return messages
    
    def _format_conversation(self, conversation: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt injection."""
        if not conversation:
            return ""
        
        formatted = []
        for msg in conversation:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)
    
    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Format citations for prompt injection."""
        if not citations:
            return ""
        
        formatted = []
        for i, citation in enumerate(citations, 1):
            source = citation.get("source", "Unknown")
            text = citation.get("text", "")
            formatted.append(f"[{i}] {source}: {text}")
        
        return "\n".join(formatted)


# Global PromptBuilder instance
_prompt_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """Get the global PromptBuilder instance."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
