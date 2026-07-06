# backend/app/ai/clinical/recommendation_engine.py
# ─────────────────────────────────────────────────────────────────────────────
# Recommendation Engine
# Generates clinical recommendations based on risk level and diagnoses.
# ─────────────────────────────────────────────────────────────────────────────

from typing import List
from pydantic import BaseModel


class ClinicalRecommendation(BaseModel):
    type: str  # 'lifestyle' | 'follow_up' | 'referral' | 'urgent'
    description: str
    priority: int  # 1 = highest


# Condition keyword -> recommendation mapping
_CONDITION_RECOMMENDATIONS = {
    "diabetes": [
        ("lifestyle", "Monitor blood glucose daily and maintain a low-glycemic diet.", 2),
        ("follow_up", "Schedule HbA1c test every 3 months.", 2),
        ("referral", "Consult an endocrinologist for optimized diabetes management.", 3),
    ],
    "hypertension": [
        ("lifestyle", "Adopt a low-sodium diet (DASH diet) and engage in 30 minutes of aerobic exercise daily.", 2),
        ("lifestyle", "Limit alcohol consumption and avoid smoking.", 2),
        ("follow_up", "Monitor blood pressure daily and schedule cardiology follow-up.", 2),
    ],
    "heart failure": [
        ("referral", "Cardiology follow-up within 1 week.", 1),
        ("lifestyle", "Restrict daily fluid and sodium intake. Weigh daily.", 1),
        ("follow_up", "Echocardiogram and BNP level assessment recommended.", 1),
    ],
    "asthma": [
        ("lifestyle", "Identify and avoid known triggers (allergens, smoke, cold air).", 2),
        ("follow_up", "Peak flow monitoring and scheduled pulmonologist review.", 2),
    ],
    "copd": [
        ("lifestyle", "Smoking cessation is the single most effective intervention.", 1),
        ("referral", "Refer to pulmonologist for spirometry and treatment optimization.", 2),
    ],
    "hypothyroidism": [
        ("follow_up", "TSH recheck 6-8 weeks after medication adjustment.", 2),
        ("lifestyle", "Take levothyroxine on an empty stomach, 30-60 minutes before meals.", 2),
    ],
    "gerd": [
        ("lifestyle", "Elevate head of bed, avoid large meals before bedtime, and limit caffeine.", 3),
        ("follow_up", "Consider upper endoscopy if symptoms persist despite PPI therapy.", 3),
    ],
    "osteoporosis": [
        ("lifestyle", "Weight-bearing exercise and adequate calcium (1200mg/day) and Vitamin D intake.", 2),
        ("follow_up", "DEXA scan for bone density assessment.", 2),
    ],
    "depression": [
        ("referral", "Referral to psychiatry or clinical psychology for evaluation.", 1),
        ("follow_up", "PHQ-9 reassessment in 4 weeks.", 2),
    ],
    "anxiety": [
        ("referral", "Consider CBT (cognitive behavioral therapy) or psychiatric evaluation.", 2),
        ("lifestyle", "Regular aerobic exercise, mindfulness, and sleep hygiene.", 3),
    ],
    "anemia": [
        ("follow_up", "CBC recheck in 4-6 weeks. Evaluate iron studies, B12, and folate.", 2),
        ("lifestyle", "Iron-rich diet: lean meat, legumes, fortified cereals.", 3),
    ],
    "urinary tract infection": [
        ("follow_up", "Urine culture and sensitivities. Repeat urinalysis post-treatment.", 2),
        ("lifestyle", "Increase fluid intake. Void after sexual intercourse.", 3),
    ],
}

_UNIVERSAL_RECOMMENDATIONS = [
    ("lifestyle", "Maintain adequate hydration (6-8 glasses of water daily).", 4),
    ("lifestyle", "Prioritize 7-8 hours of quality sleep nightly.", 4),
    ("follow_up", "Schedule a routine primary care follow-up within 4-6 weeks.", 5),
]


class RecommendationEngine:
    """
    Generates prioritized clinical recommendations based on risk and diagnoses.
    Uses a deterministic rule-based approach.
    """

    def generate(
        self,
        risk_level: str,
        diagnoses: List[str],
        findings: List[str],
    ) -> List[ClinicalRecommendation]:
        """
        Generate recommendations appropriate for the given risk level and diagnoses.

        Args:
            risk_level: One of 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'.
            diagnoses: List of suspected or confirmed diagnosis strings.
            findings: Extracted symptoms or clinical findings.

        Returns:
            Sorted list of ClinicalRecommendation objects (priority 1 = most urgent).
        """
        results: List[ClinicalRecommendation] = []
        seen: set = set()

        # Urgent recommendation for critical risk
        if risk_level in ("CRITICAL", "HIGH"):
            rec = ClinicalRecommendation(
                type="urgent",
                description=(
                    "Seek immediate medical attention. Call emergency services (911) "
                    "if symptoms are severe or rapidly worsening."
                ),
                priority=1,
            )
            if rec.description not in seen:
                results.append(rec)
                seen.add(rec.description)

        # Condition-specific recommendations
        for diagnosis in diagnoses:
            dx_lower = diagnosis.lower()
            for condition_key, recs in _CONDITION_RECOMMENDATIONS.items():
                if condition_key in dx_lower:
                    for rtype, desc, priority in recs:
                        if desc not in seen:
                            results.append(ClinicalRecommendation(
                                type=rtype, description=desc, priority=priority
                            ))
                            seen.add(desc)

        # Universal recommendations for low/moderate risk
        if risk_level in ("LOW", "MODERATE"):
            for rtype, desc, priority in _UNIVERSAL_RECOMMENDATIONS:
                if desc not in seen:
                    results.append(ClinicalRecommendation(
                        type=rtype, description=desc, priority=priority
                    ))
                    seen.add(desc)

        results.sort(key=lambda r: r.priority)
        return results
