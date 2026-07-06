# backend/app/api/chat.py
# ─────────────────────────────────────────────────────────────────────────────
# MedCortex Chat Route
# POST /chat  →  RAG + clinical reasoning + safety pipeline
# ─────────────────────────────────────────────────────────────────────────────

import logging
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    LifestyleRecommendations,
    Doctor,
    Source,
)

from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.services.memory_service import MemoryService
from app.ai.retrieval.rag_pipeline import run_rag
from app.ai.clinical.lab_interpreter import REFERENCE_RANGES, resolve_reference_range
from app.ai.clinical.lifestyle import get_lifestyle_recommendations
from app.ai.clinical.doctor_finder import find_doctors
from app.ai.safety.response_validator import ResponseValidator
from app.ai.branches.drug_branch import get_drug_information
from app.ai.branches.nutrition_branch import get_nutrition_information
from app.ai.branches.rehab_branch import get_rehab_information

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        email = decode_access_token(token)
        return db.query(User).filter(User.email == email).first()
    except Exception:
        return None


def _normalize_unified_context(unified_context: Optional[object]) -> Optional[dict]:
    if unified_context is None:
        return None
    if hasattr(unified_context, "model_dump"):
        return unified_context.model_dump()
    if isinstance(unified_context, dict):
        return unified_context
    return None


def _build_sources(source_items: list[dict[str, str]]) -> list[Source]:
    return [Source(book=item.get("book", ""), section=item.get("section", "")) for item in source_items]


def _build_recommendations(payload: dict[str, object]) -> LifestyleRecommendations:
    foods_to_eat: list[str] = []
    foods_to_avoid: list[str] = []
    drinks_to_have: list[str] = []
    drinks_to_avoid: list[str] = []
    exercises_recommended: list[str] = []
    exercises_to_avoid: list[str] = []

    for item in payload.get("foods_to_eat", []) or []:
        if isinstance(item, str):
            foods_to_eat.append(item)
    for item in payload.get("foods_to_avoid", []) or []:
        if isinstance(item, str):
            foods_to_avoid.append(item)
    for item in payload.get("drinks_to_have", []) or []:
        if isinstance(item, str):
            drinks_to_have.append(item)
    for item in payload.get("drinks_to_avoid", []) or []:
        if isinstance(item, str):
            drinks_to_avoid.append(item)
    for item in payload.get("exercises_recommended", []) or []:
        if isinstance(item, str):
            exercises_recommended.append(item)
    for item in payload.get("exercises_to_avoid", []) or []:
        if isinstance(item, str):
            exercises_to_avoid.append(item)

    return LifestyleRecommendations(
        foods_to_eat=foods_to_eat,
        foods_to_avoid=foods_to_avoid,
        drinks_to_have=drinks_to_have,
        drinks_to_avoid=drinks_to_avoid,
        exercises_recommended=exercises_recommended,
        exercises_to_avoid=exercises_to_avoid,
        rest_recommendation=str(payload.get("rest_recommendation", "") or ""),
    )


def _coerce_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("name") or item.get("text") or item.get("description")
                if text:
                    result.append(str(text).strip())
        return result
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
        return result
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _format_medication(item: object) -> str:
    if isinstance(item, dict):
        name = str(item.get("name") or "Unknown medication")
        details = [
            str(item.get("dosage") or "").strip(),
            str(item.get("frequency") or "").strip(),
            str(item.get("route") or "").strip(),
        ]
        details = [part for part in details if part]
        return f"{name} ({', '.join(details)})" if details else name
    return str(item).strip()


def _format_lab_value(item: object) -> str:
    if isinstance(item, dict):
        name = str(item.get("name") or item.get("test_name") or "Unknown test")
        raw_value = item.get("value")
        value = "" if raw_value is None else str(raw_value).strip()
        unit = str(item.get("unit") or "").strip()
        flag = str(item.get("flag") or "").strip()
        bits = [b for b in [value, unit, f"[{flag}]" if flag else ""] if b]
        return f"{name}: {' '.join(bits)}".strip()
    return str(item).strip()


def _extract_numeric_value(raw_value: object) -> Optional[float]:
    if isinstance(raw_value, (int, float)):
        return float(raw_value)
    if isinstance(raw_value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", raw_value.replace(",", ""))
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def _normalize_text_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower().strip())


