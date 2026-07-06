from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.medical_report import MedicalReport


class ReportRepository:
    """Repository for Medical Report data access operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        report_type: str,
        title: str,
        content: Dict[str, Any],
        conversation_id: Optional[int] = None,
    ) -> MedicalReport:
        report = MedicalReport(
            user_id=user_id,
            conversation_id=conversation_id,
            report_type=report_type,
            title=title,
            content=content,
            created_at=datetime.utcnow(),
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: int) -> Optional[MedicalReport]:
        return self.db.query(MedicalReport).filter(MedicalReport.id == report_id).first()

    def list_by_user(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[MedicalReport]:
        return (
            self.db.query(MedicalReport)
            .filter(MedicalReport.user_id == user_id)
            .order_by(MedicalReport.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_by_conversation(self, conversation_id: int) -> List[MedicalReport]:
        return (
            self.db.query(MedicalReport)
            .filter(MedicalReport.conversation_id == conversation_id)
            .order_by(MedicalReport.created_at.desc())
            .all()
        )
