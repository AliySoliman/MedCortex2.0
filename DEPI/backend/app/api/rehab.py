# backend/app/api/rehab.py
# ─────────────────────────────────────────────────────────────────────────────
# Rehab API
# POST /rehab → Get rehabilitation information
# ─────────────────────────────────────────────────────────────────────────────

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.ai.branches.rehab_branch import get_rehab_information

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rehab", tags=["Rehab"])


class RehabRequest(BaseModel):
    query: str
    context: str
    language: str = "en"


@router.post("", status_code=status.HTTP_200_OK)
async def get_rehab_info(request: RehabRequest):
    """
    Get rehabilitation information based on query and retrieved context.
    
    Accepts rehab and exercise questions and returns exercise protocols,
    recovery timelines, and physical therapy guidance.
    """
    try:
        result = get_rehab_information(
            query=request.query,
            context=request.context,
            language=request.language,
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception("Rehab information error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rehab information retrieval failed: {str(e)}",
        )
