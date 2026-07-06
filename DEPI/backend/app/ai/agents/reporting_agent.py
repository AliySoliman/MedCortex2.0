# backend/app/ai/agents/reporting_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# Reporting Agent
# Synthesises AgentContext into a structured clinical summary / report.
# ─────────────────────────────────────────────────────────────────────────────

import time
import logging
from typing import Optional

from app.ai.agents.base import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger(__name__)


class ReportingAgent(BaseAgent):
    """
    Synthesises all agent outputs stored in AgentContext into a coherent
    structured clinical report.

    This agent always runs last in the coordinator pipeline.
    """

    def __init__(self) -> None:
        super().__init__(name="reporting_agent")

    async def run(self, context: AgentContext) -> AgentResult:
        """Generate a structured clinical report from the AgentContext."""
        start = time.monotonic()
        self._trace(context, "Generating clinical report.")

        try:
            sections = []

            # ── RAG Answer ────────────────────────────────────────────────────
            if context.rag_answer:
                sections.append(f"## Clinical Assessment\n{context.rag_answer}")

            # ── Symptoms ──────────────────────────────────────────────────────
            if context.extracted_symptoms:
                symptom_list = "\n".join(f"  - {s}" for s in context.extracted_symptoms)
                sections.append(f"## Identified Symptoms\n{symptom_list}")

            # ── Differential Diagnoses ────────────────────────────────────────
            if context.differential_diagnoses:
                ddx_lines = []
                for ddx in context.differential_diagnoses[:5]:
                    condition = ddx.get("condition", "Unknown")
                    confidence = ddx.get("confidence", 0.0)
                    ddx_lines.append(f"  - {condition} (confidence: {confidence:.0%})")
                sections.append(f"## Differential Diagnoses\n" + "\n".join(ddx_lines))

            # ── Risk Assessment ───────────────────────────────────────────────
            if context.risk_assessment:
                risk = context.risk_assessment
                level = risk.get("level", "UNKNOWN")
                factors = "\n".join(f"  - {f}" for f in risk.get("factors", []))
                rec = risk.get("recommendation", "")
                sections.append(
                    f"## Risk Assessment\n**Level**: {level}\n{factors}\n{rec}"
                )

            # ── Drug Interactions ─────────────────────────────────────────────
            if context.drug_interactions:
                lines = []
                for i in context.drug_interactions:
                    lines.append(
                        f"  - {i.get('drug_a')} + {i.get('drug_b')}: "
                        f"{i.get('severity', '').upper()} — {i.get('description', '')}"
                    )
                sections.append(f"## Drug Interactions\n" + "\n".join(lines))

            # ── Lab Findings ──────────────────────────────────────────────────
            if context.lab_interpretations:
                lab_lines = []
                for lab in context.lab_interpretations:
                    lab_lines.append(
                        f"  - {lab.get('name', '')}: {lab.get('value', '')} "
                        f"{lab.get('unit', '')} [{lab.get('flag', '')}]"
                    )
                sections.append(f"## Abnormal Laboratory Values\n" + "\n".join(lab_lines))

            # ── Recommendations ───────────────────────────────────────────────
            if context.recommendations:
                rec_lines = [
                    f"  {i+1}. [{r.get('type','').upper()}] {r.get('description','')}"
                    for i, r in enumerate(context.recommendations)
                ]
                sections.append(f"## Recommendations\n" + "\n".join(rec_lines))

            # ── Citations ─────────────────────────────────────────────────────
            if context.citations:
                cit_lines = [f"  [{i+1}] {c}" for i, c in enumerate(context.citations)]
                sections.append(f"## Evidence Sources\n" + "\n".join(cit_lines))

            # ── Safety Issues ─────────────────────────────────────────────────
            if context.safety_issues:
                issue_lines = "\n".join(f"  ⚠ {s}" for s in context.safety_issues)
                sections.append(f"## Safety Notes\n{issue_lines}")

            context.generated_report = "\n\n".join(sections)
            self._trace(context, f"Report generated: {len(context.generated_report)} chars.")

            duration_ms = (time.monotonic() - start) * 1000
            return self._success(
                context,
                output={"report_length": len(context.generated_report)},
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            logger.exception("ReportingAgent failed")
            return self._failure(context, error=str(exc), duration_ms=duration_ms)
