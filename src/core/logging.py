"""JSON-structured logging configuration.

Every log record is emitted as a single JSON object on one line. A record's
``extra`` fields are merged in; non-serializable values fall back to ``repr``
so logging can never crash a request (M005).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from src.core.config import get_settings

_RESERVED = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}


def _json_default(value: Any) -> str:
    """Last-resort encoder for objects the JSON encoder cannot handle."""
    try:
        return repr(value)
    except Exception:  # pragma: no cover - repr raising is pathological
        return "<unrepresentable>"


class JsonFormatter(logging.Formatter):
    """Render a log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=_json_default, ensure_ascii=False)


def configure_logging(level: str | None = None) -> None:
    """Install the JSON handler on the root logger (idempotent)."""
    resolved = (level or get_settings().log_level).upper()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(resolved)

    for noisy in ("uvicorn.access", "uvicorn.error"):
        logging.getLogger(noisy).handlers.clear()
        logging.getLogger(noisy).propagate = True
