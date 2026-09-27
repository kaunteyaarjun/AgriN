"""Authentication endpoints: login and refresh token issuance (M009).

Login is enumeration-safe: unknown email and wrong password return the
identical 401 body, and both paths perform one bcrypt verification (the
unknown-email path verifies against a dummy hash) so response timing does
not reveal which emails exist. Password checks use the async wrappers so
the event loop is never blocked by hashing.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.api.deps import SessionDep
from src.core.errors import AccountDisabled, InvalidCredentials, InvalidToken
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    dummy_password_hash,
    verify_password_async,
)
from src.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

PASSWORD_MAX_LENGTH = 128


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login(
    payload: LoginRequest,
    session: SessionDep,
) -> TokenResponse:
    """Issue an access + refresh token pair for valid credentials."""
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user is None:
        # Same work and identical response as a wrong password: no enumeration.
        await verify_password_async(payload.password, dummy_password_hash())
        raise InvalidCredentials()
    if not await verify_password_async(payload.password, user.password_hash):
        raise InvalidCredentials()
    if not user.is_active:
        raise AccountDisabled()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh(
    payload: RefreshRequest,
    session: SessionDep,
) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    claims = decode_token(payload.refresh_token, "refresh")
    try:
        user_uuid = uuid.UUID(str(claims["sub"]))
    except ValueError as exc:
        raise InvalidToken() from exc

    user = await session.get(User, user_uuid)
    if user is None or not user.is_active:
        raise InvalidToken("The account for this token no longer exists or is active.")
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=payload.refresh_token,
    )
