from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.memory_service import MemoryService
from app.ai.prompts.prompt_builder import get_prompt_builder


class PromptService:
    """Service for constructing AI prompts with injected context."""

    def __init__(self, db: Session):
        self.db = db
        self.memory_service = MemoryService(db)
        self.prompt_builder = get_prompt_builder()

    def get_chat_prompt(
        self,
        user_id: int,
        conversation_id: Optional[int],
        retrieved_context: Optional[str],
        current_question: str,
    ) -> List[Dict[str, str]]:
        # Fetch memory details
        memory_data = self.memory_service.inject_memory(user_id, conversation_id)
        
        # Load system template
        system_prompt = self.prompt_builder.load_template("system")
        
        # Define formatting instructions
        formatting_instructions = (
            "RULES:\n"
            "1. Answer ONLY from the context. Do NOT hallucinate.\n"
            "2. If the answer is not in the context, say: 'I cannot find the answer to this in my medical library.'\n"
            "3. Structure your answer clearly using bullet points where appropriate.\n"
            "4. End your response with a JSON block on its own line in this exact format:\n"
            "   SUSPECTED_CONDITIONS: [\"Condition1\", \"Condition2\"]\n"
            "5. CRITICAL RULE — NO EXCEPTIONS: any message containing pain, ache, hurt, burning, "
            "discomfort, swelling, or any physical symptom description MUST trigger the doctor "
            "referral JSON block when a doctor visit may be needed. Emotional language does not "
            "override this rule.\n"
            "6. This includes messages where the user expresses distress, uses words like "
            "\"disturbing\", \"terrible\", \"unbearable\", \"awful\", or \"severe\", or describes "
            "any pain regardless of how it is phrased.\n"
            "7. When the rule above applies, you MUST include the following JSON block somewhere in "
            "your response, on its own line, with no surrounding text on that line:\n\n"
            "[DOCTOR_REFERRAL]{{\"specialist\":\"<specialist type>\",\"urgency\":\"<routine|soon|urgent>\","
            "\"reason\":\"<one short phrase>\"}}[/DOCTOR_REFERRAL]\n\n"
            "Rules for the JSON block:\n"
            "- \"specialist\" must be a plain English doctor type suitable for a Google Places search.\n"
            "- \"urgency\" must be exactly one of: \"routine\", \"soon\", \"urgent\".\n"
            "- \"reason\" must be 5 words or fewer describing why."
        )

        return self.prompt_builder.build_chat_prompt(
            system_prompt=system_prompt,
            user_preferences=memory_data.get("user_preferences"),
            persistent_memory=memory_data.get("persistent_memory"),
            conversation_summary=memory_data.get("conversation_summary"),
            recent_messages=memory_data.get("recent_messages"),
            retrieved_context=retrieved_context,
            current_question=current_question,
            formatting_instructions=formatting_instructions
        )
