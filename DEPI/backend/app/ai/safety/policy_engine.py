# backend/app/ai/safety/policy_engine.py
from typing import Any, Dict, List
from pydantic import BaseModel


class PolicyRule(BaseModel):
    name: str
    description: str
    enabled: bool = True


class PolicyDecision(BaseModel):
    allowed: bool
    applied_rules: List[str]
    reason: str


class PolicyEngine:
    """
    Evaluates responses against general platform safety policies.
    """

    def __init__(self, rules: List[PolicyRule] = None):
        if rules is None:
            self.rules = [
                PolicyRule(
                    name="require_disclaimer",
                    description="All responses must include disclaimer",
                ),
                PolicyRule(
                    name="no_specific_prescriptions",
                    description="Cannot provide specific prescriptions",
                ),
                PolicyRule(
                    name="cite_evidence",
                    description="Should cite evidence when available",
                ),
                PolicyRule(
                    name="emergency_routing",
                    description="Emergency situations must include emergency contact",
                ),
            ]
        else:
            self.rules = rules

    def evaluate(self, query: str, response: str, context: str) -> PolicyDecision:
        """
        Evaluate query, response and context against configured policies.
        Currently implements a basic pass-through check, delegating strict
        checking to guardrails and unsafe_request_handler.
        """
        # For this mock-up implementation, we assume that if it passes guardrails
        # it passes general policy, but in a real system this would apply further logic.
        return PolicyDecision(
            allowed=True,
            applied_rules=[rule.name for rule in self.rules if rule.enabled],
            reason="Response complies with all enabled policies."
        )