def _interpret_lab_result(lab_item: dict) -> dict[str, str]:
    test_name = str(lab_item.get("name") or lab_item.get("test_name") or "Unknown test")
    raw_value = lab_item.get("value")
    numeric_value = _extract_numeric_value(raw_value)
    value_text = "" if raw_value is None else str(raw_value).strip()
    unit = str(lab_item.get("unit") or "").strip()
    ref_text = str(lab_item.get("reference_range") or "").strip()
    flag = str(lab_item.get("flag") or "").strip().lower()
    canonical_name, reference = resolve_reference_range(test_name, REFERENCE_RANGES)

    if flag in {"h", "high"}:
        status = "High"
    elif flag in {"l", "low"}:
        status = "Low"
    elif flag in {"a", "abnormal"}:
        status = "Abnormal"
    elif reference and numeric_value is not None:
        if numeric_value < reference["min"]:
            status = "Low"
        elif numeric_value > reference["max"]:
            status = "High"
        else:
            status = "Normal"
    else:
        status = "Not specified"

    if reference:
        normal_range = ref_text or _reference_range_text(reference)
    else:
        normal_range = ref_text or "Not specified"

    interpretation = _derive_interpretation(lab_item)
    if canonical_name and reference and numeric_value is not None:
        if status == "High":
            interpretation = (
                f"Above the normal range for {canonical_name.replace('_', ' ')}. "
                f"This may indicate { _high_level_hint(canonical_name) }."
            )
        elif status == "Low":
            interpretation = (
                f"Below the normal range for {canonical_name.replace('_', ' ')}. "
                f"This may indicate { _low_level_hint(canonical_name) }."
            )
        elif status == "Normal":
            interpretation = (
                f"Within the normal range for {canonical_name.replace('_', ' ')}."
            )

    return {
        "test_name": test_name,
        "value": value_text or "Not specified",
        "unit": unit,
        "normal_range": normal_range,
        "status": status,
        "interpretation": interpretation,
        "is_abnormal": "yes" if status in {"High", "Low", "Abnormal"} else "no",
    }


def _reference_range_text(reference: dict[str, object]) -> str:
    minimum = reference.get("min")
    maximum = reference.get("max")
    unit = str(reference.get("unit") or "").strip()
    if minimum is None and maximum is None:
        return unit or "Not specified"
    range_text = f"{minimum}–{maximum}" if minimum is not None and maximum is not None else str(minimum or maximum)
    return f"{range_text} {unit}".strip()


def _high_level_hint(test_name: str) -> str:
    key = _normalize_text_key(test_name)
    if "glucose" in key:
        return "hyperglycemia"
    if "bun" in key or "creatinine" in key or "ratio" in key:
        return "kidney stress, dehydration, or reduced renal clearance"
    if "sodium" in key:
        return "dehydration or other electrolyte imbalance"
    if "potassium" in key:
        return "an electrolyte disturbance that warrants clinical correlation"
    if "cholesterol" in key or "triglyceride" in key or "hdl" in key or "ldl" in key or "vldl" in key:
        return "cardiometabolic risk"
    if "albumin" in key:
        return "poor nutritional status, inflammation, or protein loss"
    return "clinical correlation"


def _low_level_hint(test_name: str) -> str:
    key = _normalize_text_key(test_name)
    if "glucose" in key:
        return "hypoglycemia"
    if "sodium" in key:
        return "hyponatremia"
    if "potassium" in key:
        return "hypokalemia"
    if "albumin" in key:
        return "low protein status, liver disease, or kidney loss"
    if "hdl" in key:
        return "reduced cardioprotective cholesterol"
    return "clinical correlation"


def _derive_interpretation(lab_item: object) -> str:
    if not isinstance(lab_item, dict):
        return "Not specified"
    flag = str(lab_item.get("flag") or "").strip().lower()
    value = str(lab_item.get("value") or "").strip()
    ref = str(lab_item.get("reference_range") or "").strip()
    if flag in {"h", "high"}:
        return "High"
    if flag in {"l", "low"}:
        return "Low"
    if flag in {"a", "abnormal"}:
        return "Abnormal"
    if ref and value:
        return "Within reference range" if not flag else flag.title()
    return "Normal"


