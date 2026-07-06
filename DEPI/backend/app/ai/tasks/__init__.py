# backend/app/ai/tasks/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Tasks Module
# AI Task abstraction for all interactions
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.tasks.task import AITask
from app.ai.tasks.chat_task import ChatTask
from app.ai.tasks.vision_task import VisionTask
from app.ai.tasks.diagnosis_task import DiagnosisTask
from app.ai.tasks.prescription_task import PrescriptionTask
from app.ai.tasks.lab_task import LabTask
from app.ai.tasks.report_task import ReportTask

__all__ = [
    "AITask",
    "ChatTask",
    "VisionTask",
    "DiagnosisTask",
    "PrescriptionTask",
    "LabTask",
    "ReportTask",
]
