# backend/app/ai/retrieval/rag_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────
# MedCortex RAG Pipeline
# Connects modular retrievers and generators.
# ─────────────────────────────────────────────────────────────────────────────

import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.ai.retrieval.retrievers import ClinicalRetriever
from app.ai.retrieval.generators import ClinicalGenerator

# Helper functions originally in rag_pipeline.py for parsing referral blocks
# and symptoms. We keep the symptom extraction and normalisation logic intact.

SYMPTOM_TRIGGER_TERMS = (
    "pain", "ache", "aching", "hurt", "hurts", "burning", "discomfort",
    "swelling", "fever", "bleeding", "vomiting", "nausea", "dizziness",
    "fatigue", "weakness", "shortness of breath", "cough", "rash",
    "headache", "migraine", "back pain", "chest pain", "stomach pain",
    "cramp", "cramps", "tingling", "numbness", "infection", "injury",
    "sore", "soreness", "pressure", "palpitations",
)

DISTRESS_TRIGGER_TERMS = (
    "disturbing", "terrible", "unbearable", "awful", "severe", "intense",
    "extreme", "scary", "frightening", "worrying", "worried", "concerned",
)

REFERRAL_BLOCK_REGEX = re.compile(r"\[DOCTOR_REFERRAL\](.*?)\[/DOCTOR_REFERRAL\]", re.DOTALL)

SPECIALIST_RULES = [
    (("back pain", "lower back", "upper back", "neck pain", "spine", "joint pain", "knee", "shoulder"), "orthopedic surgeon"),
    (("chest pain", "palpitations", "heart", "blood pressure"), "cardiologist"),
    (("rash", "itching", "skin", "mole", "acne"), "dermatologist"),
    (("headache", "migraine", "numbness", "tingling", "seizure", "dizziness"), "neurologist"),
    (("ear", "nose", "throat", "sinus"), "ENT specialist"),
    (("stomach", "abdomen", "abdominal", "nausea", "vomiting", "diarrhea", "constipation", "reflux"), "gastroenterologist"),
    (("cough", "shortness of breath", "wheezing", "breathing"), "pulmonologist"),
    (("burning urination", "urine", "kidney"), "urologist"),
    (("anxiety", "depression", "panic", "mental"), "psychiatrist"),
]

IMPORTANT_MEDICAL_PHRASES = (
    "lower back", "upper back", "back pain", "chest pain", "shortness of breath",
    "stomach pain", "abdominal pain", "burning urination", "joint pain",
    "severe pain", "disturbing pain", "neck pain", "headache", "skin rash",
)

IMPORTANT_MEDICAL_WORDS = {
    "pain", "ache", "aching", "hurt", "hurts", "burning", "discomfort", "swelling",
    "fever", "bleeding", "vomiting", "nausea", "dizziness", "fatigue", "weakness",
    "cough", "rash", "headache", "migraine", "cramp", "cramps", "tingling",
    "numbness", "infection", "injury", "sore", "soreness", "pressure", "palpitations",
    "back", "lower", "upper", "neck", "spine", "joint", "knee", "shoulder", "hip",
    "chest", "heart", "stomach", "abdomen", "abdominal", "ear", "nose", "throat",
    "sinus", "breathing", "breath", "urination", "urine", "kidney", "skin",
    "itching", "mole", "acne", "disturbing", "terrible", "unbearable", "awful",
    "severe", "intense", "extreme",
}


def should_force_doctor_referral(user_message: str) -> bool:
    normalized = user_message.lower()
    return any(term in normalized for term in (*SYMPTOM_TRIGGER_TERMS, *DISTRESS_TRIGGER_TERMS))


def normalize_medical_message(user_message: str) -> str:
    normalized = user_message.lower()
    captured_phrases = [phrase for phrase in IMPORTANT_MEDICAL_PHRASES if phrase in normalized]
    word_matches = re.findall(r"[a-z']+", normalized)
    captured_words = [word for word in word_matches if word in IMPORTANT_MEDICAL_WORDS]

    deduped_terms: List[str] = []
    for term in [*captured_phrases, *captured_words]:
        if term not in deduped_terms:
            deduped_terms.append(term)

    if not deduped_terms:
        return user_message

    return f"{user_message}\n\nClinical focus terms: {', '.join(deduped_terms[:18])}"