def _build_document_response(unified_context: dict, user_message: str) -> tuple[str, list[str], list[str], list[Source]]:
    filename = str(unified_context.get("filename") or "Uploaded document")
    doc_info = unified_context.get("document_information") or {}
    patient_info = unified_context.get("patient_information") or {}
    provider_info = unified_context.get("provider_information") or {}
    processing_meta = unified_context.get("processing_metadata") or {}

    classification = str(unified_context.get("classification") or unified_context.get("document_type") or "Unknown").strip()
    modality = str(unified_context.get("modality") or "Unknown").strip()
    overall_confidence = unified_context.get("overall_confidence")

    clinical_findings = _coerce_string_list(unified_context.get("clinical_findings"))
    recommendations = _coerce_string_list(unified_context.get("recommendations"))
    warnings = _coerce_string_list(unified_context.get("warnings"))
    metadata_warnings = _coerce_string_list(processing_meta.get("warnings"))
    medications_raw = unified_context.get("medications") or []
    diagnoses_raw = unified_context.get("diagnoses") or []
    labs_raw = unified_context.get("lab_values") or []
    raw_analysis = str(unified_context.get("vision_output") or unified_context.get("ocr_output") or "").strip()

    medications = [_format_medication(item) for item in medications_raw if item]
    diagnoses = _coerce_string_list(diagnoses_raw)
    lab_values = [_format_lab_value(item) for item in labs_raw if item]
    detailed_labs = [_interpret_lab_result(item) for item in labs_raw if isinstance(item, dict)]
    abnormal_labs = [item for item in detailed_labs if item["is_abnormal"] == "yes"]
    normal_labs = [item for item in detailed_labs if item["status"] == "Normal"]
    unreadable_labs = [item for item in detailed_labs if item["status"] == "Not specified"]

    lines: list[str] = []
    doc_title = doc_info.get("title") or filename
    lines.append(f"# Clinical Summary: {doc_title}")
    lines.append("")
    
    # Lead with full vision output (Doctor's Review) when present
    if raw_analysis:
        lines.append("## Doctor's Review")
        lines.append(raw_analysis)
        lines.append("")

    lines.append("## Document Overview")
    lines.extend(
        [
            f"- **File:** {filename}",
            f"- **Classification:** {classification}",
            f"- **Modality:** {modality}",
        ]
    )
    if provider_info.get("name") or provider_info.get("specialty") or provider_info.get("organization"):
        provider_bits = [provider_info.get("name"), provider_info.get("specialty"), provider_info.get("organization")]
        provider_bits = [str(bit).strip() for bit in provider_bits if str(bit).strip()]
        lines.append(f"- **Provider / Source:** {', '.join(provider_bits)}")
    if overall_confidence is not None:
        try:
            lines.append(f"- **Confidence:** {float(overall_confidence):.0%}")
        except Exception:
            pass
    lines.append("")

    lines.append("## Patient Information")
    patient_lines = [
        f"- **Patient:** {patient_info.get('name') or 'Not specified'}",
        f"- **Age:** {patient_info.get('age') or 'Not specified'}",
        f"- **Sex:** {patient_info.get('gender') or 'Not specified'}",
        f"- **Attending Physician:** {provider_info.get('name') or 'Not specified'}",
        f"- **Report Type:** {classification}",
    ]
    if doc_info.get("date"):
        patient_lines.append(f"- **Date of Test:** {doc_info.get('date')}")
    lines.extend(patient_lines)
    lines.append("")

    combined_warnings = []
    for warning in [*warnings, *metadata_warnings]:
        if warning not in combined_warnings:
            combined_warnings.append(warning)

    if detailed_labs:
        abnormal_count = len(abnormal_labs)
        normal_count = len(normal_labs)
        summary = (
            "Most laboratory values are within the normal reference range."
            if abnormal_count == 0
            else f"There are {abnormal_count} notable laboratory finding{'s' if abnormal_count != 1 else ''} and {normal_count} value{'s' if normal_count != 1 else ''} within normal limits."
        )
        lines.append("## Detailed Laboratory Review")
        lines.append(summary)
        lines.append("")
        lines.append("| Test | Result | Normal Range | Status | Interpretation |")
        lines.append("| --- | --- | --- | --- | --- |")
        for lab in detailed_labs[:60]:
            result = lab["value"]
            if lab["unit"]:
                result = f"{result} {lab['unit']}"
            lines.append(
                f"| {lab['test_name']} | {result} | {lab['normal_range']} | {lab['status']} | {lab['interpretation']} |"
            )
        lines.append("")

        if abnormal_labs:
            lines.append("### Notable Abnormalities")
            for lab in abnormal_labs[:30]:
                unit = f" {lab['unit']}" if lab["unit"] else ""
                lines.append(
                    f"- **{lab['test_name']}**: {lab['value']}{unit} (Normal: {lab['normal_range']}) — {lab['interpretation']}"
                )
            lines.append("")

        if normal_labs:
            lines.append("### Normal / Reassuring Findings")
            for lab in normal_labs[:30]:
                unit = f" {lab['unit']}" if lab["unit"] else ""
                lines.append(
                    f"- **{lab['test_name']}**: {lab['value']}{unit} (Normal: {lab['normal_range']})"
                )
            lines.append("")

        if unreadable_labs:
            lines.append("### Unclear / Unreadable Items")
            for lab in unreadable_labs[:8]:
                lines.append(f"- **{lab['test_name']}**: unable to determine a reliable value from the document")
            lines.append("")

    if medications_raw:
        lines.append("## Prescription / Medication Details")
        for item in medications_raw[:40]:
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("text") or item.get("description") or "Unknown medication")
                dosage = str(item.get("dosage") or item.get("strength") or "").strip()
                frequency = str(item.get("frequency") or "").strip()
                route = str(item.get("route") or "").strip()
                duration = str(item.get("duration") or "").strip()
                status = str(item.get("status") or "").strip()
                details = [part for part in [dosage, frequency, route, duration, status] if part]
                lines.append(f"- **{name}**: {', '.join(details) if details else 'Not fully specified'}")
            else:
                lines.append(f"- {str(item).strip()}")
        lines.append("")

    if diagnoses:
        lines.append("## Impression")
        lines.extend(f"- {item}" for item in diagnoses[:6])
        lines.append("")

    if clinical_findings:
        lines.append("## Key Findings")
        lines.extend(f"- {item}" for item in clinical_findings[:10])
        lines.append("")

    if recommendations:
        lines.append("## Recommendations")
        lines.extend(f"- {item}" for item in recommendations[:8])
        lines.append("")

    if combined_warnings:
        lines.append("## Warnings / Cautions")
        lines.extend(f"- {item}" for item in combined_warnings[:6])
        lines.append("")

    # Only show extracted text preview if no vision output and no structured data
    if not raw_analysis and not detailed_labs and not medications_raw and not diagnoses and not clinical_findings:
        raw_preview = str(unified_context.get("ocr_output") or "").strip()
        if raw_preview:
            lines.append("## Extracted Text Preview")
            lines.append(raw_preview[:1200])
            lines.append("")

    lines.append(
        "If you want, I can also explain any lab row, compare a specific value to its normal range, "
        "or turn this into a simpler patient-friendly summary."
    )

    suspected_conditions = diagnoses or ([classification] if classification and classification.lower() != "unknown" else [])
    symptoms = clinical_findings[:8]
    sources = [
        Source(
            book=doc_info.get("title") or filename,
            section=f"Uploaded {classification.lower() if classification else 'document'}",
        )
    ]

    return "\n".join(lines).strip(), suspected_conditions, symptoms, sources

