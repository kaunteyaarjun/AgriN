"""API v1 router aggregator.

Endpoint milestones register their routers here under ``/api/v1``.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.api.v1.advisory import router as advisory_router
from src.api.v1.auth import router as auth_router
from src.api.v1.farm_state import router as farm_state_router
from src.api.v1.farmers import router as farmers_router
from src.api.v1.farms import router as farms_router
from src.api.v1.images import router as images_router
from src.api.v1.plots import router as plots_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(farmers_router)
api_router.include_router(farms_router)
api_router.include_router(plots_router)
api_router.include_router(images_router)
api_router.include_router(farm_state_router)
api_router.include_router(advisory_router)


@api_router.get("/ping", tags=["meta"])
async def ping() -> dict[str, str]:
    """Lightweight versioned liveness probe used by tests."""
    return {"status": "ok"}
