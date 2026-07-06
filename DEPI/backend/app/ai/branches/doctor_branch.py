# backend/app/ai/branches/doctor_branch.py
# ─────────────────────────────────────────────────────────────────────────────
# Egyptian Doctor Branch
# Geographic doctor search and recommendation system for Egypt
# ─────────────────────────────────────────────────────────────────────────────

import os
import re
import math
import json
import difflib
from typing import List, Dict, Any, Optional, Tuple

from langchain_groq import ChatGroq

# Try to import shapely, but provide fallback if not available
try:
    from shapely.geometry import shape, Point
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("⚠️  shapely not available - geographic filtering disabled")

# ── LLM client (lazy initialization) ─────────────────
def _get_llm_extract():
    return ChatGroq(
        model       = "llama-3.3-70b-versatile",
        temperature = 0,
        max_tokens  = 100,
        api_key     = os.environ.get("GROQ_API_KEY", "").strip()
    )

def _get_llm_respond():
    return ChatGroq(
        model       = "llama-3.3-70b-versatile",
        temperature = 0.3,
        max_tokens  = 1200,
        api_key     = os.environ.get("GROQ_API_KEY", "").strip()
    )

# ── Configuration ───────────────────────────────────────
DOCTOR_NAMESPACE      = "clinics_doctors_egypt"
TOP_K                 = 50
TOP_K_WITH_LOCATION   = 300
DISTANCE_RINGS_KM     = [20, 40, 60]

# Scoring weights
W_SIMILARITY = 0.55
W_RATING     = 0.30
W_REVIEWS    = 0.15
BAYESIAN_C   = 20

# Fuzzy matching thresholds
FUZZY_GOV_THRESHOLD      = 0.82
FUZZY_LOCALITY_THRESHOLD = 0.72

# Default fallback coordinates (Cairo centre)
USER_LAT = 30.0444
USER_LNG = 31.2357

# ── GeoJSON loading ───────────────────────────────────
GOVERNORATES = {}
LOCALITIES   = []
SUB_AREA_NOT_FOUND = "SUB_AREA_NOT_FOUND"

