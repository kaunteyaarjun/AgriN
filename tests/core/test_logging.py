"""Unit tests for the JSON log formatter (M005)."""

from __future__ import annotations

import json
import logging

from src.core.logging import JsonFormatter


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="agrin.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_formats_valid_json_with_core_fields() -> None:
    payload = json.loads(JsonFormatter().format(_record()))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "agrin.test"
    assert payload["message"] == "hello world"
    assert "timestamp" in payload


def test_merges_extra_fields() -> None:
    payload = json.loads(JsonFormatter().format(_record(request_id="abc-123")))
    assert payload["request_id"] == "abc-123"


def test_non_serializable_extra_does_not_raise() -> None:
    payload = json.loads(JsonFormatter().format(_record(obj=object())))
    assert isinstance(payload["obj"], str)


def test_exception_included_when_present() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = _record()
        record.exc_info = sys.exc_info()
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError" in payload["exception"]
