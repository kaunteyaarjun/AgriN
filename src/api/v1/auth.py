"""Authentication endpoints: login, refresh rotation, logout (M009, M055).

Login is enumeration-safe: unknown email and wrong password return the
identical 401 body, and both paths perform one bcrypt verification (the
unknown-email path verifies against a dummy hash) so response timing does
not reveal which emails exist. Password checks use the async wrappers so
the event loop is never blocked by hashing.

M055 hardening layered on top:
- login/refresh are rate limited per client IP (in-process sliding window);
- every auth outcome emits a structured ``agrin.audit`` event;
- refresh tokens **rotate** and are backed by ``refresh_tokens`` rows —
  replaying a revoked one is reuse detection and revokes the account's
  active tokens;
- ``logout`` (possession-based) and ``logout-all`` (bearer) revoke rows.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import CursorResult, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUserDep, SessionDep
from src.core.audit import audit
from src.core.config import get_settings
from src.core.errors import AccountDisabled, InvalidCredentials, InvalidToken
from src.core.ratelimit import rate_limit
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    dummy_password_hash,
    verify_password_async,
)
from src.models import RefreshToken, User

router = APIRouter(prefix="/auth", tags=["auth"])

PASSWORD_MAX_LENGTH = 128

LoginRateDep = Annotated[None, Depends(rate_limit("auth.login"))]
RefreshRateDep = Annotated[None, Depends(rate_limit("auth.refresh"))]


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    logged_out: bool = True


class LogoutAllResponse(BaseModel):
    revoked: int


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def _issue_refresh(session: AsyncSession, user_id: uuid.UUID) -> str:
    """Mint a refresh token AND its revocation row (one commit)."""
    jti = uuid.uuid4()
    token = create_refresh_token(user_id, jti=jti)
    settings = get_settings()
    session.add(
        RefreshToken(
            id=jti,
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days),
        )
    )
    await session.commit()
    return token


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(
    payload: LoginRequest,
    request: Request,
    _limit: LoginRateDep,  # before SessionDep: a blocked brute-force opens no DB work
    session: SessionDep,
) -> TokenResponse:
    """Issue an access + refresh token pair for valid credentials."""
    ip = _client_ip(request)
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user is None:
        # Same work and identical response as a wrong password: no enumeration.
        await verify_password_async(payload.password, dummy_password_hash())
        audit("auth.login.failure", outcome="failure", email=payload.email, ip=ip)
        raise InvalidCredentials()
    if not await verify_password_async(payload.password, user.password_hash):
        audit(
            "auth.login.failure",
            outcome="failure",
            user_id=str(user.id),
            email=user.email,
            ip=ip,
        )
        raise InvalidCredentials()
    if not user.is_active:
        audit(
            "auth.login.failure",
            outcome="failure",
            user_id=str(user.id),
            email=user.email,
            ip=ip,
            reason="account_disabled",
        )
        raise AccountDisabled()

    # Opportunistic GC: drop this user's expired rows while we're here.
    await session.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.expires_at < datetime.now(UTC),
        )
    )
    refresh_token = await _issue_refresh(session, user.id)
    audit(
        "auth.login.success",
        user_id=str(user.id),
        email=user.email,
        ip=ip,
    )
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    _limit: RefreshRateDep,  # before SessionDep: throttled replay costs no DB work
    session: SessionDep,
) -> TokenResponse:
    """Exchange a refresh token for a NEW pair (rotation, M055).

    The old token's row is revoked; presenting a revoked row later means
    the token leaked — every active token for that user is revoked.
    """
    ip = _client_ip(request)
    try:
        claims = decode_token(payload.refresh_token, "refresh")
    except InvalidToken:
        audit("auth.refresh.failure", outcome="failure", ip=ip, reason="bad_token")
        raise

    try:
        user_uuid = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise InvalidToken() from exc

    jti_raw = claims.get("jti")
    try:
        jti = uuid.UUID(str(jti_raw))
    except (TypeError, ValueError):
        # Pre-M055 token (no jti): force one re-login. Documented.
        audit("auth.refresh.failure", outcome="failure", user_id=str(user_uuid), ip=ip)
        raise InvalidToken(
            "This token predates server-side sessions; please log in again."
        ) from None

    row = await session.get(RefreshToken, jti)
    if row is None or row.user_id != user_uuid:
        audit("auth.refresh.failure", outcome="failure", user_id=str(user_uuid), ip=ip)
        raise InvalidToken()

    now = datetime.now(UTC)
    if row.revoked_at is not None:
        # Reuse detection: a revoked token came back — assume leakage and
        # revoke everything active for this account (OAuth BCP pattern).
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_uuid, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.commit()
        audit(
            "auth.refresh.reuse_detected",
            outcome="failure",
            user_id=str(user_uuid),
            ip=ip,
        )
        raise InvalidToken()
    if row.expires_at <= now:
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == jti, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.commit()
        audit("auth.refresh.failure", outcome="failure", user_id=str(user_uuid), ip=ip)
        raise InvalidToken()

    user = await session.get(User, user_uuid)
    if user is None or not user.is_active:
        row.revoked_at = now
        await session.commit()
        audit("auth.refresh.failure", outcome="failure", user_id=str(user_uuid), ip=ip)
        raise InvalidToken("The account for this token no longer exists or is active.")

    row.revoked_at = now  # rotation: old row dies with this exchange
    refresh_token = await _issue_refresh(session, user_uuid)
    audit("auth.refresh.success", user_id=str(user_uuid), ip=ip)
    return TokenResponse(
        access_token=create_access_token(user_uuid),
        refresh_token=refresh_token,
    )


@router.post("/logout", response_model=LogoutResponse, status_code=200)
async def logout(
    payload: RefreshRequest,
    request: Request,
    session: SessionDep,
) -> LogoutResponse:
    """Revoke the presented refresh token. Idempotent, possession-based:
    any structurally valid token answers success (no existence oracle)."""
    ip = _client_ip(request)
    try:
        claims = decode_token(payload.refresh_token, "refresh")
    except InvalidToken:
        audit("auth.logout", outcome="failure", ip=ip, reason="bad_token")
        raise
    try:
        jti = uuid.UUID(str(claims["jti"]))
    except (KeyError, TypeError, ValueError):
        audit("auth.logout", outcome="failure", ip=ip, reason="bad_jti")
        raise InvalidToken() from None

    row = await session.get(RefreshToken, jti)
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        await session.commit()
    audit("auth.logout", user_id=str(claims["sub"]), ip=ip)
    return LogoutResponse()


@router.post("/logout-all", response_model=LogoutAllResponse, status_code=200)
async def logout_all(
    user: CurrentUserDep,
    request: Request,
    session: SessionDep,
) -> LogoutAllResponse:
    """Revoke every active refresh token for the current user."""
    ip = _client_ip(request)
    result = await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
    revoked = int(cast(CursorResult[Any], result).rowcount or 0)
    audit("auth.logout_all", user_id=str(user.id), ip=ip, revoked=revoked)
    return LogoutAllResponse(revoked=revoked)
