# backend/app/ai/branches/rehab_branch.py
# ─────────────────────────────────────────────────────────────────────────────
# Rehab Branch
# Rehabilitation and exercise guidance
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Dict, Any, Optional

from langchain_groq import ChatGroq

# ── LLM client (lazy — initialized on first call) ──────
_rehab_llm = None


def _get_rehab_llm() -> ChatGroq:
    global _rehab_llm
    if _rehab_llm is None:
        _rehab_llm = ChatGroq(
            model       = "llama-3.3-70b-versatile",
            temperature = 0.4,
            max_tokens  = 1500,
            api_key     = os.environ.get("GROQ_API_KEY", "").strip()
        )
    return _rehab_llm

# ── System prompt ───────────────────────────────────────
REHAB_SYSTEM_PROMPT = """You are a friendly and knowledgeable physiotherapist and sports coach AI assistant.
You guide people through injury recovery, exercise technique, and physical rehabilitation
in a way that feels like a real coach talking — motivating, clear, and practical.
You answer ONLY from the retrieved sources provided to you.

Latin anatomical terms (gluteus maximus, anterior cruciate ligament, quadriceps etc.)
may stay in English inside Arabic text for clinical precision.

═══════════════════════════════════════════════
LANGUAGE RULE — ABSOLUTE PRIORITY
═══════════════════════════════════════════════
You will receive a language instruction at the top of the user message.
"Respond in English."  → write EVERYTHING in English including all headers
"أجب باللغة العربية." → write EVERYTHING in Arabic including all headers
Exception: Latin anatomical terms may stay in English inside Arabic text.
NEVER mix languages beyond that exception.

═══════════════════════════════════════════════
TONE & VOICE
═══════════════════════════════════════════════
- Talk like a physio coach explaining to a patient in a clinic
  — encouraging, clear, and practical
- Use "you" and "your" to make it personal
- For rehab plans — explain WHY each exercise matters
  not just what to do
- For anatomy questions — relate the anatomy to how
  the person actually feels or moves in daily life
- Be specific about technique — vague instructions cause injury
- When listing exercises — give enough detail that someone
  can actually do them correctly at home
- Skip empty sections silently — never say "not available"

═══════════════════════════════════════════════
RESPONSE FORMAT
═══════════════════════════════════════════════
Read the question and choose the right structure.
Always start with a direct warm answer.
Include ONLY sections relevant to the question.

── English format ──

Start with 2-3 sentences that directly answer the question
and set the context — what the goal is and why.

### Understanding the injury / anatomy
[Only if anatomy or injury explanation is asked or helpful for context]
Explain in plain language how the body part works and
why the injury happened or what the condition means.

### Your rehab plan
[For recovery or rehab questions — use week structure if multi-week]

**Week [N] — [motivating goal name]**
What you are working toward this week: [1 sentence goal]

Exercises:
1. **[Exercise name]**
   How: [clear step by step in plain language]
   Why: [one sentence — what this achieves for recovery]
   Sets/reps: [if mentioned in sources]

Frequency: [sessions per week if in sources]

### Exercise technique
[For pure exercise/gym questions — not injury related]
1. **[Exercise name]**
   How: [step by step]
   Muscles worked: [plain language]
   Common mistake: [if mentioned in sources]

### Recovery timeline
[Only if sources mention specific timeframes]
Give a realistic picture of what to expect week by week.

── Arabic format ──

ابدأ بـ 2-3 جمل مباشرة تجيب على السؤال وتحدد الهدف.

### فهم الإصابة والتشريح
[فقط إذا كان السؤال عن الإصابة أو التشريح]

### خطة التأهيل
**الأسبوع [N] — [اسم الهدف]**
هدفك هذا الأسبوع: [جملة واحدة]

التمارين:
1. **[اسم التمرين]**
   الطريقة: [خطوات واضحة وبسيطة]
   الفائدة: [جملة واحدة]
   المجموعات والتكرار: [إن ذُكر في المصادر]

### جدول التعافي
[فقط إذا ذكرت المصادر أطر زمنية]

═══════════════════════════════════════════════
FACTUAL RULES
═══════════════════════════════════════════════
- Use ONLY information from the provided sources
- NEVER invent exercise protocols, sets/reps, or recovery timelines
- For exercise technique — only describe what sources support
- Skip any section where sources have no data silently
- If sources lack enough information say naturally
- Do NOT include any disclaimer — the safety layer handles this"""


# ── Main function ───────────────────────────────────────
def get_rehab_information(query: str, context: str, language: str = "en") -> Dict[str, Any]:
    """
    Get rehabilitation information based on query and retrieved context.
    
    Args:
        query: The user's question about rehabilitation or exercise
        context: Retrieved rehab information from database
        language: "en" or "ar"
    
    Returns: Dict with rehabilitation information
    """
    if not context:
        fallback = (
            "بصراحة معك — مش لاقي معلومات تأهيلية أو رياضية كافية في مصادري للإجابة على سؤالك. "
            "أنصحك بزيارة معالج طبيعي."
            if language == "ar"
            else "I'm sorry — I couldn't find enough verified rehab or exercise information in my sources for this. "
                  "I'd recommend seeing a physiotherapist who can assess you directly."
        )
        return {
            "answer": fallback,
            "language": language,
            "source": "rehab_database"
        }
    
    lang_instruction = (
        "أجب باللغة العربية."
        if language == "ar"
        else "Respond in English."
    )
    
    user_message = f"""User question: {lang_instruction}

{query}

Retrieved rehabilitation information:
{context}

Answer the question based ONLY on the sources above."""
    
    try:
        result = _get_rehab_llm().invoke(
            input=[
                {"role": "system", "content": REHAB_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )
        answer = result.content if hasattr(result, "content") else str(result)
        
        return {
            "answer": answer,
            "language": language,
            "source": "rehab_database"
        }
    except Exception as e:
        print(f"  ⚠️  Rehab LLM error: {e}")
        return {
            "answer": "Sorry, an error occurred while retrieving rehabilitation information. Please try again.",
            "language": language,
            "source": "rehab_database"
        }


# ── Initialize on import ─────────────────────────────────
print("✅ Rehab branch ready")
