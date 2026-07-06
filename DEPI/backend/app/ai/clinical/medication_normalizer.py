# backend/app/ai/clinical/medication_normalizer.py
# ─────────────────────────────────────────────────────────────────────────────
# Medication Normalizer
# Maps brand names to generic equivalents and normalizes abbreviations.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict

BRAND_TO_GENERIC: Dict[str, str] = {
    "tylenol": "acetaminophen", "panadol": "acetaminophen", "paracetamol": "acetaminophen",
    "advil": "ibuprofen", "motrin": "ibuprofen", "nurofen": "ibuprofen",
    "aleve": "naproxen", "naprosyn": "naproxen",
    "celebrex": "celecoxib", "voltaren": "diclofenac",
    "bayer": "aspirin", "ecotrin": "aspirin",
    "lipitor": "atorvastatin", "crestor": "rosuvastatin",
    "zocor": "simvastatin", "pravachol": "pravastatin",
    "zestril": "lisinopril", "prinivil": "lisinopril",
    "vasotec": "enalapril", "altace": "ramipril",
    "norvasc": "amlodipine", "cardizem": "diltiazem",
    "lopressor": "metoprolol", "toprol": "metoprolol",
    "tenormin": "atenolol", "coreg": "carvedilol",
    "cozaar": "losartan", "diovan": "valsartan", "avapro": "irbesartan",
    "glucophage": "metformin", "glumetza": "metformin",
    "januvia": "sitagliptin", "jardiance": "empagliflozin",
    "ozempic": "semaglutide", "victoza": "liraglutide",
    "lantus": "insulin glargine", "humalog": "insulin lispro",
    "zoloft": "sertraline", "prozac": "fluoxetine",
    "lexapro": "escitalopram", "celexa": "citalopram",
    "effexor": "venlafaxine", "cymbalta": "duloxetine",
    "xanax": "alprazolam", "klonopin": "clonazepam",
    "valium": "diazepam", "ativan": "lorazepam",
    "ventolin": "albuterol", "proventil": "albuterol",
    "advair": "fluticasone/salmeterol", "symbicort": "budesonide/formoterol",
    "spiriva": "tiotropium", "singulair": "montelukast",
    "prilosec": "omeprazole", "nexium": "esomeprazole",
    "prevacid": "lansoprazole", "protonix": "pantoprazole",
    "pepcid": "famotidine",
    "augmentin": "amoxicillin/clavulanate", "zithromax": "azithromycin",
    "cipro": "ciprofloxacin", "levaquin": "levofloxacin",
    "synthroid": "levothyroxine",
    "coumadin": "warfarin", "eliquis": "apixaban",
    "xarelto": "rivaroxaban", "pradaxa": "dabigatran",
    "deltasone": "prednisone", "medrol": "methylprednisolone",
    "ambien": "zolpidem", "lunesta": "eszopiclone",
    "seroquel": "quetiapine", "abilify": "aripiprazole",
    "neurontin": "gabapentin", "lyrica": "pregabalin",
    "plavix": "clopidogrel", "plaquenil": "hydroxychloroquine",
}

FREQUENCY_MAP: Dict[str, str] = {
    "qd": "once daily", "q.d.": "once daily", "od": "once daily",
    "bid": "twice daily", "b.i.d.": "twice daily", "bd": "twice daily",
    "tid": "three times daily", "t.i.d.": "three times daily",
    "qid": "four times daily", "q.i.d.": "four times daily",
    "prn": "as needed", "p.r.n.": "as needed",
    "qhs": "at bedtime", "q.h.s.": "at bedtime", "hs": "at bedtime",
    "q4h": "every 4 hours", "q6h": "every 6 hours",
    "q8h": "every 8 hours", "q12h": "every 12 hours",
}

ROUTE_MAP: Dict[str, str] = {
    "po": "oral", "p.o.": "oral",
    "iv": "intravenous", "i.v.": "intravenous",
    "im": "intramuscular", "i.m.": "intramuscular",
    "sc": "subcutaneous", "sq": "subcutaneous", "s.c.": "subcutaneous",
    "sl": "sublingual", "s.l.": "sublingual",
    "pr": "rectal", "p.r.": "rectal",
    "top": "topical", "inh": "inhaled", "td": "transdermal",
}


class MedicationNormalizer:
    """Normalizes medication names, frequencies, and routes."""

    def normalize(self, name: str) -> str:
        """Map brand name to generic equivalent, if known."""
        if not name:
            return name
        return BRAND_TO_GENERIC.get(name.lower().strip(), name)

    def normalize_frequency(self, freq_str: str) -> str:
        """Map frequency abbreviations to plain English."""
        if not freq_str:
            return freq_str
        return FREQUENCY_MAP.get(freq_str.lower().strip(), freq_str)

    def normalize_route(self, route_str: str) -> str:
        """Map route abbreviations to plain English."""
        if not route_str:
            return route_str
        return ROUTE_MAP.get(route_str.lower().strip(), route_str)
