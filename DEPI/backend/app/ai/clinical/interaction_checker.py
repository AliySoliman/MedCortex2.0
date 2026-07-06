# backend/app/ai/clinical/interaction_checker.py
# ─────────────────────────────────────────────────────────────────────────────
# Drug Interaction Checker
# Evidence-based pairwise drug-drug interaction detection.
# ─────────────────────────────────────────────────────────────────────────────

from itertools import combinations
from typing import Dict, FrozenSet, List, Optional
from pydantic import BaseModel


class InteractionResult(BaseModel):
    """Result of a drug-drug interaction check."""
    drug_a: str
    drug_b: str
    severity: str  # 'major' | 'moderate' | 'minor'
    description: str
    recommendation: str


# Key: frozenset of two lowercase generic names
# Value: {severity, description, recommendation}
KNOWN_INTERACTIONS: Dict[FrozenSet, Dict] = {
    frozenset({"warfarin", "aspirin"}): {
        "severity": "major",
        "description": "Concurrent use significantly increases bleeding risk by inhibiting platelet function and displacing warfarin from plasma proteins.",
        "recommendation": "Avoid combination. If necessary, monitor INR closely and use lowest effective aspirin dose.",
    },
    frozenset({"warfarin", "ibuprofen"}): {
        "severity": "major",
        "description": "NSAIDs inhibit platelet aggregation and may displace warfarin, increasing anticoagulant effect and GI bleeding risk.",
        "recommendation": "Avoid. Use acetaminophen for analgesia. Monitor INR if unavoidable.",
    },
    frozenset({"warfarin", "naproxen"}): {
        "severity": "major",
        "description": "Similar to warfarin+ibuprofen — NSAID potentiates anticoagulation and GI bleeding.",
        "recommendation": "Avoid combination. Prefer acetaminophen.",
    },
    frozenset({"sertraline", "tramadol"}): {
        "severity": "major",
        "description": "High risk of serotonin syndrome due to combined serotonergic activity.",
        "recommendation": "Avoid. If opioid required, use a non-serotonergic agent.",
    },
    frozenset({"fluoxetine", "tramadol"}): {
        "severity": "major",
        "description": "Risk of serotonin syndrome and seizures. Fluoxetine inhibits CYP2D6, increasing tramadol toxicity.",
        "recommendation": "Contraindicated. Select an alternative analgesic.",
    },
    frozenset({"metformin", "ibuprofen"}): {
        "severity": "moderate",
        "description": "NSAIDs may impair renal function and increase metformin accumulation risk (lactic acidosis).",
        "recommendation": "Monitor renal function. Limit NSAID use in diabetic patients.",
    },
    frozenset({"atorvastatin", "clarithromycin"}): {
        "severity": "major",
        "description": "Clarithromycin inhibits CYP3A4, markedly increasing atorvastatin plasma levels and myopathy risk.",
        "recommendation": "Temporarily discontinue atorvastatin during clarithromycin therapy.",
    },
    frozenset({"simvastatin", "amiodarone"}): {
        "severity": "major",
        "description": "Amiodarone inhibits CYP3A4, increasing simvastatin exposure and risk of rhabdomyolysis.",
        "recommendation": "Use alternative statin (rosuvastatin/pravastatin) or reduce simvastatin dose.",
    },
    frozenset({"lisinopril", "potassium"}): {
        "severity": "moderate",
        "description": "ACE inhibitors reduce potassium excretion; concurrent potassium supplementation may cause hyperkalemia.",
        "recommendation": "Monitor serum potassium levels regularly.",
    },
    frozenset({"metoprolol", "verapamil"}): {
        "severity": "major",
        "description": "Combined use of beta-blocker and non-dihydropyridine calcium channel blocker can cause severe bradycardia and AV block.",
        "recommendation": "Avoid combination. If needed, monitor heart rate and ECG closely.",
    },
    frozenset({"clopidogrel", "omeprazole"}): {
        "severity": "moderate",
        "description": "Omeprazole inhibits CYP2C19, reducing clopidogrel activation and antiplatelet effect.",
        "recommendation": "Prefer pantoprazole if PPI required with clopidogrel.",
    },
    frozenset({"ciprofloxacin", "warfarin"}): {
        "severity": "major",
        "description": "Fluoroquinolones inhibit warfarin metabolism via CYP1A2, significantly increasing INR.",
        "recommendation": "Monitor INR closely during and 2 weeks after fluoroquinolone course.",
    },
    frozenset({"lithium", "ibuprofen"}): {
        "severity": "major",
        "description": "NSAIDs reduce renal lithium clearance, causing lithium toxicity.",
        "recommendation": "Avoid NSAIDs in patients on lithium. Monitor lithium levels.",
    },
    frozenset({"metformin", "alcohol"}): {
        "severity": "moderate",
        "description": "Alcohol potentiates lactic acidosis risk with metformin, especially in binge drinking.",
        "recommendation": "Advise against heavy alcohol use in patients on metformin.",
    },
    frozenset({"fluoxetine", "maoi"}): {
        "severity": "major",
        "description": "Combination of SSRIs and MAOIs causes potentially fatal serotonin syndrome.",
        "recommendation": "Contraindicated. Allow 14-day washout after stopping MAOI before starting SSRI.",
    },
    frozenset({"sertraline", "maoi"}): {
        "severity": "major",
        "description": "Risk of life-threatening serotonin syndrome.",
        "recommendation": "Contraindicated. Require washout period.",
    },
    frozenset({"apixaban", "aspirin"}): {
        "severity": "moderate",
        "description": "Increased bleeding risk with dual antithrombotic therapy.",
        "recommendation": "Use only when clearly indicated (e.g., recent ACS). Monitor for bleeding.",
    },
    frozenset({"amlodipine", "simvastatin"}): {
        "severity": "moderate",
        "description": "Amlodipine inhibits CYP3A4, increasing simvastatin levels and myopathy risk.",
        "recommendation": "Limit simvastatin dose to 20mg/day when used with amlodipine.",
    },
    frozenset({"levothyroxine", "calcium"}): {
        "severity": "moderate",
        "description": "Calcium supplements impair levothyroxine absorption when taken simultaneously.",
        "recommendation": "Separate administration by at least 4 hours.",
    },
    frozenset({"gabapentin", "opioid"}): {
        "severity": "major",
        "description": "Combined CNS depression potentiates respiratory depression risk.",
        "recommendation": "Use lowest effective doses. Monitor respiratory status closely.",
    },
}