def build_rag_input(user_message: str) -> str:
    if not should_force_doctor_referral(user_message):
        return user_message

    return (
        f"{user_message}\n\n"
        "[System note: This message contains symptom descriptions or distress language. "
        "CRITICAL RULE — NO EXCEPTIONS: any message containing pain, ache, hurt, burning, "
        "discomfort, swelling, or another physical symptom description MUST include exactly one "
        "DOCTOR_REFERRAL block if a medical professional visit may be needed.]"
    )


def extract_doctor_referral_block(answer_text: str) -> str | None:
    match = REFERRAL_BLOCK_REGEX.search(answer_text)
    return match.group(0) if match else None


def infer_referral_specialist(symptoms: List[str], suspected_conditions: List[str], user_message: str) -> str:
    haystack = " ".join([*symptoms, *suspected_conditions, user_message.lower()])
    for keywords, specialist in SPECIALIST_RULES:
        if any(keyword in haystack for keyword in keywords):
            return specialist
    return "general practitioner"


def infer_referral_urgency(symptoms: List[str], user_message: str) -> str:
    haystack = " ".join([*symptoms, user_message.lower()])

    urgent_terms = (
        "chest pain", "shortness of breath", "trouble breathing", "severe bleeding",
        "loss of consciousness", "fainting", "stroke", "seizure",
    )
    soon_terms = (
        "severe", "unbearable", "disturbing", "extreme", "back pain", "lower back",
        "numbness", "tingling", "vomiting", "fever", "injury",
    )

    if any(term in haystack for term in urgent_terms):
        return "urgent"
    if any(term in haystack for term in soon_terms):
        return "soon"
    return "routine"


def infer_referral_reason(symptoms: List[str], user_message: str) -> str:
    if symptoms:
        primary = symptoms[0].strip().lower()
        return " ".join(primary.split()[:5])

    words = re.findall(r"[a-zA-Z]+", user_message.lower())
    return " ".join(words[:5]) or "physical symptoms"


def build_fallback_referral_block(
    symptoms: List[str],
    suspected_conditions: List[str],
    user_message: str,
) -> str | None:
    if not (symptoms or should_force_doctor_referral(user_message)):
        return None

    payload = {
        "specialist": infer_referral_specialist(symptoms, suspected_conditions, user_message),
        "urgency": infer_referral_urgency(symptoms, user_message),
        "reason": infer_referral_reason(symptoms, user_message),
    }
    return f'[DOCTOR_REFERRAL]{json.dumps(payload)}[/DOCTOR_REFERRAL]'


def run_rag(
    user_message: str,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Modular RAG pipeline entry point.
    """
    normalized_message = normalize_medical_message(user_message)
    
    # In modular design, symptom extraction is done by Clinical Intelligence,
    # but we can fallback to extracting from normalized_message if needed.
    symptoms = [term for term in IMPORTANT_MEDICAL_WORDS if term in normalized_message]
    
    retriever = ClinicalRetriever()
    generator = ClinicalGenerator()
    
    # 1. Retrieve
    source_docs = retriever.retrieve(normalized_message)
    retrieved_context = retriever.format_docs(source_docs)
    
    # 2. Generate
    rag_input = build_rag_input(normalized_message)
    answer_raw = generator.generate(query=rag_input, context_text=retrieved_context)
    
    # 3. Parse Output
    suspected = []
    match = re.search(r'SUSPECTED_CONDITIONS:\s*(\[.*?\])', answer_raw)
    if match:
        try:
            suspected = json.loads(match.group(1))
        except Exception:
            pass

    if not extract_doctor_referral_block(answer_raw):
        fallback_referral = build_fallback_referral_block(symptoms, suspected, normalized_message)
        if fallback_referral:
            answer_raw = f"{answer_raw.rstrip()}\n{fallback_referral}"

    answer_clean = re.sub(r'SUSPECTED_CONDITIONS:.*', '', answer_raw).strip()

    sources = []
    seen = set()
    for doc in source_docs:
        book = doc.metadata.get("book_title", "Unknown")
        sec  = doc.metadata.get("docling_headings", "")
        key  = f"{book}|{sec}"
        if key not in seen:
            seen.add(key)
            sources.append({"book": book, "section": sec})

    return {
        "answer": answer_clean,
        "suspected_conditions": suspected,
        "symptoms": symptoms,
        "sources": sources,
    }
