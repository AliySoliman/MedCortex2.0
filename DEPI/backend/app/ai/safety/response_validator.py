# backend/app/ai/safety/response_validator.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.ai.safety.guardrails import MedicalGuardrails
from app.ai.safety.hallucination_detector import HallucinationDetector
from app.ai.safety.confidence_calibrator import ConfidenceCalibrator
from app.ai.safety.medical_disclaimer import MedicalDisclaimer, DisclaimerConfig
from app.ai.safety.policy_engine import PolicyEngine


class ValidationResult(BaseModel):
    is_valid: bool
    safety_score: float  # 0.0-1.0
    issues: List[str]
    validated_response: str
    metadata: Dict[str, Any]


class ResponseValidator:
    """
    Main entry point for AI safety validation.
    Chains together all safety checks.
    """

    def __init__(
        self,
        guardrails: MedicalGuardrails,
        hallucination_detector: HallucinationDetector,
        confidence_calibrator: ConfidenceCalibrator,
        disclaimer: MedicalDisclaimer,
        policy_engine: PolicyEngine,
    ):
        self.guardrails = guardrails
        self.hallucination_detector = hallucination_detector
        self.confidence_calibrator = confidence_calibrator
        self.disclaimer = disclaimer
        self.policy_engine = policy_engine

    @classmethod
    def create_default(cls) -> "ResponseValidator":
        """Factory method to create a fully configured ResponseValidator."""
        return cls(
            guardrails=MedicalGuardrails(),
            hallucination_detector=HallucinationDetector(),
            confidence_calibrator=ConfidenceCalibrator(),
            disclaimer=MedicalDisclaimer(),
            policy_engine=PolicyEngine(),
        )

    def validate(
        self,
        response: str,
        query: str,
        source_context: str,
        raw_confidence: float = 0.8,
        evidence_count: int = 1,
        citations: Optional[List[str]] = None,
    ) -> ValidationResult:
        """
        Run the full validation pipeline on an AI response.
        """
        issues: List[str] = []
        is_valid = True
        validated_response = response

        # 1. Guardrails
        gr_result = self.guardrails.check(validated_response, query)
        if not gr_result.passed:
            is_valid = False
            for v in gr_result.violations:
                if v.severity in ("error", "critical"):
                    issues.append(f"Guardrail {v.severity}: {v.message}")
        
        if gr_result.modified_response:
            validated_response = gr_result.modified_response

        # 2. Hallucination Detection
        hall_risk = self.hallucination_detector.detect(validated_response, source_context)
        if hall_risk.risk_level == "high":
            is_valid = False
            issues.append("High hallucination risk detected.")

        # 3. Calibrate Confidence
        cal_conf = self.confidence_calibrator.calibrate(
            raw_confidence=raw_confidence,
            evidence_count=evidence_count,
            hallucination_risk=hall_risk.risk_score
        )

        # 4. Disclaimer Injection
        config = DisclaimerConfig(include_general=True)
        if self.disclaimer.needs_emergency_disclaimer(validated_response):
            config.include_emergency = True
        validated_response = self.disclaimer.inject(validated_response, config)

        # 5. Policy Engine
        policy_decision = self.policy_engine.evaluate(query, validated_response, source_context)
        if not policy_decision.allowed:
            is_valid = False
            issues.append(f"Policy violation: {policy_decision.reason}")

        # Compute final safety score
        safety_score = 1.0 - (hall_risk.risk_score * 0.5)
        if not is_valid:
            safety_score *= 0.5

        metadata = {
            "hallucination_risk": hall_risk.model_dump(),
            "calibrated_confidence": cal_conf.model_dump(),
            "guardrail_violations": [v.model_dump() for v in gr_result.violations],
        }

        return ValidationResult(
            is_valid=is_valid,
            safety_score=round(safety_score, 3),
            issues=issues,
            validated_response=validated_response,
            metadata=metadata,
        )
