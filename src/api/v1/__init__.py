"""API v1 router aggregator.

Endpoint milestones register their routers here under ``/api/v1``.
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/ping", tags=["meta"])
async def ping() -> dict[str, str]:
    """Lightweight versioned liveness probe used by tests."""
    return {"status": "ok"}
