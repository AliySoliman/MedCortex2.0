# backend/app/api/egyptian_hospitals.py
# ─────────────────────────────────────────────────────────────────────────────
# Egyptian Hospitals API
# POST /egyptian-hospitals → Search for Egyptian hospitals using geographic filtering
# ─────────────────────────────────────────────────────────────────────────────

import logging
import json
import math
import os
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/egyptian-hospitals", tags=["Egyptian Hospitals"])


class HospitalSearchRequest(BaseModel):
    query: str | None = None
    userCoordinates: dict | None = None
    governorate: str | None = None


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def load_hOSPITALS_data():
    """Load hospitals data from JSON file."""
    # Try multiple possible paths for the hospitals JSON file
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    possible_paths = [
        os.path.join(base_path, "..", "..", "..", "egypt_hospitals_full.json"),
        os.path.join(base_path, "..", "..", "..", "..", "egypt_hospitals_full.json"),
        "/Users/alisoliman/Developer/labs/DEPI Project/MedCortex2.0/egypt_hospitals_full.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Loading hospitals from: {path}")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    
    logger.warning("Egypt hospitals JSON file not found")
    return []


@router.post("", status_code=status.HTTP_200_OK)
async def search_egyptian_hospitals(request: HospitalSearchRequest):
    """
    Search for Egyptian hospitals using geographic filtering.
    
    Accepts query, user coordinates, and governorate filter.
    Returns ranked list of Egyptian hospitals with distance-based filtering.
    """
    try:
        hospitals = load_hOSPITALS_data()
        
        if not hospitals:
            return JSONResponse(content={
                "hospitals": [],
                "count": 0,
                "source": "egyptian_database"
            })
        
        # Get user coordinates if provided
        user_lat = None
        user_lng = None
        if request.userCoordinates and request.userCoordinates.get('lat') and request.userCoordinates.get('lng'):
            user_lat = float(request.userCoordinates['lat'])
            user_lng = float(request.userCoordinates['lng'])
            logger.info(f"Using user coordinates: {user_lat}, {user_lng}")
        
        # Filter and rank hospitals
        filtered_hospitals = []
        
        for hospital in hospitals:
            # Filter by governorate if specified
            if request.governorate:
                hospital_gov = hospital.get("governorate", "").lower()
                if request.governorate.lower() not in hospital_gov:
                    continue
            
            # Calculate distance if user coordinates are available
            distance = None
            if user_lat is not None and user_lng is not None:
                hospital_lat = hospital.get("latitude")
                hospital_lng = hospital.get("longitude")
                if hospital_lat is not None and hospital_lng is not None:
                    distance = haversine(user_lat, user_lng, float(hospital_lat), float(hospital_lng))
            
            # Filter by query if specified (search in name and address)
            if request.query:
                query_lower = request.query.lower()
                name = hospital.get("name", "").lower()
                address = hospital.get("address", "").lower()
                if query_lower not in name and query_lower not in address:
                    continue
            
            hospital_data = {
                "name": hospital.get("name"),
                "governorate": hospital.get("governorate"),
                "address": hospital.get("address"),
                "latitude": hospital.get("latitude"),
                "longitude": hospital.get("longitude"),
                "distance": distance,
                "source": "egyptian_database"
            }
            filtered_hospitals.append(hospital_data)
        
        # Sort by distance if available
        if user_lat is not None:
            filtered_hospitals.sort(key=lambda x: x["distance"] if x["distance"] is not None else float('inf'))
        
        # Limit results
        filtered_hospitals = filtered_hospitals[:50]
        
        logger.info(f"✓ Egyptian hospital search — {len(filtered_hospitals)} results found")
        
        return JSONResponse(content={
            "hospitals": filtered_hospitals,
            "count": len(filtered_hospitals),
            "source": "egyptian_database"
        })
        
    except Exception as e:
        logger.exception("Egyptian hospital search error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Egyptian hospital search failed: {str(e)}",
        )
