# backend/app/ai/graph/multimodal_nodes.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Pipeline Graph Nodes
# Real execution nodes for the multimodal upload LangGraph.
#
# Each node reads/writes the shared `MultimodalPipelineState` and mutates the
# `ProcessingContext` in place via the existing services. Nodes are defensive:
# a failure in one enrichment node is recorded in state and never aborts the
# whole graph — the pipeline always reaches `finalize_node`.
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import logging
from typing import Any, Dict, Optional

from app.ai.clinical.interaction_checker import InteractionChecker
from app.ai.clinical.lab_interpreter import LabInterpretationService
from app.ai.multimodal.enums import DocumentType, PipelineStage, ProcessorType
from app.ai.multimodal.logger import MultimodalLogger
from app.ai.multimodal.medical_image_analyzer import medical_image_analyzer
from app.ai.multimodal.schemas import ProcessingContext
from app.ai.ocr.service import OCRService
from app.ai.shared.medical_parser import SharedMedicalParser
from app.ai.vision.service import VisionService

logger = logging.getLogger("medcortex.graph.multimodal")


def _meta(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return the mutable metadata dict from state (created if missing)."""
    meta = dict(state.get("metadata") or {})
    return meta


async def route_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry node. Mirrors the orchestrator's processor decision into state so
    the conditional edges can fan out, and resolves enrichment intent flags.
    """
    context: ProcessingContext = state["context"]
    processor = context.processor_type or ProcessorType.UNKNOWN

    # Override processor type if user explicitly selected medical_image upload type
    if context.upload_type == "medical_image":
        processor = ProcessorType.MEDICAL_IMAGE

    needs_lab = context.document_type == DocumentType.LAB_REPORT
    needs_drug = bool(context.unified_context.medications) or context.document_type == DocumentType.PRESCRIPTION

    MultimodalLogger.log_event(
        PipelineStage.WORKFLOW_STARTED,
        context.upload_id,
        f"Multimodal graph routing -> {processor.value}",
        {
            "processor": processor.value,
            "document_type": context.document_type.value,
            "needs_lab": needs_lab,
            "needs_drug": needs_drug,
            "upload_type": context.upload_type,
        },
    )

    meta = _meta(state)
    meta["processor"] = processor.value
    meta["document_type"] = context.document_type.value

    return {
        "processor": processor,
        "needs_lab_interpretation": needs_lab,
        "needs_drug_interaction": needs_drug,
        "metadata": meta,
    }


async def vision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Vision service (Gemini) for images and PDFs."""
    context: ProcessingContext = state["context"]
    try:
        service = VisionService()
        await service.process(context)
    except Exception as exc:  # non-fatal
        logger.exception("Vision node failed for %s", context.upload_id)
        return {"error": f"vision: {exc}", "metadata": _meta(state)}
    return {}


async def ocr_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the OCR service for scanned documents."""
    context: ProcessingContext = state["context"]
    try:
        service = OCRService()
        await service.process(context)
    except Exception as exc:  # non-fatal
        logger.exception("OCR node failed for %s", context.upload_id)
        return {"error": f"ocr: {exc}", "metadata": _meta(state)}
    return {}


async def text_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the shared medical parser directly on plain-text uploads (no OCR/Vision).
    """
    context: ProcessingContext = state["context"]
    try:
        raw_text = (context.file_bytes or b"").decode("utf-8", errors="ignore")
        parser = SharedMedicalParser()
        await parser.parse(raw_text, context)
    except Exception as exc:  # non-fatal
        logger.exception("Text parse node failed for %s", context.upload_id)
        return {"error": f"text: {exc}", "metadata": _meta(state)}
    return {}


async def medical_image_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the medical image analyzer for wound/skin condition analysis.
    Uses Groq Vision models with HuggingFace fallback.
    """
    context: ProcessingContext = state["context"]
    try:
        # Use the preprocessed bytes if available, otherwise use original file bytes
        image_bytes = context.preprocessed_bytes or context.file_bytes
        mime_type = context.mime_type or "image/jpeg"
        
        result = medical_image_analyzer.analyze_medical_image(image_bytes, mime_type)
        
        # Store the analysis result in the unified context
        context.unified_context.vision_output = result["answer"]
        context.unified_context.processing_metadata.provider = "Groq" if result["source_type"] == "vision_groq" else "HuggingFace"
        context.unified_context.processing_metadata.model_name = result["model_used"]
        
        # Add to clinical findings
        context.unified_context.clinical_findings.append(result["answer"])
        
        # Update confidence scores
        context.unified_context.vision_confidence = 0.8 if result["source_type"] == "vision_groq" else 0.5
        context.unified_context.confidence_scores.vision = context.unified_context.vision_confidence
        
        MultimodalLogger.log_event(
            PipelineStage.VISION_COMPLETED,
            context.upload_id,
            f"Medical image analysis completed using {result['model_used']}",
            {
                "source_type": result["source_type"],
                "model_used": result["model_used"],
            },
        )
    except Exception as exc:  # non-fatal
        logger.exception("Medical image analysis failed for %s", context.upload_id)
        return {"error": f"medical_image: {exc}", "metadata": _meta(state)}
    return {}


async def lab_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret structured lab values extracted by Vision/OCR against the
    reference-range engine. Skips silently if no usable values were parsed.
    """
    context: ProcessingContext = state["context"]
    lab_values = context.unified_context.lab_values or []
    if not lab_values:
        return {}

    # Build {test_name: numeric_value}, tolerating non-numeric entries.
    values: Dict[str, float] = {}
    for lv in lab_values:
        if lv.name and lv.value is not None:
            try:
                values[lv.name] = float(lv.value)
            except (TypeError, ValueError):
                continue

    if not values:
        return {}

    try:
        service = LabInterpretationService()
        # Sync service — run off the event loop.
        result = await asyncio.to_thread(service.analyze_lab_report, values)
    except Exception as exc:  # non-fatal
        logger.exception("Lab interpretation failed for %s", context.upload_id)
        return {"error": f"lab: {exc}", "metadata": _meta(state)}

    meta = _meta(state)
    meta["lab_interpretation"] = result
    return {"metadata": meta}


async def drug_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check pairwise drug-drug interactions for extracted medications.
    Skips silently if fewer than two medications are present.
    """
    context: ProcessingContext = state["context"]
    meds = [m.name for m in (context.unified_context.medications or []) if m.name]
    if len(meds) < 2:
        return {}

    try:
        checker = InteractionChecker()
        interactions = await asyncio.to_thread(checker.check, meds)
    except Exception as exc:  # non-fatal
        logger.exception("Drug interaction check failed for %s", context.upload_id)
        return {"error": f"drug: {exc}", "metadata": _meta(state)}

    meta = _meta(state)
    meta["drug_interactions"] = [i.model_dump() for i in interactions]
    return {"metadata": meta}


async def finalize_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Terminal node. Blends component confidences into the overall score and
    records pipeline completion. Always reached, even when enrichment nodes
    recorded non-fatal errors.
    """
    context: ProcessingContext = state["context"]
    unified = context.unified_context

    scores = unified.confidence_scores
    component_scores = [
        v for v in (scores.classification, scores.ocr, scores.vision, scores.parser) if v is not None
    ]
    if component_scores:
        unified.overall_confidence = round(sum(component_scores) / len(component_scores), 4)

    if state.get("error"):
        unified.warnings.append(state["error"])

    unified.processing_history.append(
        _history_entry(state, PipelineStage.WORKFLOW_COMPLETED, "Multimodal graph execution completed")
    )

    meta = _meta(state)
    meta["completed"] = True

    MultimodalLogger.log_stage_complete(
        PipelineStage.PIPELINE_COMPLETED,
        context.upload_id,
        {"overall_confidence": unified.overall_confidence, "warnings": len(unified.warnings)},
    )

    return {"context": context, "metadata": meta}


def _history_entry(state: Dict[str, Any], stage: PipelineStage, message: str):
    """Build a ProcessingHistoryEntry with provider/model from metadata when present."""
    from app.ai.multimodal.schemas import ProcessingHistoryEntry

    meta = state.get("metadata") or {}
    return ProcessingHistoryEntry(
        stage=stage,
        message=message,
        provider=meta.get("provider"),
        model_name=meta.get("model_name"),
    )


# --------------------------------------------------------------------------- #
# Conditional-edge router functions
# --------------------------------------------------------------------------- #
def route_after_route(state: Dict[str, Any]) -> str:
    """Choose the extraction branch based on the processor decision."""
    processor = state.get("processor") or ProcessorType.UNKNOWN
    if processor == ProcessorType.VISION:
        return "vision"
    if processor == ProcessorType.OCR:
        return "ocr"
    if processor == ProcessorType.TEXT:
        return "text"
    if processor == ProcessorType.MEDICAL_IMAGE:
        return "medical_image"
    # UNKNOWN: nothing to extract — go straight to finalize.
    return "finalize"


def maybe_lab(state: Dict[str, Any]) -> str:
    """After extraction, run lab interpretation if flagged and values exist."""
    if state.get("needs_lab_interpretation") and state.get("context"):
        context: ProcessingContext = state["context"]
        if context.unified_context.lab_values:
            return "lab"
    return "drug"


def maybe_drug(state: Dict[str, Any]) -> str:
    """Run drug-interaction check if flagged and enough meds exist."""
    if state.get("needs_drug_interaction") and state.get("context"):
        context: ProcessingContext = state["context"]
        if len([m for m in (context.unified_context.medications or []) if m.name]) >= 2:
            return "drug"
    return "finalize"
