from typing import Dict, Any, Optional
from sqlalchemy import Integer, String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    response_style: Mapped[str] = mapped_column(String(50), default="balanced", nullable=False)  # concise, balanced, detailed
    preferred_provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="preferences")
