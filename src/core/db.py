"""Async database engine, session factory, and FastAPI session dependency.

Sessions are created per-request and always closed (even when a handler
raises). The engine/session factory are built lazily and cached so importing
this module never requires a reachable database (M003).
"""

from __future__ import annotations

import functools
from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

POOL_SIZE = 5
MAX_OVERFLOW = 10
POOL_RECYCLE_SECONDS = 1800


def redact_database_url(url: str) -> str:
    """Return ``url`` with any password replaced by ``***`` for safe logging."""
    try:
        return make_url(url).render_as_string(hide_password=True)
    except Exception:  # pragma: no cover - defensive, never leak on failure
        return "<unparseable database url>"


@functools.lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Build (once) the async engine from configured ``database_url``."""
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "database_url is not configured; set DATABASE_URL before using the database."
        )
    connect_args: dict[str, object] = {}
    db_url = settings.database_url
    if "supabase.co" in db_url or "ssl=require" in db_url or "sslmode=require" in db_url:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx
        db_url = (
            db_url.replace("?ssl=require", "")
            .replace("&ssl=require", "")
            .replace("?sslmode=require", "")
            .replace("&sslmode=require", "")
        )

    return create_async_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_recycle=POOL_RECYCLE_SECONDS,
    )


@functools.lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Build (once) the async session factory bound to the engine."""
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a session that is always closed."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Dispose the cached engine (used on shutdown and in tests)."""
    if get_engine.cache_info().currsize:
        engine = get_engine()
        await engine.dispose()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
