# backend/app/ai/clinical/drug_parser.py
# ─────────────────────────────────────────────────────────────────────────────
# Drug Parser
# Extracts medication information from raw clinical text using regex patterns.
# No LLM dependency — deterministic and fast.
# ─────────────────────────────────────────────────────────────────────────────

import re
from typing import Any, Dict, List, Optional


_DOSAGE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(mcg|microgram|mg|milligram|g|gram|ml|mL|IU|units?|%)",
    re.IGNORECASE,
)

_FREQUENCY_PATTERNS = [
    (r"\bonce\s+daily\b|\bQD\b|\bq\.?d\.?\b", "once daily"),
    (r"\btwice\s+daily\b|\bBID\b|\bb\.?i\.?d\.?\b", "twice daily"),
    (r"\bthree\s+times\s+daily\b|\bTID\b|\bt\.?i\.?d\.?\b", "three times daily"),
    (r"\bfour\s+times\s+daily\b|\bQID\b|\bq\.?i\.?d\.?\b", "four times daily"),
    (r"\bq(\d+)h\b|\bevery\s+(\d+)\s+hours?\b", "every {n} hours"),
    (r"\bPRN\b|\bp\.?r\.?n\.?\b|\bas\s+needed\b", "as needed"),
    (r"\bQHS\b|\bq\.?h\.?s\.?\b|\bat\s+bedtime\b", "at bedtime"),
    (r"\bweekly\b|\bonce\s+a\s+week\b", "weekly"),
    (r"\bmonthly\b|\bonce\s+a\s+month\b", "monthly"),
]

_ROUTE_PATTERNS = [
    (r"\bPO\b|\bp\.?o\.?\b|\boral(?:ly)?\b|\bby\s+mouth\b", "oral"),
    (r"\bIV\b|\bi\.?v\.?\b|\bintravenous(?:ly)?\b", "intravenous"),
    (r"\bIM\b|\bi\.?m\.?\b|\bintramuscular(?:ly)?\b", "intramuscular"),
    (r"\bSC\b|\bSQ\b|\bs\.?c\.?\b|\bsubcutaneous(?:ly)?\b", "subcutaneous"),
    (r"\bSL\b|\bs\.?l\.?\b|\bsublingual(?:ly)?\b|\bunder\s+tongue\b", "sublingual"),
    (r"\btopical(?:ly)?\b|\bapplied\s+to\s+skin\b", "topical"),
    (r"\binhaled?\b|\bvia\s+inhaler\b|\bnebuliz", "inhaled"),
    (r"\brectal(?:ly)?\b|\bPR\b|\bp\.?r\.?\b", "rectal"),
    (r"\btransdermal(?:ly)?\b|\bpatch\b", "transdermal"),
]

_DRUG_KEYWORDS = [
    "acetaminophen","ibuprofen","aspirin","naproxen","diclofenac",
    "metformin","glipizide","glyburide","sitagliptin","insulin",
    "atorvastatin","rosuvastatin","simvastatin","pravastatin",
    "lisinopril","enalapril","ramipril","captopril",
    "amlodipine","nifedipine","verapamil","diltiazem",
    "metoprolol","atenolol","carvedilol","bisoprolol",
    "losartan","valsartan","irbesartan","olmesartan",
    "omeprazole","pantoprazole","esomeprazole","lansoprazole",
    "hydrochlorothiazide","furosemide","spironolactone",
    "warfarin","apixaban","rivaroxaban","dabigatran","heparin",
    "amoxicillin","azithromycin","ciprofloxacin","doxycycline","cephalexin",
    "prednisone","prednisolone","methylprednisolone","dexamethasone",
    "levothyroxine","methimazole","propylthiouracil",
    "sertraline","fluoxetine","escitalopram","paroxetine","venlafaxine",
    "alprazolam","clonazepam","diazepam","lorazepam",
    "zolpidem","melatonin","quetiapine","risperidone",
    "albuterol","salbutamol","salmeterol","fluticasone","budesonide",
    "methotrexate","hydroxychloroquine","sulfasalazine",
    "gabapentin","pregabalin","carbamazepine","phenytoin","valproate",
    "clopidogrel","digoxin","amiodarone","nitroglycerin",
    "codeine","tramadol","morphine","oxycodone","hydrocodone",
    "ondansetron","metoclopramide","famotidine","ranitidine",
]
_DRUG_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(d) for d in sorted(_DRUG_KEYWORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


class DrugParser:
    """
    Parses raw clinical text to extract medication information.
    Deterministic regex approach — no LLM dependency.
    """

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """Extract medication records from free-form clinical text."""
        if not text or not text.strip():
            return []

        results: List[Dict[str, Any]] = []
        seen: set = set()

        for segment in re.split(r"[.\n;]", text):
            segment = segment.strip()
            if not segment:
                continue
            for drug_name in _DRUG_PATTERN.findall(segment):
                key = drug_name.lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append({
                    "name": drug_name.capitalize(),
                    "dosage": self._extract_dosage(segment),
                    "frequency": self._extract_frequency(segment),
                    "route": self._extract_route(segment),
                    "raw_text": segment[:200],
                })
        return results

    def _extract_dosage(self, text: str) -> Optional[str]:
        m = _DOSAGE_PATTERN.search(text)
        return f"{m.group(1)} {m.group(2)}" if m else None

    def _extract_frequency(self, text: str) -> Optional[str]:
        for pattern, label in _FREQUENCY_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                if "{n}" in label:
                    n = next((g for g in m.groups() if g), "?")
                    return label.replace("{n}", n)
                return label
        return None

    def _extract_route(self, text: str) -> Optional[str]:
        for pattern, label in _ROUTE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None
