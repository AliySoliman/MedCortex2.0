# backend/app/api/nutrition.py
# ─────────────────────────────────────────────────────────────────────────────
# Nutrition API
# POST /nutrition → Get nutrition information
# ─────────────────────────────────────────────────────────────────────────────

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.ai.branches.nutrition_branch import get_nutrition_information

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


class NutritionRequest(BaseModel):
    query: str
    context: str
    language: str = "en"


@router.post("", status_code=status.HTTP_200_OK)
async def get_nutrition_info(request: NutritionRequest):
    """
    Get nutrition information based on query and retrieved context.
    
    Accepts nutrition questions and returns dietary advice,
    meal plans, and food recommendations.
    """
    try:
        result = get_nutrition_information(
            query=request.query,
            context=request.context,
            language=request.language,
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.exception("Nutrition information error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Nutrition information retrieval failed: {str(e)}",
        )
