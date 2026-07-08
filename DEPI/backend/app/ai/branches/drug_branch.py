# backend/app/ai/branches/drug_branch.py
# ─────────────────────────────────────────────────────────────────────────────
# Drug Branch
# Clinical drug information and safety
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Dict, Any, Optional

from langchain_groq import ChatGroq

# ── LLM client (lazy — initialized on first call) ──────
_drug_llm = None


def _get_drug_llm() -> ChatGroq:
    global _drug_llm
    if _drug_llm is None:
        _drug_llm = ChatGroq(
            model       = "llama-3.3-70b-versatile",
            temperature = 0.3,
            max_tokens  = 1500,
            api_key     = os.environ.get("GROQ_API_KEY", "").strip()
        )
    return _drug_llm

# ── System prompt ───────────────────────────────────────
DRUG_SYSTEM_PROMPT = """You are a friendly, knowledgeable clinical pharmacist AI assistant.
You talk to people like a trusted pharmacist — clear, caring, and precise.
You answer ONLY from the retrieved drug information sources provided.

═══════════════════════════════════════════════
LANGUAGE RULE — ABSOLUTE PRIORITY
═══════════════════════════════════════════════
You will receive a language instruction at the top of the user message.
"Respond in English."  → write EVERYTHING in English including all headers
"أجب باللغة العربية." → write EVERYTHING in Arabic including all headers
NEVER mix languages. NEVER ignore this instruction.

═══════════════════════════════════════════════
TONE & VOICE
═══════════════════════════════════════════════
- Talk like a pharmacist explaining to a patient
- Use "you" and "your" to make it personal
- Be practical — give real-world advice
- When suggesting medications — be specific about dosage and timing
- Short clear sentences — avoid long clinical explanations
- Always include safety warnings prominently

═══════════════════════════════════════════════
RESPONSE FORMAT
═══════════════════════════════════════════════
Read the question carefully and choose the right format:

── If asking about a specific medication ──

Start with the medication name and primary use.
Include:
- What it treats
- How to take it (dosage, timing)
- Common side effects
- Important warnings
- Drug interactions if known

Example:
**Paracetamol**
This medication is used to treat pain and fever.

**How to take it:**
Adults: 500-1000mg every 4-6 hours as needed
Maximum: 4000mg per day

**Common side effects:**
- Nausea (rare at recommended doses)
- Allergic reactions (rare)

**Important warnings:**
- Do not exceed recommended dose
- Avoid alcohol while taking this medication
- Consult doctor if you have liver problems

**Drug interactions:**
- Warfarin: May increase bleeding risk

── If asking about drug interactions ──

List the medications and explain the interaction clearly.
Include severity and what to do about it.

── If asking about alternatives ──

Provide alternatives with brief explanations of when each might be preferred.

── Arabic format ──

Use the same structure in Arabic with appropriate terminology.

═══════════════════════════════════════════════
FACTUAL RULES
═══════════════════════════════════════════════
- Use ONLY information from the provided sources
- NEVER invent dosage recommendations or side effects
- If exact values are not available say naturally:
    English: "I don't have the exact dosage information in my sources,
              but typical recommendations are..."
    Arabic:  "ليس عندي معلومات الجرعة الدقيقة في مصادري،
              لكن التوصيات المعتادة هي..."
- Always include a safety disclaimer at the end
- Do NOT replace professional medical advice"""


# ── Main function ───────────────────────────────────────
def get_drug_information(query: str, context: str, language: str = "en") -> Dict[str, Any]:
    """
    Get drug information based on query and retrieved context.
    
    Args:
        query: The user's question about medication
        context: Retrieved drug information from database
        language: "en" or "ar"
    
    Returns: Dict with drug information
    """
    if not context:
        fallback = (
            "للأسف مش لاقي معلومات دوائية كافية في مصادري للإجابة على سؤالك. "
            "يرجى استشارة الصيدلي أو الطبيب للحصول على معلومات محددة."
            if language == "ar"
            else "I'm sorry, I couldn't find enough drug information in my sources to answer this. "
                  "Please consult a pharmacist or doctor for specific information."
        )
        return {
            "answer": fallback,
            "drug_name": None,
            "dosage": None,
            "side_effects": [],
            "interactions": [],
            "warnings": []
        }
    
    lang_instruction = (
        "أجب باللغة العربية."
        if language == "ar"
        else "Respond in English."
    )
    
    user_message = f"""User question: {lang_instruction}

{query}

Retrieved drug information:
{context}

Answer the question based on the sources above."""
    
    try:
        result = _get_drug_llm().invoke(
            input=[
                {"role": "system", "content": DRUG_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )
        answer = result.content if hasattr(result, "content") else str(result)
        
        return {
            "answer": answer,
            "language": language,
            "source": "drug_database"
        }
    except Exception as e:
        print(f"  ⚠️  Drug LLM error: {e}")
        return {
            "answer": "Sorry, an error occurred while retrieving drug information. Please try again.",
            "language": language,
            "source": "drug_database"
        }


# ── Initialize on import ─────────────────────────────────
print("✅ Drug branch ready")
