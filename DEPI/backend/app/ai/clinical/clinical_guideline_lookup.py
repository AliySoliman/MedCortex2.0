# backend/app/ai/clinical/clinical_guideline_lookup.py
# ─────────────────────────────────────────────────────────────────────────────
# Clinical Guideline Lookup
# Evidence-based clinical guideline summaries for common conditions.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, List, Optional
from pydantic import BaseModel


class ClinicalGuideline(BaseModel):
    condition: str
    guideline: str
    source: str
    key_recommendations: List[str]


GUIDELINES: Dict[str, ClinicalGuideline] = {
    "hypertension": ClinicalGuideline(
        condition="Hypertension",
        guideline="JNC 8 / ACC/AHA 2017 Hypertension Guideline",
        source="American College of Cardiology / American Heart Association",
        key_recommendations=[
            "Target BP <130/80 mmHg for most adults (ACC/AHA 2017).",
            "Lifestyle modification: DASH diet, sodium restriction (<2.3g/day), weight loss, aerobic exercise.",
            "First-line pharmacotherapy: thiazide diuretics, ACE inhibitors, ARBs, or CCBs.",
            "Avoid ACE inhibitors + ARBs in combination.",
            "Monitor renal function and electrolytes with ACE inhibitors/ARBs.",
        ],
    ),
    "type2_diabetes": ClinicalGuideline(
        condition="Type 2 Diabetes Mellitus",
        guideline="ADA Standards of Medical Care in Diabetes 2024",
        source="American Diabetes Association",
        key_recommendations=[
            "HbA1c target <7% for most adults; individualize based on patient factors.",
            "First-line therapy: Metformin (if no contraindications).",
            "Consider GLP-1 agonist or SGLT-2 inhibitor for patients with established CVD or high CV risk.",
            "Monitor renal function before and during metformin therapy.",
            "Annual screening for diabetic nephropathy, retinopathy, neuropathy, and foot care.",
            "Lifestyle: Mediterranean or low-carbohydrate diet; 150 min/week moderate aerobic activity.",
        ],
    ),
    "asthma": ClinicalGuideline(
        condition="Asthma",
        guideline="GINA 2023 Global Strategy for Asthma Management",
        source="Global Initiative for Asthma (GINA)",
        key_recommendations=[
            "Short-acting beta-agonist (SABA) for acute relief; use as-needed.",
            "ICS (inhaled corticosteroid) is the cornerstone of maintenance therapy.",
            "Step up therapy if asthma is uncontrolled: ICS + LABA.",
            "Avoid known triggers: allergens, smoke, NSAIDs if NSAID-sensitive.",
            "Annual influenza vaccination recommended.",
            "Action plan: patient should have a written asthma action plan.",
        ],
    ),
    "copd": ClinicalGuideline(
        condition="Chronic Obstructive Pulmonary Disease (COPD)",
        guideline="GOLD 2024 COPD Management Guidelines",
        source="Global Initiative for Chronic Obstructive Lung Disease (GOLD)",
        key_recommendations=[
            "Smoking cessation is the most effective intervention to slow disease progression.",
            "Short-acting bronchodilators (SABA/SAMA) for symptom relief.",
            "Long-acting bronchodilators (LABA/LAMA) as maintenance therapy.",
            "Pulmonary rehabilitation improves exercise tolerance and quality of life.",
            "Annual influenza and pneumococcal vaccination.",
            "Supplemental oxygen if PaO2 <55mmHg or SaO2 <88% at rest.",
        ],
    ),
    "heart_failure": ClinicalGuideline(
        condition="Heart Failure with Reduced Ejection Fraction (HFrEF)",
        guideline="ACC/AHA/HFSA 2022 Heart Failure Guideline",
        source="American College of Cardiology / American Heart Association",
        key_recommendations=[
            "Foundational therapy (GDMT): ACE inhibitor/ARB or ARNI + beta-blocker + MRA + SGLT2i.",
            "Target: EF <40% requires GDMT initiation.",
            "Fluid restriction 1.5-2L/day if fluid retention present.",
            "Daily weight monitoring: report >2kg gain in 2 days to provider.",
            "Avoid NSAIDs, most CCBs (except amlodipine), and thiazolidinediones.",
            "ICD implantation if EF <35% despite optimal medical therapy.",
        ],
    ),
    "atrial_fibrillation": ClinicalGuideline(
        condition="Atrial Fibrillation",
        guideline="ACC/AHA/HRS 2023 Atrial Fibrillation Guideline",
        source="American College of Cardiology",
        key_recommendations=[
            "Assess stroke risk with CHA2DS2-VASc score; anticoagulate if score ≥2 (men) or ≥3 (women).",
            "Prefer DOACs (apixaban, rivaroxaban, dabigatran) over warfarin.",
            "Rate control with beta-blockers or calcium channel blockers (diltiazem/verapamil).",
            "Rhythm control (cardioversion/ablation) for symptomatic patients or new-onset AF.",
            "Treat underlying causes: hypertension, sleep apnea, alcohol use.",
        ],
    ),
    "hypothyroidism": ClinicalGuideline(
        condition="Hypothyroidism",
        guideline="ATA 2014 Guidelines for Treatment of Hypothyroidism",
        source="American Thyroid Association",
        key_recommendations=[
            "First-line treatment: Levothyroxine (T4 replacement).",
            "Target TSH: 0.5-2.5 mIU/L for most patients.",
            "Take levothyroxine on empty stomach, 30-60 min before breakfast.",
            "Recheck TSH 6-8 weeks after initiating or changing dose.",
            "Avoid concurrent calcium, iron, or antacids within 4 hours of levothyroxine.",
        ],
    ),
    "osteoporosis": ClinicalGuideline(
        condition="Osteoporosis",
        guideline="NOF 2023 Clinician's Guide to Osteoporosis",
        source="National Osteoporosis Foundation",
        key_recommendations=[
            "DEXA scan for all women ≥65 and men ≥70, or younger with risk factors.",
            "Calcium 1000-1200mg/day and Vitamin D 800-1000 IU/day.",
            "First-line pharmacotherapy: oral bisphosphonates (alendronate, risedronate).",
            "Fall prevention: exercise, home safety modifications, review medications.",
            "Avoid smoking and excessive alcohol.",
        ],
    ),
    "depression": ClinicalGuideline(
        condition="Major Depressive Disorder",
        guideline="APA 2010 Practice Guideline for MDD",
        source="American Psychiatric Association",
        key_recommendations=[
            "First-line: SSRIs (sertraline, escitalopram) or SNRIs.",
            "Continue antidepressant for minimum 6-12 months after remission.",
            "Psychotherapy (CBT) is as effective as medication for mild-moderate depression.",
            "PHQ-9 for baseline and follow-up monitoring.",
            "Screen for bipolar disorder before prescribing antidepressant monotherapy.",
            "Safety assessment: evaluate suicidality at every visit.",
        ],
    ),
    "anxiety": ClinicalGuideline(
        condition="Generalized Anxiety Disorder",
        guideline="NICE 2019 Anxiety Disorders Guideline",
        source="National Institute for Health and Care Excellence (NICE)",
        key_recommendations=[
            "First-line: Cognitive Behavioral Therapy (CBT).",
            "Pharmacotherapy: SSRIs (sertraline, escitalopram) or SNRIs (venlafaxine).",
            "Avoid long-term benzodiazepine use due to dependence risk.",
            "GAD-7 scale for monitoring.",
            "Lifestyle: regular aerobic exercise, mindfulness, sleep hygiene.",
            "Refer to psychiatry if inadequate response to two medication trials.",
        ],
    ),
}


class GuidelineLookup:
    """
    Looks up evidence-based clinical guidelines by condition name or keywords.
    Case-insensitive matching.
    """

    def lookup(self, condition: str) -> Optional[ClinicalGuideline]:
        """Return a guideline for an exact condition key, or by fuzzy match."""
        key = condition.lower().strip().replace(" ", "_").replace("-", "_")
        if key in GUIDELINES:
            return GUIDELINES[key]
        # Fuzzy search
        for gkey, guideline in GUIDELINES.items():
            if key in gkey or gkey in key or condition.lower() in guideline.condition.lower():
                return guideline
        return None

    def search(self, keywords: List[str]) -> List[ClinicalGuideline]:
        """Return all guidelines whose condition matches any of the provided keywords."""
        results: List[ClinicalGuideline] = []
        seen: set = set()
        for kw in keywords:
            result = self.lookup(kw)
            if result and result.condition not in seen:
                results.append(result)
                seen.add(result.condition)
        return results
