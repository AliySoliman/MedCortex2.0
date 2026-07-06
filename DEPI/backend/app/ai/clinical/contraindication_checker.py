# backend/app/ai/clinical/contraindication_checker.py
# ─────────────────────────────────────────────────────────────────────────────
# Contraindication Checker
# Checks drug-condition contraindications from an evidence-based lookup.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, List
from pydantic import BaseModel


class ContraindicationResult(BaseModel):
    """Represents a drug-condition contraindication finding."""
    drug: str
    condition: str
    severity: str  # 'absolute' | 'relative'
    description: str


# drug (lowercase) -> list of {condition, severity, description}
CONTRAINDICATIONS: Dict[str, List[Dict]] = {
    "metformin": [
        {
            "condition": "renal failure",
            "severity": "absolute",
            "description": "Metformin is contraindicated in severe renal impairment (eGFR <30) due to risk of lactic acidosis.",
        },
        {
            "condition": "hepatic failure",
            "severity": "absolute",
            "description": "Liver disease impairs lactate metabolism, increasing lactic acidosis risk with metformin.",
        },
    ],
    "aspirin": [
        {
            "condition": "peptic ulcer",
            "severity": "relative",
            "description": "Aspirin inhibits prostaglandins, exacerbating gastric mucosal injury in peptic ulcer disease.",
        },
        {
            "condition": "bleeding disorder",
            "severity": "absolute",
            "description": "Aspirin irreversibly inhibits platelet aggregation, worsening bleeding disorders.",
        },
        {
            "condition": "children with viral illness",
            "severity": "absolute",
            "description": "Risk of Reye's syndrome in children with viral infections.",
        },
    ],
    "ibuprofen": [
        {
            "condition": "renal failure",
            "severity": "absolute",
            "description": "NSAIDs reduce renal prostaglandin synthesis, worsening renal function.",
        },
        {
            "condition": "heart failure",
            "severity": "absolute",
            "description": "NSAIDs cause sodium retention and may worsen heart failure decompensation.",
        },
        {
            "condition": "peptic ulcer",
            "severity": "relative",
            "description": "NSAIDs increase gastric acid secretion and inhibit mucosal protection.",
        },
    ],
    "warfarin": [
        {
            "condition": "pregnancy",
            "severity": "absolute",
            "description": "Warfarin is teratogenic and causes fetal warfarin syndrome. Use heparin instead.",
        },
        {
            "condition": "active bleeding",
            "severity": "absolute",
            "description": "Anticoagulation is contraindicated in active uncontrolled bleeding.",
        },
    ],
    "lisinopril": [
        {
            "condition": "pregnancy",
            "severity": "absolute",
            "description": "ACE inhibitors cause fetal renal dysgenesis and are contraindicated in pregnancy.",
        },
        {
            "condition": "angioedema",
            "severity": "absolute",
            "description": "Prior ACE inhibitor-induced angioedema is an absolute contraindication.",
        },
        {
            "condition": "bilateral renal artery stenosis",
            "severity": "absolute",
            "description": "ACE inhibitors can precipitate acute renal failure in bilateral RAS.",
        },
    ],
    "metoprolol": [
        {
            "condition": "severe asthma",
            "severity": "absolute",
            "description": "Non-selective beta-blockade can precipitate severe bronchospasm.",
        },
        {
            "condition": "cardiogenic shock",
            "severity": "absolute",
            "description": "Beta-blockers reduce cardiac output and are contraindicated in cardiogenic shock.",
        },
        {
            "condition": "second degree av block",
            "severity": "absolute",
            "description": "Beta-blockers worsen AV conduction and are contraindicated in second/third degree AV block.",
        },
    ],
    "atorvastatin": [
        {
            "condition": "active liver disease",
            "severity": "absolute",
            "description": "Statins are hepatotoxic and contraindicated in active liver disease or unexplained elevated transaminases.",
        },
        {
            "condition": "pregnancy",
            "severity": "absolute",
            "description": "Statins are teratogenic. Contraindicated in pregnancy and nursing.",
        },
        {
            "condition": "myopathy",
            "severity": "relative",
            "description": "History of statin-induced myopathy requires caution and CK monitoring.",
        },
    ],
    "ciprofloxacin": [
        {
            "condition": "tendon disorder",
            "severity": "relative",
            "description": "Fluoroquinolones increase risk of tendinitis and tendon rupture, especially in elderly.",
        },
        {
            "condition": "epilepsy",
            "severity": "relative",
            "description": "Fluoroquinolones lower seizure threshold and should be used with caution in epilepsy.",
        },
    ],
    "prednisone": [
        {
            "condition": "systemic fungal infection",
            "severity": "absolute",
            "description": "Corticosteroids suppress immune response, worsening systemic fungal infections.",
        },
        {
            "condition": "osteoporosis",
            "severity": "relative",
            "description": "Long-term corticosteroid use accelerates bone loss. Requires calcium, Vitamin D, and bisphosphonate prophylaxis.",
        },
        {
            "condition": "diabetes",
            "severity": "relative",
            "description": "Corticosteroids cause hyperglycemia and worsen glycemic control in diabetics.",
        },
    ],
    "sertraline": [
        {
            "condition": "maoi use",
            "severity": "absolute",
            "description": "Combining SSRIs with MAOIs causes potentially fatal serotonin syndrome.",
        },
        {
            "condition": "bipolar disorder",
            "severity": "relative",
            "description": "SSRIs may trigger manic episodes in bipolar disorder without mood stabilizer cover.",
        },
    ],
    "amoxicillin": [
        {
            "condition": "penicillin allergy",
            "severity": "absolute",
            "description": "Amoxicillin is a penicillin antibiotic. Anaphylaxis risk in penicillin-allergic patients.",
        },
        {
            "condition": "mononucleosis",
            "severity": "relative",
            "description": "Amoxicillin causes widespread maculopapular rash in Epstein-Barr virus/mononucleosis.",
        },
    ],
    "levothyroxine": [
        {
            "condition": "uncorrected adrenal insufficiency",
            "severity": "absolute",
            "description": "Initiating thyroid hormone without treating adrenal insufficiency can precipitate adrenal crisis.",
        },
        {
            "condition": "thyrotoxicosis",
            "severity": "absolute",
            "description": "Levothyroxine is contraindicated in active thyrotoxicosis.",
        },
    ],
    "furosemide": [
        {
            "condition": "anuria",
            "severity": "absolute",
            "description": "Loop diuretics are contraindicated in anuria as they require tubular secretion to work.",
        },
        {
            "condition": "severe hypokalemia",
            "severity": "relative",
            "description": "Furosemide causes further potassium loss and may worsen hypokalemia.",
        },
    ],
    "digoxin": [
        {
            "condition": "ventricular fibrillation",
            "severity": "absolute",
            "description": "Digoxin is contraindicated in ventricular fibrillation.",
        },
        {
            "condition": "hypokalemia",
            "severity": "relative",
            "description": "Hypokalemia increases myocardial sensitivity to digoxin toxicity.",
        },
        {
            "condition": "renal failure",
            "severity": "relative",
            "description": "Digoxin is renally cleared; dose adjustment required in renal impairment.",
        },
    ],
}


class ContraindicationChecker:
    """
    Checks drug-condition contraindications using an evidence-based lookup.
    All lookups are case-insensitive.
    """

    def check(self, medications: List[str], conditions: List[str]) -> List[ContraindicationResult]:
        """
        Identify contraindications for a list of medications given a list of conditions.

        Args:
            medications: Patient's current medications.
            conditions: Patient's active medical conditions.

        Returns:
            List of ContraindicationResult for each identified contraindication.
        """
        results: List[ContraindicationResult] = []
        norm_conditions = [c.lower().strip() for c in conditions if c]

        for medication in medications:
            drug_lower = medication.lower().strip()
            # Look for exact or partial key match
            matched_key: str | None = None
            for key in CONTRAINDICATIONS:
                if key in drug_lower or drug_lower in key:
                    matched_key = key
                    break

            if not matched_key:
                continue

            for entry in CONTRAINDICATIONS[matched_key]:
                entry_condition = entry["condition"].lower()
                for patient_condition in norm_conditions:
                    if entry_condition in patient_condition or patient_condition in entry_condition:
                        results.append(ContraindicationResult(
                            drug=medication,
                            condition=entry["condition"],
                            severity=entry["severity"],
                            description=entry["description"],
                        ))
                        break

        return results
