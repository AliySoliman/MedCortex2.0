# backend/app/repositories/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Repositories Module
# Data access layer with repository pattern
# ─────────────────────────────────────────────────────────────────────────────

from app.repositories.user_repository import UserRepository

__all__ = ["UserRepository"]
