"""Unit tests for database URL redaction (M003) — must never leak passwords."""

from __future__ import annotations

from src.core.db import redact_database_url


def test_redacts_password() -> None:
    url = "postgresql+asyncpg://agrin:s3cretpw@localhost:5432/agrin"
    redacted = redact_database_url(url)
    assert "s3cretpw" not in redacted
    assert "agrin" in redacted
    assert "localhost" in redacted


def test_no_password_left_to_redact() -> None:
    url = "postgresql+asyncpg://agrin@localhost:5432/agrin"
    assert "agrin" in redact_database_url(url)


def test_unparseable_url_does_not_leak() -> None:
    assert redact_database_url("not a url with s3cret") == "<unparseable database url>"
