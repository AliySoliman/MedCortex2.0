# backend/app/ai/router/intent_router.py
# ─────────────────────────────────────────────────────────────────────────────
# Intent Router
# Routes user requests to appropriate workflows based on intent
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
from enum import Enum


class Intent(Enum):
    """User intent types."""
    CHAT = "chat"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION_ANALYSIS = "prescription_analysis"
    LAB_INTERPRETATION = "lab_interpretation"
    VISION_ANALYSIS = "vision_analysis"
    REPORT_GENERATION = "report_generation"
    DRUG_CHECK = "drug_check"


class IntentRouter:
    """Routes user requests based on detected intent."""
    
    def __init__(self):
        self._intent_patterns: Dict[Intent, list[str]] = {
            Intent.CHAT: ["hello", "hi", "how are you", "general"],
            Intent.DIAGNOSIS: ["diagnose", "symptoms", "what do i have"],
            Intent.PRESCRIPTION_ANALYSIS: ["prescription", "medication", "drug"],
            Intent.LAB_INTERPRETATION: ["lab", "test result", "blood work"],
            Intent.VISION_ANALYSIS: ["image", "photo", "scan", "x-ray"],
            Intent.REPORT_GENERATION: ["report", "summary", "document"],
            Intent.DRUG_CHECK: ["interaction", "side effect", "contraindication"],
        }
    
    def detect_intent(self, message: str) -> Intent:
        """
        Detect user intent from message.
        
        Placeholder for future ML-based intent classification.
        """
        message_lower = message.lower()
        
        for intent, patterns in self._intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return intent
        
        return Intent.CHAT  # Default to chat
    
    def route(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route message to appropriate workflow.
        
        Placeholder for future implementation.
        """
        intent = self.detect_intent(message)
        return {
            "intent": intent.value,
            "message": message,
            "context": context or {},
        }
