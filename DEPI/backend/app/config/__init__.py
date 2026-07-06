# backend/app/config/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Config Module
# Application configuration management
# ─────────────────────────────────────────────────────────────────────────────

from app.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
