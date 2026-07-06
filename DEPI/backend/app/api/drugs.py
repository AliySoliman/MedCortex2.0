# backend/app/api/drugs.py
# ─────────────────────────────────────────────────────────────────────────────
# Drugs API
# POST /drugs → Get drug information
# ─────────────────────────────────────────────────────────────────────────────

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.ai.branches.drug_branch import get_drug_information

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drugs", tags=["Drugs"])


class DrugRequest(BaseModel):
    query: str
    context: str
    language: str = "en"


@router.post("", status_code=status.HTTP_200_OK)
async def get_drug_info(request: DrugRequest):
    """
    Get drug information based on query and retrieved context.
    
    Accepts medication questions and returns detailed drug information
    including dosage, side effects, interactions, and warnings.
    """
    try:
        result = get_drug_information(
            query=request.query,
            context=request.context,
            language=request.language,
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception("Drug information error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drug information retrieval failed: {str(e)}",
        )
