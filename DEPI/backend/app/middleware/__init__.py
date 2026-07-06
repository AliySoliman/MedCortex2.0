# backend/app/middleware/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Middleware Module
# Custom middleware for request/response processing
# ─────────────────────────────────────────────────────────────────────────────

from app.middleware.logging_middleware import LoggingMiddleware

__all__ = ["LoggingMiddleware"]
