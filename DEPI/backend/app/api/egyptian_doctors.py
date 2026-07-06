# backend/app/api/egyptian_doctors.py
# ─────────────────────────────────────────────────────────────────────────────
# Egyptian Doctors API
# POST /egyptian-doctors → Search for Egyptian doctors using geographic filtering
# ─────────────────────────────────────────────────────────────────────────────

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/egyptian-doctors", tags=["Egyptian Doctors"])


class DoctorSearchRequest(BaseModel):
    query: str
    location: str | None = None
    specialty: str | None = None
    userCoordinates: dict | None = None


@router.post("", status_code=status.HTTP_200_OK)
async def search_egyptian_doctors(request: DoctorSearchRequest):
    """
    Search for Egyptian doctors using the new doctor node with geographic filtering.
    
    Accepts medical specialty and location queries.
    Returns ranked list of Egyptian doctors with distance-based filtering.
    """
    try:
        from app.ai.branches.doctor_branch import search_egyptian_doctors

        doctors = search_egyptian_doctors(
            query=request.query,
            location=request.location,
            specialty=request.specialty,
            user_coordinates=request.userCoordinates,
        )
        
        return JSONResponse(content={
            "doctors": doctors,
            "count": len(doctors),
            "source": "egyptian_database"
        })
        
    except Exception as e:
        logger.exception("Egyptian doctor search error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Egyptian doctor search failed: {str(e)}",
        )
