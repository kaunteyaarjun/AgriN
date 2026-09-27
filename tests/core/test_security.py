"""Unit tests for the password hashing utilities (M008)."""

from __future__ import annotations

import threading

import pytest
from src.core import security


def test_hash_verify_round_trip() -> None:
    password = "correct-horse-battery-staple-1"
    hashed = security.hash_password(password)
    assert security.verify_password(password, hashed) is True


def test_wrong_password_fails_verification() -> None:
    hashed = security.hash_password("right-password")
    assert security.verify_password("wrong-password", hashed) is False


def test_hashing_is_salted() -> None:
    password = "same-password-twice"
    assert security.hash_password(password) != security.hash_password(password)


def test_hash_is_bcrypt_and_contains_no_plaintext() -> None:
    password = "s3cret-p@ssw0rd"
    hashed = security.hash_password(password)
    assert hashed.startswith("$2b$")
    assert password not in hashed


def test_bcrypt_work_factor_is_explicit() -> None:
    hashed = security.hash_password("work-factor-probe")
    rounds = int(hashed.split("$")[2])
    assert rounds == security.BCRYPT_ROUNDS == 12


def test_malformed_stored_hash_returns_false_without_raising() -> None:
    assert security.verify_password("anything", "not-a-real-hash") is False
    assert security.verify_password("anything", "") is False


async def test_async_wrappers_round_trip() -> None:
    hashed = await security.hash_password_async("async-password")
    assert await security.verify_password_async("async-password", hashed) is True
    assert await security.verify_password_async("async-wrong", hashed) is False


async def test_hash_password_async_runs_off_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verified (not assumed): the sync core executes in a worker thread."""
    main_thread = threading.get_ident()
    seen: list[int] = []

    def _fake_hash(password: str) -> str:
        seen.append(threading.get_ident())
        return "$2b$12$fakefakefakefakefakefak"

    monkeypatch.setattr(security, "hash_password", _fake_hash)
    result = await security.hash_password_async("x")
    assert result == "$2b$12$fakefakefakefakefakefak"
    assert seen and seen[0] != main_thread


async def test_verify_password_async_runs_off_event_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main_thread = threading.get_ident()
    seen: list[int] = []

    def _fake_verify(password: str, password_hash: str) -> bool:
        seen.append(threading.get_ident())
        return True

    monkeypatch.setattr(security, "verify_password", _fake_verify)
    assert await security.verify_password_async("x", "y") is True
    assert seen and seen[0] != main_thread
