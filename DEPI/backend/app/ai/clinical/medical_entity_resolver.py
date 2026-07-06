# backend/app/ai/clinical/medical_entity_resolver.py
# ─────────────────────────────────────────────────────────────────────────────
# Medical Entity Resolver
# Resolves medical entities to standardized codes (ICD-10, RxNorm, LOINC).
# ─────────────────────────────────────────────────────────────────────────────

from typing import Any, Dict, List, Optional

# ICD-10 diagnosis codes
_ICD10_LOOKUP: Dict[str, str] = {
    "hypertension": "I10", "essential hypertension": "I10",
    "type 2 diabetes": "E11", "diabetes mellitus": "E11", "t2dm": "E11",
    "type 1 diabetes": "E10",
    "asthma": "J45",
    "copd": "J44", "chronic obstructive pulmonary disease": "J44",
    "heart failure": "I50", "congestive heart failure": "I50",
    "atrial fibrillation": "I48",
    "myocardial infarction": "I21", "heart attack": "I21",
    "pneumonia": "J18",
    "urinary tract infection": "N39.0", "uti": "N39.0",
    "hypothyroidism": "E03",
    "hyperthyroidism": "E05",
    "osteoporosis": "M81",
    "rheumatoid arthritis": "M06",
    "osteoarthritis": "M19",
    "gerd": "K21", "gastroesophageal reflux": "K21",
    "peptic ulcer": "K27",
    "migraine": "G43",
    "epilepsy": "G40",
    "depression": "F32", "major depressive disorder": "F32",
    "anxiety": "F41", "generalized anxiety disorder": "F41.1",
    "anemia": "D64",
    "iron deficiency anemia": "D50",
    "pulmonary embolism": "I26",
    "deep vein thrombosis": "I82",
    "stroke": "I63", "ischemic stroke": "I63",
    "sepsis": "A41",
    "appendicitis": "K37",
}

# RxNorm concept IDs (simplified string identifiers)
_RXNORM_LOOKUP: Dict[str, str] = {
    "acetaminophen": "RxCUI:161", "ibuprofen": "RxCUI:5640",
    "aspirin": "RxCUI:1191", "naproxen": "RxCUI:41493",
    "metformin": "RxCUI:6809", "atorvastatin": "RxCUI:83367",
    "lisinopril": "RxCUI:29046", "amlodipine": "RxCUI:17767",
    "metoprolol": "RxCUI:41493", "losartan": "RxCUI:52175",
    "omeprazole": "RxCUI:7646", "levothyroxine": "RxCUI:10582",
    "warfarin": "RxCUI:11289", "apixaban": "RxCUI:1364430",
    "sertraline": "RxCUI:36437", "fluoxetine": "RxCUI:41493",
    "gabapentin": "RxCUI:25480", "pregabalin": "RxCUI:187832",
    "albuterol": "RxCUI:435", "fluticasone": "RxCUI:41253",
    "prednisone": "RxCUI:8640", "amoxicillin": "RxCUI:723",
    "ciprofloxacin": "RxCUI:2551", "azithromycin": "RxCUI:18631",
    "insulin glargine": "RxCUI:274783", "furosemide": "RxCUI:4603",
    "clopidogrel": "RxCUI:32968",
}

# LOINC codes for common lab tests
_LOINC_LOOKUP: Dict[str, str] = {
    "glucose": "2345-7", "fasting glucose": "1558-6",
    "hba1c": "4548-4", "hemoglobin a1c": "4548-4",
    "creatinine": "2160-0", "bun": "3094-0",
    "sodium": "2951-2", "potassium": "2823-3",
    "chloride": "2075-0", "bicarbonate": "1963-8",
    "calcium": "17861-6", "magnesium": "19123-9",
    "wbc": "6690-2", "rbc": "789-8",
    "hemoglobin": "718-7", "hematocrit": "4544-3",
    "platelets": "777-3",
    "tsh": "3016-3", "t4": "3026-2", "free t4": "3024-7",
    "alt": "1742-6", "ast": "1920-8",
    "alp": "6768-6", "total bilirubin": "1975-2",
    "albumin": "1751-7",
    "ldl": "2089-1", "hdl": "2085-9", "triglycerides": "2571-8",
    "inr": "34714-6", "pt": "5902-2",
}


class MedicalEntityResolver:
    """
    Resolves clinical entity names to standardized codes.
    Supports ICD-10 (diagnoses), RxNorm (medications), LOINC (lab tests).
    All lookups are case-insensitive.
    """

    def resolve(self, entity_name: str, entity_type: str) -> Dict[str, Any]:
        """
        Resolve a single entity to its standardized code.

        Args:
            entity_name: Name of the entity (e.g., 'metformin', 'asthma').
            entity_type: One of 'diagnosis', 'medication', 'lab'.

        Returns:
            Dict with: {name, entity_type, code_system, code, resolved}
        """
        key = entity_name.lower().strip()
        code: Optional[str] = None
        code_system: Optional[str] = None

        if entity_type == "diagnosis":
            code = _ICD10_LOOKUP.get(key)
            code_system = "ICD-10-CM"
        elif entity_type == "medication":
            code = _RXNORM_LOOKUP.get(key)
            code_system = "RxNorm"
        elif entity_type == "lab":
            code = _LOINC_LOOKUP.get(key)
            code_system = "LOINC"

        return {
            "name": entity_name,
            "entity_type": entity_type,
            "code_system": code_system,
            "code": code,
            "resolved": code is not None,
        }

    def batch_resolve(self, entities: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Resolve a list of entities.

        Args:
            entities: List of {name, type} dicts.

        Returns:
            List of resolution result dicts.
        """
        return [
            self.resolve(e.get("name", ""), e.get("type", ""))
            for e in entities
        ]
