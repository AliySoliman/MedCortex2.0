# backend/app/models/patient.py
# ─────────────────────────────────────────────────────────────────────────────
# Patient Profile Model
# Stores structured longitudinal clinical data extracted by the MedicalCoordinatorAgent
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Structured Clinical Data
    demographics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    chronic_conditions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    medications: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    allergies: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    surgical_history: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    family_history: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Timeline
    clinical_events: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", backref="patient_profile")
