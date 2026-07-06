# backend/app/ai/clinical/timeline_builder.py
# ─────────────────────────────────────────────────────────────────────────────
# Timeline Builder
# Constructs chronological patient clinical timelines from structured context.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    event_type: str  # diagnosis | medication_started | lab_result | visit | upload
    description: str
    date: Optional[str] = None
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PatientTimeline(BaseModel):
    patient_id: str
    events: List[TimelineEvent] = Field(default_factory=list)


class TimelineBuilder:
    """
    Builds and manages patient clinical timelines.
    Extracts events from UnifiedMedicalContext dicts and sorts chronologically.
    """

    def add_event(self, timeline: PatientTimeline, event: TimelineEvent) -> PatientTimeline:
        """Append an event to the timeline and return updated object."""
        timeline.events.append(event)
        return timeline

    def from_context(self, context_dict: Dict[str, Any]) -> List[TimelineEvent]:
        """
        Extract timeline events from a serialized UnifiedMedicalContext dict.

        Args:
            context_dict: Serialized UnifiedMedicalContext.

        Returns:
            List of TimelineEvent objects extracted from the context.
        """
        events: List[TimelineEvent] = []
        source = f"upload:{context_dict.get('upload_id', 'unknown')}"
        doc_date = context_dict.get("document_information", {}).get("date")

        # Upload event
        events.append(TimelineEvent(
            event_type="upload",
            description=f"Document uploaded: {context_dict.get('filename', 'unknown')}",
            date=doc_date,
            source=source,
            metadata={"mime_type": context_dict.get("mime_type")},
        ))

        # Medication started events
        for med in context_dict.get("medications", []):
            events.append(TimelineEvent(
                event_type="medication_started",
                description=(
                    f"Medication: {med.get('name', 'Unknown')} "
                    f"{med.get('dosage', '')} {med.get('frequency', '')}".strip()
                ),
                date=doc_date,
                source=source,
                metadata=med,
            ))

        # Diagnosis recorded events
        for dx in context_dict.get("diagnoses", []):
            events.append(TimelineEvent(
                event_type="diagnosis_recorded",
                description=f"Diagnosis: {dx.get('name', 'Unknown')} — {dx.get('status', '')}",
                date=doc_date,
                source=source,
                metadata=dx,
            ))

        # Lab result events
        for lab in context_dict.get("lab_values", []):
            flag = lab.get("flag", "")
            events.append(TimelineEvent(
                event_type="lab_result",
                description=(
                    f"Lab: {lab.get('name', 'Unknown')} = "
                    f"{lab.get('value', '?')} {lab.get('unit', '')} "
                    f"{'[' + flag + ']' if flag else ''}".strip()
                ),
                date=doc_date,
                source=source,
                metadata=lab,
            ))

        # Clinical findings
        for finding in context_dict.get("clinical_findings", []):
            events.append(TimelineEvent(
                event_type="clinical_finding",
                description=f"Finding: {finding}",
                date=doc_date,
                source=source,
            ))

        return events

    def sort(self, timeline: PatientTimeline) -> PatientTimeline:
        """Sort timeline events chronologically by date, then by creation time."""
        def sort_key(event: TimelineEvent):
            if event.date:
                try:
                    return event.date
                except Exception:
                    pass
            return event.created_at

        timeline.events = sorted(timeline.events, key=sort_key)
        return timeline
