"""Unit tests for the security utilities: password hashing (M008) and JWT
token helpers (M009)."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from src.core import security
from src.core.config import Settings
from src.core.errors import InvalidToken


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


# --- JWT helpers (M009) ---


def test_access_token_round_trip() -> None:
    user_id = uuid.uuid4()
    token = security.create_access_token(user_id)
    claims = security.decode_token(token, "access")
    assert claims["sub"] == str(user_id)
    assert claims["type"] == "access"
    ttl = int(claims["exp"]) - int(claims["iat"])
    assert ttl == 15 * 60  # settings default jwt_access_ttl_minutes


def test_refresh_token_round_trip_and_ttl() -> None:
    user_id = uuid.uuid4()
    jti = uuid.uuid4()
    token = security.create_refresh_token(user_id, jti=jti)
    claims = security.decode_token(token, "refresh")
    assert claims["sub"] == str(user_id)
    assert claims["type"] == "refresh"
    assert claims["jti"] == str(jti)  # M055: revocation key is in the claim
    ttl = int(claims["exp"]) - int(claims["iat"])
    assert ttl == 7 * 24 * 3600  # settings default jwt_refresh_ttl_days


def test_access_token_rejected_where_refresh_expected() -> None:
    token = security.create_access_token(uuid.uuid4())
    with pytest.raises(InvalidToken):
        security.decode_token(token, "refresh")


def test_refresh_token_rejected_where_access_expected() -> None:
    token = security.create_refresh_token(uuid.uuid4(), jti=uuid.uuid4())
    with pytest.raises(InvalidToken):
        security.decode_token(token, "access")


def test_tampered_token_rejected() -> None:
    token = security.create_access_token(uuid.uuid4())
    mid = 10
    flipped = "A" if token[mid] != "A" else "B"
    tampered = token[:mid] + flipped + token[mid + 1 :]
    with pytest.raises(InvalidToken):
        security.decode_token(tampered, "access")


def test_expired_token_rejected() -> None:
    now = datetime.now(UTC) - timedelta(hours=1)  # well beyond the 5s leeway
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=1)).timestamp()),
    }
    token = pyjwt.encode(payload, security.get_jwt_secret(), algorithm=security.JWT_ALGORITHM)
    with pytest.raises(InvalidToken):
        security.decode_token(token, "access")


def test_token_missing_required_claim_rejected() -> None:
    payload = {
        "sub": str(uuid.uuid4()),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        # no "type"
    }
    token = pyjwt.encode(payload, security.get_jwt_secret(), algorithm=security.JWT_ALGORITHM)
    with pytest.raises(InvalidToken):
        security.decode_token(token, "access")


def test_missing_jwt_secret_fails_clearly_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unconfigured = Settings(jwt_secret=None)
    monkeypatch.setattr(security, "get_settings", lambda: unconfigured)
    with pytest.raises(RuntimeError, match="jwt_secret"):
        security.get_jwt_secret()