class InteractionChecker:
    """
    Checks pairwise drug-drug interactions against a curated evidence database.
    Normalizes drug names to lowercase before lookup.
    """

    def check(self, medications: List[str]) -> List[InteractionResult]:
        """
        Check all pairwise combinations of the provided medication list.

        Args:
            medications: List of medication names (brand or generic).

        Returns:
            List of InteractionResult objects for found interactions.
        """
        results: List[InteractionResult] = []
        normalized = [m.lower().strip() for m in medications if m]

        for drug_a, drug_b in combinations(normalized, 2):
            key = frozenset({drug_a, drug_b})
            # Direct match
            if key in KNOWN_INTERACTIONS:
                data = KNOWN_INTERACTIONS[key]
                results.append(InteractionResult(
                    drug_a=drug_a, drug_b=drug_b, **data
                ))
                continue
            # Partial match (drug name contains known key component)
            for known_key, data in KNOWN_INTERACTIONS.items():
                known_list = list(known_key)
                if (any(known_list[0] in drug_a or known_list[0] in drug_b for _ in [1]) and
                        any(known_list[1] in drug_a or known_list[1] in drug_b for _ in [1])):
                    results.append(InteractionResult(
                        drug_a=drug_a, drug_b=drug_b, **data
                    ))
                    break

        return results
