# backend/app/ai/clinical/doctor_finder.py
# ─────────────────────────────────────────────────────────────────────────────
# MedCortex Doctor Finder
# Uses a hybrid doctor finder:
# 1. Google Places (Egypt clinics / doctors) when GOOGLE_PLACES_API_KEY is configured
# 2. FREE NPPES NPI Registry API for the existing foreign-doctor recommendations
# https://npiregistry.cms.hhs.gov/api/
# ─────────────────────────────────────────────────────────────────────────────

import os
import httpx
from typing import List, Dict, Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Provider API CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber"
)
DOCTOR_LOOKUP_DEFAULT_CITY = os.getenv("DOCTOR_LOOKUP_DEFAULT_CITY", "Alexandria")
DOCTOR_LOOKUP_COUNTRY = os.getenv("DOCTOR_LOOKUP_COUNTRY", "Egypt")

NPPES_BASE_URL = "https://npiregistry.cms.hhs.gov/api/"
NPPES_VERSION  = "2.1"
RESULTS_PER_SPECIALTY = 3   # doctors returned per specialty
REQUEST_TIMEOUT       = 8   # seconds


# ─────────────────────────────────────────────────────────────────────────────
# SPECIALTY → NPPES TAXONOMY MAPPING
# Maps our LLM-friendly names → NPPES taxonomy descriptions
# ─────────────────────────────────────────────────────────────────────────────
SPECIALTY_TAXONOMY_MAP: Dict[str, str] = {
    "General Practitioner":           "General Practice",
    "Family Medicine":                "Family Medicine",
    "Internal Medicine":              "Internal Medicine",
    "Pediatrician":                   "Pediatrics",
    "Cardiologist":                   "Cardiovascular Disease",
    "Pulmonologist":                  "Pulmonary Disease",
    "Neurologist":                    "Neurology",
    "Gastroenterologist":             "Gastroenterology",
    "Dermatologist":                  "Dermatology",
    "Endocrinologist":                "Endocrinology",
    "Oncologist":                     "Hematology & Oncology",
    "Orthopedic Surgeon":             "Orthopedic Surgery",
    "Ophthalmologist":                "Ophthalmology",
    "ENT Specialist":                 "Otolaryngology",
    "Urologist":                      "Urology",
    "Rheumatologist":                 "Rheumatology",
    "Infectious Disease Specialist":  "Infectious Disease",
    "Psychiatrist":                   "Psychiatry",
    "Nephrologist":                   "Nephrology",
    "Obstetrician":                   "Obstetrics & Gynecology",
    "Gynecologist":                   "Obstetrics & Gynecology",
    "Allergist":                      "Allergy & Immunology",
    "Hematologist":                   "Hematology",
    "Radiologist":                    "Diagnostic Radiology",
    "Emergency Medicine":             "Emergency Medicine",
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_doctor(result: Dict, specialty_label: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single NPPES result into a clean doctor dict.
    Returns None if essential fields are missing.
    """
    try:
        basic    = result.get("basic", {})
        addrs    = result.get("addresses", [])
        taxons   = result.get("taxonomies", [])

        # Name
        first = basic.get("first_name", "")
        last  = basic.get("last_name",  "")
        org   = basic.get("organization_name", "")
        name  = f"Dr. {first} {last}".strip() if first or last else org
        if not name or name == "Dr. ":
            return None

        # Address — prefer location address (address_purpose = LOCATION)
        address_str = ""
        phone       = ""
        for addr in addrs:
            if addr.get("address_purpose") in ("LOCATION", "MAILING"):
                line1 = addr.get("address_1", "")
                city  = addr.get("city", "")
                state = addr.get("state", "")
                zip_  = addr.get("postal_code", "")[:5]
                address_str = f"{line1}, {city}, {state} {zip_}".strip(", ")
                phone = addr.get("telephone_number", "")
                break

        # Taxonomy / actual specialty
        actual_specialty = specialty_label
        for t in taxons:
            if t.get("primary"):
                actual_specialty = t.get("desc", specialty_label)
                break

        npi = result.get("number", "")

        return {
            "name":     name,
            "specialty": actual_specialty,
            "address":  address_str or "Address not available",
            "phone":    phone        or "Phone not available",
            "npi":      npi,
            "source":   "NPPES NPI Registry",
        }
    except Exception:
        return None


def _fetch_doctors_for_specialty(
    specialty_label: str,
    limit: int = RESULTS_PER_SPECIALTY,
) -> List[Dict[str, Any]]:
    """
    Query NPPES for individual practitioners matching a taxonomy.
    Falls back to the raw specialty_label if not in our map.
    """
    taxonomy = SPECIALTY_TAXONOMY_MAP.get(specialty_label, specialty_label)

    params = {
        "version":           NPPES_VERSION,
        "enumeration_type":  "NPI-1",          # individual providers only
        "taxonomy_description": taxonomy,
        "limit":             limit,
        "skip":              0,
    }

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            resp = client.get(NPPES_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[doctor_model] NPPES request failed for '{taxonomy}': {e}")
        return []

    doctors = []
    for result in data.get("results", []):
        doc = _parse_doctor(result, specialty_label)
        if doc:
            doctors.append(doc)
        if len(doctors) >= limit:
            break

    return doctors


def _parse_egypt_place(place: Dict[str, Any], specialty_label: str) -> Optional[Dict[str, Any]]:
    display_name = (place.get("displayName") or {}).get("text", "").strip()
    if not display_name:
        return None

    return {
        "name": display_name,
        "specialty": specialty_label,
        "address": place.get("formattedAddress") or "Egypt address not available",
        "phone": place.get("nationalPhoneNumber") or "Phone not available",
        "npi": place.get("id", ""),
        "source": "Google Places (Egypt clinic / doctor)",
    }


def _fetch_egypt_doctors_for_specialty(
    specialty_label: str,
    limit: int = RESULTS_PER_SPECIALTY,
) -> List[Dict[str, Any]]:
    if not GOOGLE_PLACES_API_KEY:
        return []

    queries = [
        f"{specialty_label} doctor in {DOCTOR_LOOKUP_DEFAULT_CITY}, {DOCTOR_LOOKUP_COUNTRY}",
        f"{specialty_label} clinic in {DOCTOR_LOOKUP_COUNTRY}",
    ]

    results: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        for query in queries:
            try:
                response = client.post(
                    GOOGLE_PLACES_TEXT_SEARCH_URL,
                    headers={
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
                        "X-Goog-FieldMask": GOOGLE_PLACES_FIELD_MASK,
                    },
                    json={
                        "textQuery": query,
                        "languageCode": "en",
                        "regionCode": "EG",
                        "pageSize": limit,
                    },
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                print(f"[doctor_model] Egypt lookup failed for '{query}': {exc}")
                continue

            for place in payload.get("places", []):
                parsed = _parse_egypt_place(place, specialty_label)
                if not parsed:
                    continue
                place_id = parsed.get("npi", "")
                if place_id and place_id in seen_ids:
                    continue
                if place_id:
                    seen_ids.add(place_id)
                results.append(parsed)
                if len(results) >= limit:
                    return results

    return results


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def find_doctors(
    specialties: List[str],
    max_per_specialty: int = RESULTS_PER_SPECIALTY,
) -> List[Dict[str, Any]]:
    """
    Given a list of medical specialties, query NPPES and return doctors.

    Args:
        specialties:        e.g. ["General Practitioner", "Pulmonologist"]
        max_per_specialty:  how many doctors per specialty (default 3)

    Returns:
        Flat list of doctor dicts:
        [
          {
            "name":      "Dr. Jane Smith",
            "specialty": "General Practice",
            "address":   "123 Main St, New York, NY 10001",
            "phone":     "212-555-0100",
            "npi":       "1234567890",
            "source":    "NPPES NPI Registry"
          },
          ...
        ]
    """
    if not specialties:
        return []

    all_doctors: List[Dict[str, Any]] = []
    seen_refs:   set[str] = set()

    for specialty in specialties:
        egypt_docs = _fetch_egypt_doctors_for_specialty(specialty, max_per_specialty)
        foreign_docs = _fetch_doctors_for_specialty(specialty, max_per_specialty)

        for doc in [*egypt_docs, *foreign_docs]:
            ref = doc.get("npi", "") or f"{doc.get('name', '')}:{doc.get('source', '')}"
            if ref in seen_refs:
                continue
            seen_refs.add(ref)
            all_doctors.append(doc)

    return all_doctors
