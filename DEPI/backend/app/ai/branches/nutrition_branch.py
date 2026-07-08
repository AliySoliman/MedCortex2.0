# backend/app/ai/branches/nutrition_branch.py
# ─────────────────────────────────────────────────────────────────────────────
# Nutrition Branch
# Clinical nutrition guidance and meal planning
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Dict, Any, Optional

from langchain_groq import ChatGroq

# ── LLM client (lazy — initialized on first call) ──────
_nutrition_llm = None


def _get_nutrition_llm() -> ChatGroq:
    global _nutrition_llm
    if _nutrition_llm is None:
        _nutrition_llm = ChatGroq(
            model       = "llama-3.3-70b-versatile",
            temperature = 0.5,
            max_tokens  = 1500,
            api_key     = os.environ.get("GROQ_API_KEY", "").strip()
        )
    return _nutrition_llm

# ── System prompt ───────────────────────────────────────
NUTRITION_SYSTEM_PROMPT = """You are a friendly, knowledgeable clinical nutritionist and dietitian.
You talk to people like a trusted nutrition coach — practical, warm, and specific.
You answer ONLY from the retrieved nutritional sources provided.

You know Egyptian and Arabic foods deeply — koshari, ful, molokhia, kofta, feteer,
Om Ali, and all regional dishes are as familiar to you as any international food.

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
- Talk like a nutrition coach explaining to a client — not a textbook
- Use "you" and "your" to make it personal and actionable
- Lead with the number or key fact the person is looking for
- Be practical — give real-world portion sizes and food swaps
- When suggesting foods or plans — be specific, not generic
- Short clear sentences — avoid long clinical explanations

═══════════════════════════════════════════════
RESPONSE FORMAT
═══════════════════════════════════════════════
Read the question carefully and choose the right format:

── If asking about calories / macros of a specific food ──

Start with the number directly. Then give the breakdown.
Add a practical note about portion or preparation if useful.

── If asking for food advice / diet guidance / condition-specific diet ──

Start with a warm direct answer.
Explain what to eat and what to limit — be specific with food names.
Include Egyptian or Arabic food options when relevant.
End with 2-3 practical tips.

── If asking for a meal plan ──

Build a practical day or week plan based on the sources.
Use real food names — including Egyptian and Arabic foods.

── Arabic format ──

Use the same structure in Arabic.

═══════════════════════════════════════════════
FACTUAL RULES
═══════════════════════════════════════════════
- Use ONLY values and facts from the provided sources
- NEVER invent calorie counts, macro values, or medical nutrition claims
- For meal plans — use foods mentioned or consistent with source content
- If exact values are not available say naturally
- Do NOT include any disclaimer — the safety layer handles this"""


# ── Main function ───────────────────────────────────────
def get_nutrition_information(query: str, context: str, language: str = "en") -> Dict[str, Any]:
    """
    Get nutrition information based on query and retrieved context.
    
    Args:
        query: The user's question about nutrition
        context: Retrieved nutrition information from database
        language: "en" or "ar"
    
    Returns: Dict with nutrition information
    """
    if not context:
        fallback = (
            "للأسف مش لاقي معلومات غذائية كافية في مصادري للإجابة على سؤالك. "
            "جرب تسأل عن طعام أو حالة تانية."
            if language == "ar"
            else "I'm sorry, I couldn't find enough nutritional information in my sources to answer this. "
                  "Try asking about a specific food or condition."
        )
        return {
            "answer": fallback,
            "language": language,
            "source": "nutrition_database"
        }
    
    lang_instruction = (
        "أجب باللغة العربية."
        if language == "ar"
        else "Respond in English."
    )
    
    user_message = f"""User question: {lang_instruction}

{query}

Retrieved nutrition information:
{context}

Answer the question based on the sources above."""
    
    try:
        result = _get_nutrition_llm().invoke(
            input=[
                {"role": "system", "content": NUTRITION_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )
        answer = result.content if hasattr(result, "content") else str(result)
        
        return {
            "answer": answer,
            "language": language,
            "source": "nutrition_database"
        }
    except Exception as e:
        print(f"  ⚠️  Nutrition LLM error: {e}")
        return {
            "answer": "Sorry, an error occurred while retrieving nutrition information. Please try again.",
            "language": language,
            "source": "nutrition_database"
        }


# ── Initialize on import ─────────────────────────────────
print("✅ Nutrition branch ready")
