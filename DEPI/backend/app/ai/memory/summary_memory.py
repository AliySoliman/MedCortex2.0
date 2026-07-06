import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from app.ai.providers.provider_factory import get_provider


class SummaryMemory(ABC):
    """Abstract base class for summary memory engines."""
    
    @abstractmethod
    def generate_summary(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """Generate conversation summary."""
        pass
    
    @abstractmethod
    def extract_key_info(
        self,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Extract key information from conversation."""
        pass


class GroqSummaryMemory(SummaryMemory):
    """Groq-powered implementation of SummaryMemory."""

    def __init__(self, provider_name: str = "groq", model_name: Optional[str] = None):
        self.provider_name = provider_name
        self.model_name = model_name or "llama-3.1-8b-instant"  # Use faster model for utility task

    def generate_summary(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        if not messages:
            return ""

        formatted_dialogue = ""
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            formatted_dialogue += f"{role}: {content}\n"

        prompt = [
            {
                "role": "system",
                "content": "You are a medical assistant summarizer. Summarize the clinical conversation below concisely. Focus on symptoms, suspected conditions, lifestyle advice, and next steps."
            },
            {
                "role": "user",
                "content": f"Please summarize this conversation:\n\n{formatted_dialogue}"
            }
        ]

        try:
            provider = get_provider(self.provider_name)
            summary = provider.generate(prompt, model=self.model_name)
            return summary.strip()
        except Exception as e:
            # Fallback
            return f"Summary extraction failed: {str(e)}"

    def extract_key_info(
        self,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        default_result = {
            "symptoms": [],
            "allergies": [],
            "conditions": [],
            "medications": [],
            "preferences": []
        }
        if not messages:
            return default_result

        formatted_dialogue = ""
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            formatted_dialogue += f"{role}: {content}\n"

        system_instruction = (
            "You are a medical facts extractor. Extract any user-mentioned symptoms, allergies, medical conditions, medications, or assistant/user preferences. "
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            "  \"symptoms\": [\"symptom1\", ...],\n"
            "  \"allergies\": [\"allergy1\", ...],\n"
            "  \"conditions\": [\"condition1\", ...],\n"
            "  \"medications\": [\"medication1\", ...],\n"
            "  \"preferences\": [\"preference1\", ...]\n"
            "}\n"
            "If none are found, leave the lists empty. Do not include any other markdown or conversational text."
        )

        prompt = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Extract facts from this clinical conversation:\n\n{formatted_dialogue}"}
        ]

        try:
            provider = get_provider(self.provider_name)
            response = provider.generate(prompt, model=self.model_name)
            
            # Clean up potential markdown formatting block ```json ... ```
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            parsed = json.loads(cleaned_response)
            # Ensure it has all keys
            for key in default_result:
                if key not in parsed or not isinstance(parsed[key], list):
                    parsed[key] = []
            return parsed
        except Exception:
            # Fallback on parse failure / LLM error
            return default_result


class SummaryMemoryService:
    """Service for summary memory operations."""
    
    def __init__(self, memory: Optional[SummaryMemory] = None):
        self.memory = memory or GroqSummaryMemory()
    
    def summarize(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        return self.memory.generate_summary(messages)

    def extract_info(
        self,
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        return self.memory.extract_key_info(messages)