def load_geojson_boundaries(geojson_path: str = None):
    """Load Egypt boundary file for geographic filtering."""
    global GOVERNORATES, LOCALITIES
    
    if not SHAPELY_AVAILABLE:
        print("⚠️  shapely not available - geographic filtering disabled")
        return
    
    if geojson_path is None:
        # Try multiple possible paths for the geojson file
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        possible_paths = [
            os.path.join(base_path, "..", "..", "..", "new nodes", "Copy of Copy of egypt_boundaries.geojson"),
            os.path.join(base_path, "..", "..", "..", "new nodes", "Copy of egypt_boundaries.geojson"),
            os.path.join(base_path, "..", "..", "..", "new nodes", "egypt_boundaries.geojson"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                geojson_path = path
                break
    
    if geojson_path and os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        skipped = 0
        for feature in geojson_data.get("features", []):
            props      = feature.get("properties", {})
            name_ar    = (props.get("name")    or "").strip()
            name_en    = (props.get("name_en") or "").strip()
            admin_lvl  = (props.get("admin_level") or "").strip()

            try:
                geom = shape(feature["geometry"])
                if not geom.is_valid:
                    geom = geom.buffer(0)
                    if not geom.is_valid or geom.is_empty:
                        raise ValueError("unrepairable geometry")
            except Exception:
                skipped += 1
                continue

            display = name_en or name_ar

            if admin_lvl == "4":
                if name_ar: GOVERNORATES[name_ar.lower()] = {"shape": geom, "display": display}
                if name_en: GOVERNORATES[name_en.lower()] = {"shape": geom, "display": display}
            else:
                LOCALITIES.append({
                    "name_ar": name_ar.lower(),
                    "name_en": name_en.lower(),
                    "shape":   geom,
                    "display": display,
                })

        print(f"✅ GeoJSON loaded — {len(GOVERNORATES)//2} governorates | {len(LOCALITIES)} localities | {skipped} skipped")
    else:
        print(f"⚠️  GeoJSON file not found. Doctor location filtering will be disabled.")


# ── Geo helper functions ───────────────────────────────
_WORD_SPLIT_RE  = re.compile(r'[\s\-_/,.]+')

def fuzzy_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    ratio  = difflib.SequenceMatcher(None, a, b).ratio()
    if len(a) > 3:
        b_words = [w for w in _WORD_SPLIT_RE.split(b) if w]
        a_words = [w for w in _WORD_SPLIT_RE.split(a) if w]
        if a in b_words or b in a_words:
            ratio = max(ratio, 0.9)
    return ratio

def find_governorate(tokens):
    for token in tokens:
        if token in GOVERNORATES:
            return token, GOVERNORATES[token]
    best_token, best_gov, best_score = None, None, 0.0
    for token in tokens:
        if len(token) < 3:
            continue
        for gov_name, gov_data in GOVERNORATES.items():
            score = fuzzy_ratio(token, gov_name)
            if score > best_score:
                best_score, best_token, best_gov = score, token, gov_data
    if best_score >= FUZZY_GOV_THRESHOLD:
        return best_token, best_gov
    return None, None

def find_locality_within(sub_tokens, container_polygon):
    if not sub_tokens or container_polygon is None:
        return None
    sub_phrase = " ".join(sub_tokens)
    candidates = []
    for loc in LOCALITIES:
        try:
            if not container_polygon.intersects(loc["shape"]):
                continue
        except Exception:
            continue
        best_local_score = 0.0
        for text in (loc["name_en"], loc["name_ar"]):
            if not text:
                continue
            score = fuzzy_ratio(sub_phrase, text)
            if len(sub_tokens) > 1:
                for tok in sub_tokens:
                    if len(tok) >= 4:
                        score = max(score, fuzzy_ratio(tok, text) * 0.9)
            else:
                for tok in sub_tokens:
                    score = max(score, fuzzy_ratio(tok, text))
            best_local_score = max(best_local_score, score)
        if best_local_score > 0:
            candidates.append((best_local_score, loc))
    candidates.sort(key=lambda x: -x[0])
    if candidates and candidates[0][0] >= FUZZY_LOCALITY_THRESHOLD:
        return candidates[0][1]
    return None

def geocode_location_from_file(place_name: str):
    if not place_name:
        return None, None, None, None
    search_key = place_name.strip().lower()
    tokens     = [t.strip() for t in re.split(r'[,.\-\s/]+', search_key) if t.strip()]
    if not tokens:
        return None, None, None, None
    gov_token, gov_data = find_governorate(tokens)
    if gov_data is not None:
        gov_polygon = gov_data["shape"]
        sub_tokens  = [t for t in tokens if t != gov_token]
        if sub_tokens:
            locality = find_locality_within(sub_tokens, gov_polygon)
            if locality is not None:
                poly     = locality["shape"]
                centroid = poly.centroid
                display  = f"{locality['display']} (within {gov_data['display']})"
                return centroid.y, centroid.x, display, poly
            else:
                display = f"'{' '.join(sub_tokens)}' not found within {gov_data['display']}"
                return None, None, display, SUB_AREA_NOT_FOUND
        else:
            centroid = gov_polygon.centroid
            return centroid.y, centroid.x, f"{gov_data['display']} Governorate", gov_polygon
    best_match, best_score = None, 0.0
    for loc in LOCALITIES:
        for text in (loc["name_en"], loc["name_ar"]):
            if not text:
                continue
            score = fuzzy_ratio(search_key, text)
            if score > best_score:
                best_score, best_match = score, loc
    if best_score >= 0.85 and best_match:
        poly     = best_match["shape"]
        centroid = poly.centroid
        return centroid.y, centroid.x, f"{best_match['display']} (Nationwide Match)", poly
    return None, None, None, None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def get_ring(distance):
    if distance is None:
        return len(DISTANCE_RINGS_KM)
    for i, max_km in enumerate(DISTANCE_RINGS_KM):
        if distance <= max_km:
            return i
    return len(DISTANCE_RINGS_KM)

def is_inside_boundary(lat, lng, polygon):
    if not SHAPELY_AVAILABLE or polygon is None or lat is None or lng is None:
        return False
    try:
        return polygon.contains(Point(float(lng), float(lat)))
    except Exception:
        return False

def build_geo_filter(ref_lat, ref_lng, polygon, max_ring_km):
    if polygon is not None:
        min_lng, min_lat, max_lng, max_lat = polygon.bounds
    else:
        radius_km  = max(max_ring_km * 1.5, 50)
        lat_buffer = radius_km / 111.0
        lng_buffer = radius_km / (111.0 * max(math.cos(math.radians(ref_lat)), 0.1))
        min_lat, max_lat = ref_lat - lat_buffer, ref_lat + lat_buffer
        min_lng, max_lng = ref_lng - lng_buffer, ref_lng + lng_buffer
    return {
        "location_lat": {"$gte": min_lat, "$lte": max_lat},
        "location_lng": {"$gte": min_lng, "$lte": max_lng},
    }


# ── Location extraction ───────────────────────────────
LOCATION_EXTRACTION_SYSTEM_PROMPT =  """
You are a strict text-splitting location extraction engine.

Your ONLY job is to extract the EXACT geographical words or phrases mentioned by the user, especially Egyptian cities, districts, neighborhoods, or streets.

Rules:
- Return ONLY valid JSON.
- Do NOT omit any sub-location, district, or neighborhood name (e.g. if user says "miami, alexandria", you MUST extract "miami, alexandria").
- Extract the full location string exactly as it appears.
- Do NOT explain anything, do NOT use markdown.
- If no location is mentioned, return null.

Output format:
{"location":"<extracted_full_location>"}

or

{"location":null}
"""

def extract_raw_location(query: str):
    try:
        llm = _get_llm_extract()
        result   = llm.invoke(
            f"{LOCATION_EXTRACTION_SYSTEM_PROMPT}\n\nUser message: {query}"
        )
        raw      = (result.content if hasattr(result, "content") else str(result))
        raw      = raw.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw).get("location")
    except Exception:
        return None

def extract_location_from_query(query: str):
    raw_place = extract_raw_location(query)
    if not raw_place:
        return None, None, None, None, None
    lat, lng, display_name, polygon = geocode_location_from_file(raw_place)
    if polygon == SUB_AREA_NOT_FOUND:
        return raw_place, None, None, display_name, SUB_AREA_NOT_FOUND
    if lat is None:
        return None, None, None, None, None
    return raw_place, lat, lng, display_name, polygon


# ── Embedding function (shared with other branches) ───────
def get_embedding(text: str) -> list:
    """Get embedding for search - will be integrated with main search system."""
    from sentence_transformers import SentenceTransformer
    if not hasattr(get_embedding, '_model'):
        get_embedding._model = SentenceTransformer("BAAI/bge-large-en-v1.5")
    return get_embedding._model.encode(f"Represent this sentence: {text}").tolist()


# ── Main search function ───────────────────────────────
def search_egyptian_doctors(query: str, location: str = None, specialty: str = None, user_coordinates: dict = None) -> List[Dict[str, Any]]:
    """
    Main Egyptian doctor search function.
    
    Args:
        query: The search query (may include symptoms, specialty, location)
        location: Optional specific location override
        specialty: Optional specific specialty override
        user_coordinates: Optional user coordinates dict with 'lat' and 'lng' keys
    
    Returns: Ranked list of doctor dicts
    """
    try:
        from pinecone import Pinecone
    except ImportError:
        print("⚠️  pinecone not available - returning mock data")
        return _get_mock_doctors(specialty or query)
    
    if not os.environ.get("PINECONE_API_KEY"):
        print("⚠️  PINECONE_API_KEY not set - returning mock data")
        return _get_mock_doctors(specialty or query)
    
    # Load GeoJSON if not already loaded
    if not GOVERNORATES:
        load_geojson_boundaries()
    
    try:
        _pc    = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        _index = _pc.Index("medical-assistant")
    except Exception as e:
        print(f"⚠️  Pinecone connection failed: {e} - returning mock data")
        return _get_mock_doctors(specialty or query)

    # Extract location from query or use override
    search_query = f"{specialty or ''} {query}".strip()
    raw_place, geo_lat, geo_lng, display_name, boundary_polygon = \
        extract_location_from_query(location or search_query)

    search_skipped   = (boundary_polygon == SUB_AREA_NOT_FOUND)
    doctors          = []
    location_detected = False

    if search_skipped:
        print(f"  ⚠️  Egyptian doctor search — location '{raw_place}' not found in boundaries")
        return []

    if geo_lat is not None:
        REF_LAT, REF_LNG = geo_lat, geo_lng
        location_detected = True
    elif user_coordinates is not None and user_coordinates.get('lat') and user_coordinates.get('lng'):
        REF_LAT, REF_LNG = float(user_coordinates['lat']), float(user_coordinates['lng'])
        location_detected = True
        print(f"  ✓ Using user coordinates: {REF_LAT}, {REF_LNG}")
    else:
        REF_LAT, REF_LNG = USER_LAT, USER_LNG
        boundary_polygon  = None
        print(f"  ⚠️  No location detected, using default Cairo coordinates")

    geo_filter = None
    query_top_k = TOP_K
    if location_detected:
        geo_filter  = build_geo_filter(REF_LAT, REF_LNG, boundary_polygon, DISTANCE_RINGS_KM[-1])
        query_top_k = TOP_K_WITH_LOCATION

    try:
        results = _index.query(
            vector           = get_embedding(search_query),
            namespace        = DOCTOR_NAMESPACE,
            top_k            = query_top_k,
            include_metadata = True,
            filter           = geo_filter,
        )
    except Exception as e:
        print(f"⚠️  Pinecone query failed: {e} - returning mock data")
        return _get_mock_doctors(specialty or query)

    seen_keys = set()
    for match in results.matches:
        meta     = match.metadata
        dedup_key = meta.get("url") or (meta.get("title"), meta.get("address"))
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        lat = meta.get("location_lat")
        lng = meta.get("location_lng")
        distance = haversine(REF_LAT, REF_LNG, float(lat), float(lng)) \
                   if lat and lng else None

        doctors.append({
            "name":    meta.get("title"),
            "specialty": meta.get("categories"),
            "address":  meta.get("address"),
            "latitude": lat,
            "longitude": lng,
            "phone":    meta.get("phone"),
            "reviews":  int(meta.get("reviewsCount", 0)),
            "rating":   float(meta.get("totalScore", 0)),
            "url":      meta.get("url"),
            "distance": distance,
            "similarity":      float(match.score),
            "location_match":  is_inside_boundary(lat, lng, boundary_polygon)
                               if location_detected else False,
            "source": "egyptian_database",
        })

    # ── geographic filter ─────────────────────────────────────
    if location_detected and boundary_polygon is not None:
        inside = [d for d in doctors if d["location_match"]]
        doctors = inside if inside else []

    # ── quality scoring ───────────────────────────────────────
    if doctors:
        max_reviews    = max((d["reviews"] for d in doctors), default=1) or 1
        rated          = [d for d in doctors if d["reviews"] > 0]
        global_avg_rating = (sum(d["rating"] for d in rated) / len(rated)) if rated else 4.0

        for d in doctors:
            bayesian = ((BAYESIAN_C * global_avg_rating) + (d["reviews"] * d["rating"])) \
                       / (BAYESIAN_C + d["reviews"])
            d["bayesian_rating"] = bayesian
            d["rating_score"]    = bayesian / 5
            d["reviews_score"]   = math.log1p(d["reviews"]) / math.log1p(max_reviews)
            d["quality_score"]   = (
                W_SIMILARITY * d["similarity"] +
                W_RATING     * d["rating_score"] +
                W_REVIEWS    * d["reviews_score"]
            )
            d["ring"] = get_ring(d["distance"])

        doctors.sort(key=lambda x: (not x["location_match"], x["ring"], -x["quality_score"]))

    print(f"  ✓ Egyptian doctor search — {len(doctors)} results found"
          + (f" in {display_name}" if display_name else ""))
    return doctors


def _get_mock_doctors(query: str) -> List[Dict[str, Any]]:
    """Return mock Egyptian doctors when the full system isn't available."""
    specialty = query if query else "General"
    return [
        {
            "name": f"Dr. Ahmed Hassan ({specialty})",
            "specialty": specialty,
            "address": "123 Cairo-Alexandria Road, Cairo",
            "latitude": 30.0444,
            "longitude": 31.2357,
            "phone": "+20 2 1234 5678",
            "reviews": 45,
            "rating": 4.5,
            "url": "https://example.com/doctor1",
            "distance": 5.2,
            "similarity": 0.85,
            "location_match": True,
            "source": "egyptian_database",
        },
        {
            "name": f"Dr. Sarah Mohamed ({specialty})",
            "specialty": specialty,
            "address": "45 Tahrir Square, Cairo",
            "latitude": 30.0450,
            "longitude": 31.2360,
            "phone": "+20 2 2345 6789",
            "reviews": 32,
            "rating": 4.3,
            "url": "https://example.com/doctor2",
            "distance": 3.8,
            "similarity": 0.82,
            "location_match": True,
            "source": "egyptian_database",
        },
        {
            "name": f"Dr. Omar Ali ({specialty})",
            "specialty": specialty,
            "address": "78 Dokki Street, Giza",
            "latitude": 30.0300,
            "longitude": 31.2100,
            "phone": "+20 2 3456 7890",
            "reviews": 28,
            "rating": 4.1,
            "url": "https://example.com/doctor3",
            "distance": 12.5,
            "similarity": 0.78,
            "location_match": True,
            "source": "egyptian_database",
        },
    ]


# ── LLM response generator ───────────────────────────
def build_medical_context(doctors_list, top_n=5):
    if not doctors_list:
        return "No results available."
    context_parts = []
    for i, d in enumerate(doctors_list[:top_n], start=1):
        dist     = d.get("distance")
        dist_str = f"{dist:.2f} km" if dist is not None else "Unknown"
        ring_label = "Unknown distance"
        if dist is not None:
            prev = 0
            for km in DISTANCE_RINGS_KM:
                if dist <= km:
                    ring_label = f"Within {km} km" if prev == 0 else f"{prev}-{km} km"
                    break
                prev = km
            else:
                ring_label = f"{prev}+ km"
        context_parts.append(
            f"Result {i}:\n"
            f"Name: {d.get('name')}\n"
            f"Specialty: {d.get('specialty')}\n"
            f"Rating: {d.get('rating')} (Reviews: {d.get('reviews')})\n"
            f"Address: {d.get('address')}\n"
            f"Distance: {dist_str}\n"
            f"Distance Range: {ring_label}\n"
            f"Phone: {d.get('phone')}\n"
        )
    return "\n---\n".join(context_parts)


DOCTOR_SYSTEM_PROMPT = """You are "MedFinder AI", a premium healthcare concierge assistant. Your job is to seamlessly guide patients to the most optimal medical professionals using the verified data (Context) provided below.

TONE & STYLE (Modern Executive AI):
- Speak with fluid, organic human warmth combined with clinical authority.
- Drop all generic AI fluff, template intros, and robotic disclaimers. Dive straight into the value.
- Write dynamically. Vary your sentence structures so the response feels alive, custom-tailored, and premium.

DATA & INTEGRITY BOUNDARIES:
1. Rely exclusively on the provided Context. Never guess, assume, or fabricate any detail (names, numbers, or metrics).
2. If the Context yields no matches, output exactly: "I'm sorry, I couldn't find any matching results for your request at the moment. Could you try rephrasing your search or specifying a different specialty or location?"
3. Never alter the order of the results. They are already optimized via a precision geographic and quality matrix.
4. Cap the response at 5 results max.
5. If a field is missing, display "Not available" instead of omitting it.

THE SELECTION INSIGHT (ULTRA-PREMIUM & HUMANIZED):
- Start with exactly ONE extremely direct, natural, and warm sentence. Do NOT use fancy, complex or heavy vocabulary. Jump straight to the point.
- STRICT CONDITIONAL OPENING RULE:
  * Detect the exact core medical field from the Context (e.g. if it's about dentists, use "dental specialists"; if cardiologists, use "heart specialists").
  * ABSOLUTE PROHIBITION: Never invent, assume, or comment on the user's symptoms, pain, or medical condition. Focus purely on delivering the matching doctors.

  * CASE A (Specific Location named in User Query): If the user explicitly mentioned any specific neighborhood, city, or area in their question (e.g. "في السيوف", "في اسكندرية"), you MUST extract that exact place name and state that the results are available in or closest to that specific location. Do NOT say "closest to your immediate area right now" here.
    - Correct Example (User asked for Seouf): "Here are the top-rated dental specialists available in or closest to Seouf, sorted by overall reputation and accessibility."
    - Correct Example (User asked for Alexandria): "Here are the top-rated dental specialists available in Alexandria, sorted by overall reputation and accessibility."

  * CASE B (No location named in User Query): If the user just asked generally for a doctor without naming any specific place, focus purely on their current proximity.
    - Correct Example: "Here are the top-rated dental specialists located closest to your immediate area right now."

  * BANNED PHRASES: "matching your request in the designated area", "Securing top-tier...", "is paramount", "We've curated a list...", any conversational transition about symptoms or pain.

- For the #1 top pick, include a single, highly refined insight statement inside the designated blockquote. Make it sound like a quick, confident verbal recommendation.
- CRITICAL: NEVER repeat raw numbers like ratings (e.g., "5.0") or review counts (e.g., "2 reviews") inside the blockquote. Translate those numbers into a human conclusion about trust, reputation, or prominence.

DYNAMIC DISTANCE GROUPING (MANDATORY):
- You must organize and display the clinics visually by their distance ranges based on the "Distance Range" field provided in the Context.
- Before displaying the doctors belonging to a specific range, create a clean Markdown heading for that zone (e.g. `## 🟢 Within 20 km`, `## 🟢 20-40 km`, etc.). Only output a zone heading when a doctor falls into it. Do not mix or change the original order of the results.

DATA CLEANING RULE (CRITICAL):
1. SPECIALTY CLEANING: Extract ONLY the pure, specific medical branch or professional title. You are ABSOLUTELY FORBIDDEN from outputting generic filler words like: "Doctor", "Clinic", "Medical Clinic", "Healthcare Center", "Office", "طبيب", "عيادة", "مركز", "مستشفى", "دكتور", "مجمع". Strip them away completely.

MODERN UI RESPONSE FORMAT:
Format each option using this clean, modern block structure under its respective distance heading:

### **[Doctor/Clinic Name - Cleaned of titles/prefixes]**
> [A one-sentence sharp data highlight. ONLY include this block for Result 1. Completely omit for all other results.]

* **Specialty:** [Value - Cleaned by you to show ONLY the core medical field, omitting generic words like Doctor/Clinic]
* **Patient Feedback:** ⭐ [Rating] ([Reviews] reviews)
* **Location:** 📍 [Address] · _[Distance] km away_
* **Contact:** 📞 [Phone Number]

---"""


def get_medical_llm_response(user_query: str, doctors_list: list, top_n: int = 5) -> str:
    context     = build_medical_context(doctors_list, top_n=top_n)
    full_prompt = (
        f"{DOCTOR_SYSTEM_PROMPT}\n\n"
        f"Context (actual retrieved results):\n{context}\n\n"
        f"User question: {user_query}"
    )
    try:
        llm = _get_llm_respond()
        result = llm.invoke(full_prompt)
        return result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        print(f"  ⚠️  Doctor LLM error: {e}")
        return "Sorry, an error occurred while generating the response. Please try again."


# ── Initialize on import ─────────────────────────────────
print("✅ Egyptian doctor branch ready")