# ─────────────────────────────────────────────────────────────────────────────
# POST /chat
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a health message and receive diagnosis + recommendations",
    status_code=status.HTTP_200_OK,
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Full MedCortex pipeline:
    1. Retrieve grounded medical evidence
    2. Derive lifestyle recommendations and doctor specialties
    3. Validate the response with the safety layer
    3. Save to DB
    """
    try:
        conv_id = request.conversation_id
        conversation_history = []
        
        # If authenticated, handle conversation logic
        if current_user:
            conv_service = ConversationService(db)
            if conv_id:
                conversation = conv_service.get_conversation(conv_id)
                if not conversation or conversation.user_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Conversation not found",
                    )
                # Fetch recent messages for context
                msg_service = MessageService(db)
                messages = msg_service.get_recent_messages(conv_id, limit=5)
                conversation_history = [{"role": m.role, "content": m.content} for m in messages]
            else:
                title = f"Consultation: {request.message[:40]}..." if len(request.message) > 40 else f"Consultation: {request.message}"
                conversation = conv_service.create_conversation(user_id=current_user.id, title=title)
                conv_id = conversation.id

        unified_context = _normalize_unified_context(request.unified_context)

        # ── Step 1: Prefer uploaded-document analysis when available ──
        if unified_context:
            final_answer, suspected_conditions, symptoms, sources = _build_document_response(
                unified_context=unified_context,
                user_message=request.message,
            )
            rag_result = {
                "answer": final_answer,
                "suspected_conditions": suspected_conditions,
                "symptoms": symptoms,
                "sources": [s.model_dump() for s in sources],
            }
        else:
            # ── Step 1: Retrieval / grounding ──
            rag_result = run_rag(
                user_message=request.message,
                db=db,
                user_id=current_user.id if current_user else None,
                conversation_id=conv_id,
            )
            sources = _build_sources(rag_result.get("sources", []) or [])
            symptoms = rag_result.get("symptoms", []) or []
            suspected_conditions = rag_result.get("suspected_conditions", []) or []
            final_answer = rag_result.get("answer", "") or "I could not generate a report."

        # ── Step 2: Clinical recommendations and doctor lookup ──
        lifestyle_payload = get_lifestyle_recommendations(
            suspected_conditions=suspected_conditions,
            symptoms=symptoms,
        )
        recommendations = _build_recommendations(lifestyle_payload)
        doctors = find_doctors(lifestyle_payload.get("doctor_specialties", []) or [])

        # ── Step 2.5: Prepare specialized branch context (for on-demand use) ──
        # These will be used when user clicks on specialized tabs
        specialized_context = {
            "suspected_conditions": suspected_conditions,
            "symptoms": symptoms,
            "query": request.message,
        }

        # ── Step 3: Safety Validation ──
        validator = ResponseValidator.create_default()
        safety_result = validator.validate(
            response=final_answer,
            query=request.message,
            source_context=" ".join(f"{s.book} {s.section}".strip() for s in sources),
            raw_confidence=0.8,
            evidence_count=max(len(sources), 1),
            citations=[f"{s.book} — {s.section}".strip(" —") for s in sources],
        )
        final_answer = safety_result.validated_response

        # ── Step 3: Persist messages if authenticated ──
        if current_user and conv_id:
            msg_service = MessageService(db)
            msg_service.store_message(
                conversation_id=conv_id,
                role="user",
                content=request.message,
            )
            msg_service.store_message(
                conversation_id=conv_id,
                role="assistant",
                content=rag_result.get("answer", "") or final_answer,
                citations=[s.model_dump() for s in sources],
                metadata_json={
                    "safety_score": safety_result.safety_score,
                    "issues": safety_result.issues,
                    "symptoms": symptoms,
                    "suspected_conditions": suspected_conditions,
                    "unified_context_present": unified_context is not None,
                }
            )
            memory_service = MemoryService(db)
            memory_service.auto_summarize(conv_id)
            memory_service.extract_and_store_facts(current_user.id, conv_id)

        # ── Step 2.6: Pre-compute specialized branches in parallel ──
        import asyncio
        loop = asyncio.get_running_loop()

        drugs_query = f"Drug information for: {', '.join(suspected_conditions) or 'general health'}"
        nutrition_query = f"Nutrition plan for: {', '.join(suspected_conditions) or 'general health'}"
        rehab_query = f"Rehabilitation exercises for: {', '.join(suspected_conditions) or 'general health'}"

        diagnosis_context = [
            final_answer,
            f"Conditions: {', '.join(suspected_conditions)}" if suspected_conditions else "",
            f"Symptoms: {', '.join(symptoms)}" if symptoms else "",
        ]
        diagnosis_context_str = "\n".join(filter(None, diagnosis_context))

        def run_drug_sync():
            try:
                res = get_drug_information(drugs_query, diagnosis_context_str)
                return res.get("answer")
            except Exception as ex:
                logger.error(f"Sync drug branch error: {ex}")
                return None

        def run_nutrition_sync():
            try:
                res = get_nutrition_information(nutrition_query, diagnosis_context_str)
                return res.get("answer")
            except Exception as ex:
                logger.error(f"Sync nutrition branch error: {ex}")
                return None

        def run_rehab_sync():
            try:
                res = get_rehab_information(rehab_query, diagnosis_context_str)
                return res.get("answer")
            except Exception as ex:
                logger.error(f"Sync rehab branch error: {ex}")
                return None

        drugs_answer, nutrition_answer, rehab_answer = await asyncio.gather(
            loop.run_in_executor(None, run_drug_sync),
            loop.run_in_executor(None, run_nutrition_sync),
            loop.run_in_executor(None, run_rehab_sync),
        )

        return ChatResponse(
            answer=final_answer,
            suspected_conditions=suspected_conditions,
            symptoms=symptoms,
            sources=sources,
            recommendations=recommendations,
            doctors=doctors,
            conversation_id=conv_id,
            specialized_context=specialized_context,
            drugs_answer=drugs_answer,
            nutrition_answer=nutrition_answer,
            rehab_answer=rehab_answer,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Pipeline Error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MedCortex pipeline error: {str(e)}",
        )

@router.get("/health", summary="Check chat service is alive")
async def health():
    return {"status": "ok", "service": "MedCortex Chat"}
