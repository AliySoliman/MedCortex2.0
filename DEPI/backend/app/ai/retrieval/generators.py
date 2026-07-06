# backend/app/ai/retrieval/generators.py
# ─────────────────────────────────────────────────────────────────────────────
# Clinical Generator
# Handles generation of clinical answers using LLMs based on retrieved context.
# ─────────────────────────────────────────────────────────────────────────────

from typing import List, Dict, Any, Optional
import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.ai.providers.provider_factory import get_default_llm

LLM_MODEL = "llama-3.3-70b-versatile"

def _get_llm():
    return get_default_llm(
        model=LLM_MODEL,
        temperature=0.0,
        max_tokens=1024,
    )


class ClinicalGenerator:
    """
    Generates clinical answers using RAG context.
    """
    
    def __init__(self):
        self.llm = _get_llm()
        self.system_prompt = (
            "You are MedCortex, an elite Clinical AI Assistant. "
            "Your knowledge is strictly limited to the provided medical textbook excerpts.\n\n"
            "RULES:\n"
            "1. Answer ONLY from the context below. Do NOT hallucinate.\n"
            "2. If the answer is not in the context, say: "
            "'I cannot find the answer to this in my medical library.'\n"
            "3. Structure your answer with a short summary followed by 2-5 concise bullets.\n"
            "4. Use simple markdown headings only if they improve readability.\n"
            "5. End your response with a JSON block on its own line in this exact format:\n"
            "   SUSPECTED_CONDITIONS: [\"Condition1\", \"Condition2\"]\n"
            "6. CRITICAL RULE — NO EXCEPTIONS: any message containing physical symptom descriptions "
            "MUST trigger the doctor referral JSON block when a doctor visit may be needed.\n"
            "7. When the rule above applies, you MUST include the following JSON block somewhere in "
            "your response, on its own line and separated from the main answer:\n\n"
            "[DOCTOR_REFERRAL]{{\"specialist\":\"<specialist type>\",\"urgency\":\"<routine|soon|urgent>\","
            "\"reason\":\"<one short phrase>\"}}[/DOCTOR_REFERRAL]\n\n"
            "MEDICAL CONTEXT:\n{context}"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()
        
    def generate(self, query: str, context_text: str) -> str:
        """
        Generate answer based on query and retrieved context text.
        """
        raw = self.chain.invoke({"context": context_text, "input": query})
        return _normalize_answer_text(raw)


def _normalize_answer_text(answer: str) -> str:
    """Normalize model output into a cleaner, more readable markdown-like answer."""
    cleaned = answer.replace("\r\n", "\n").strip()

    # Remove duplicated blank lines and standardize bullets.
    lines: List[str] = []
    for raw_line in cleaned.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if stripped.startswith("* "):
            stripped = "- " + stripped[2:].lstrip()
        lines.append(stripped)

    cleaned = "\n".join(lines).strip()

    # Collapse accidental markdown fences while keeping the text readable.
    cleaned = re.sub(r"```(?:json|markdown)?\s*", "", cleaned)
    cleaned = cleaned.replace("```", "")

    # Ensure the referral block is separated from prose when present.
    cleaned = cleaned.replace("[DOCTOR_REFERRAL]", "\n[DOCTOR_REFERRAL]")
    cleaned = cleaned.replace("[/DOCTOR_REFERRAL]", "[/DOCTOR_REFERRAL]\n")

    return cleaned.strip()
