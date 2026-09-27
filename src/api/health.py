"""Health and readiness probes (M007).

``/health`` is a pure liveness probe: it answers as long as the process is
serving. ``/ready`` checks that the database answers ``SELECT 1`` within a
bounded timeout, so a hung (not merely failing) database produces a fast 503
instead of a stuck request. Both probes are public but non-revealing: the
response body is only an up/down status; detail goes to the server log.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.core.db import get_engine

logger = logging.getLogger("agrin.health")

READY_TIMEOUT_S = 2.0
"""Hard ceiling for the readiness DB check; beyond it the answer is 503."""

router = APIRouter(tags=["infra"])


async def _database_reachable() -> None:
    """Raise (any exception) if the database cannot answer ``SELECT 1``."""
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


def _unavailable() -> JSONResponse:
    return JSONResponse(status_code=503, content={"status": "unavailable"})


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Process liveness — no dependencies, always 200 while serving."""
    return {"status": "ok"}


@router.get(
    "/ready",
    summary="Readiness probe (database)",
    responses={
        200: {"description": "Database reachable."},
        503: {"description": "Database unreachable or slow; status only."},
    },
)
async def ready() -> Response:
    """Readiness — 200 only if the DB answers within READY_TIMEOUT_S."""
    try:
        await asyncio.wait_for(_database_reachable(), timeout=READY_TIMEOUT_S)
    except TimeoutError:
        logger.warning("readiness_timeout", extra={"timeout_s": READY_TIMEOUT_S})
        return _unavailable()
    except Exception as exc:
        # Client learns only "unavailable"; the type goes to the server log.
        logger.warning(
            "readiness_check_failed",
            extra={"error_type": type(exc).__name__},
        )
        return _unavailable()
    return JSONResponse(status_code=200, content={"status": "ready"})
