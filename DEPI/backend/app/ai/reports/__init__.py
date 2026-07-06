# backend/app/ai/reports/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Reports Module
# Medical report generation and formatting
# ─────────────────────────────────────────────────────────────────────────────

from app.ai.reports.report_generator import ReportGenerator

__all__ = ["ReportGenerator"]
