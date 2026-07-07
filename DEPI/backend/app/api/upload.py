# backend/app/api/upload.py
# ─────────────────────────────────────────────────────────────────────────────
# Upload API
# ─────────────────────────────────────────────────────────────────────────────

from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session
import uuid

from app.database.database import get_db
from app.models.user import User
from app.api.chat import get_current_user_optional
from app.ai.multimodal.orchestrator import MultimodalOrchestrator
from app.ai.graph.multimodal_builder import get_multimodal_graph

router = APIRouter(prefix="/upload", tags=["Uploads"])

# Instantiate the primary orchestrator (LLM brain + heuristic fallback)
multimodal_engine = MultimodalOrchestrator()
# Compiled multimodal execution graph (cached)
multimodal_graph = get_multimodal_graph()


@router.post("", summary="Upload a medical document or image for unified processing")
async def process_upload(
    file: UploadFile = File(...),
    upload_type: str = "document",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Ingests a file through the Multimodal Engine.
    Validates, Classifies, Routes to OCR or Vision, Parses into JSON,
    and returns a UnifiedMedicalContext.

    Phase 1 — MultimodalOrchestrator: LLM-driven classify + route (with
    heuristic fallback) and preprocessing.
    Phase 2 — Multimodal LangGraph: executes the routed processor and any
    conditional enrichments (lab interpretation, drug interactions) based on
    the extracted content.
    """
    try:
        file_bytes = await file.read()
        upload_id = str(uuid.uuid4())
        mime_type = file.content_type or "application/octet-stream"

        # Phase 1: LLM-driven routing and preprocessing
        context = await multimodal_engine.process_upload(
            upload_id=upload_id,
            filename=file.filename,
            mime_type=mime_type,
            file_bytes=file_bytes,
            upload_type=upload_type
        )

        # Phase 2: Execution through the multimodal LangGraph.
        # The graph fans out by processor (vision/ocr/text) and runs
        # conditional lab/drug enrichments before finalizing.
        final_state = await multimodal_graph.ainvoke({"context": context})
        context = final_state.get("context", context)

        return {
            "status": "success",
            "upload_id": upload_id,
            "unified_context": context.unified_context.model_dump()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )

# Future endpoints
@router.post("/ocr", summary="Force OCR processing")
async def process_ocr(file: UploadFile = File(...)):
    """Bypasses standard routing, forces OCR."""
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.post("/vision", summary="Force Vision processing")
async def process_vision(file: UploadFile = File(...)):
    """Bypasses standard routing, forces Vision."""
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.post("/analyze", summary="Analyze processed context")
async def analyze_context(context_id: str):
    """Triggers LangGraph workflows directly from an existing context."""
    raise HTTPException(status_code=501, detail="Not Implemented")
