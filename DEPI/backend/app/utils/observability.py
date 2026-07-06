# backend/app/utils/observability.py
# ─────────────────────────────────────────────────────────────────────────────
# Observability — Structured Logging & Metrics
# All subsystems must use this module for logging.
# Supports JSON (production) and text (development) formats.
# ─────────────────────────────────────────────────────────────────────────────

import json
import logging
import time
import uuid
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generator, Optional


class StructuredLogger:
    """
    Wraps Python's standard logging with structured JSON output.
    Every log entry includes service, trace_id, and arbitrary context fields.
    """

    def __init__(self, name: str, service: str = "medcortex") -> None:
        self._logger = logging.getLogger(name)
        self._service = service

    def _emit(self, level: str, message: str, **fields: Any) -> None:
        record: Dict[str, Any] = {
            "service": self._service,
            "logger": self._logger.name,
            "level": level,
            "message": message,
            **fields,
        }
        log_fn = getattr(self._logger, level.lower(), self._logger.info)
        log_fn(json.dumps(record))

    def info(self, message: str, **fields: Any) -> None:
        self._emit("INFO", message, **fields)

    def debug(self, message: str, **fields: Any) -> None:
        self._emit("DEBUG", message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._emit("WARNING", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._emit("ERROR", message, **fields)

    def critical(self, message: str, **fields: Any) -> None:
        self._emit("CRITICAL", message, **fields)


class MetricsCollector:
    """
    Simple in-memory metrics collector for counters and histograms.
    In production, replace the underlying store with Prometheus / Datadog.
    """

    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}
        self._histograms: Dict[str, list] = {}

    def increment(self, metric: str, value: int = 1, **labels: str) -> None:
        key = self._make_key(metric, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def record(self, metric: str, value: float, **labels: str) -> None:
        key = self._make_key(metric, labels)
        self._histograms.setdefault(key, []).append(value)

    def get_counter(self, metric: str, **labels: str) -> int:
        return self._counters.get(self._make_key(metric, labels), 0)

    def get_histogram(self, metric: str, **labels: str) -> list:
        return self._histograms.get(self._make_key(metric, labels), [])

    def snapshot(self) -> Dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                }
                for k, v in self._histograms.items()
            },
        }

    @staticmethod
    def _make_key(metric: str, labels: Dict[str, str]) -> str:
        if not labels:
            return metric
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric}{{{label_str}}}"


# ── Module-level singletons ───────────────────────────────────────────────────
metrics = MetricsCollector()


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger for a given module name."""
    return StructuredLogger(name)


@contextmanager
def timed_operation(
    metric_name: str,
    logger: Optional[StructuredLogger] = None,
    **labels: str,
) -> Generator[None, None, None]:
    """
    Context manager that records latency of a code block.

    Usage::

        with timed_operation("rag.retrieval", logger=log, component="rag"):
            result = run_retrieval()
    """
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = (time.monotonic() - start) * 1000
        metrics.record(metric_name, elapsed_ms, **labels)
        if logger:
            logger.debug(f"{metric_name} completed", duration_ms=round(elapsed_ms, 2), **labels)


def trace_agent(func: Callable) -> Callable:
    """
    Decorator that auto-traces an agent's async run() method.
    Records a call counter and latency histogram.
    """
    @wraps(func)
    async def wrapper(self, context, *args, **kwargs):
        agent_name = getattr(self, "name", func.__qualname__)
        metrics.increment("agent.calls", agent_name=agent_name)
        start = time.monotonic()
        try:
            result = await func(self, context, *args, **kwargs)
            status = "success" if result.success else "failure"
            metrics.increment(f"agent.{status}", agent_name=agent_name)
            return result
        except Exception:
            metrics.increment("agent.exception", agent_name=agent_name)
            raise
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            metrics.record("agent.duration_ms", elapsed_ms, agent_name=agent_name)
    return wrapper


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    """
    Configure root logger.

    Args:
        level: Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        fmt: Output format — 'json' for structured, 'text' for human-readable.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    if fmt == "text":
        log_format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
        logging.basicConfig(level=numeric_level, format=log_format)
    else:
        # JSON format: rely on StructuredLogger to emit JSON strings
        logging.basicConfig(level=numeric_level, format="%(message)s")
