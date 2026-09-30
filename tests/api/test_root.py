"""API-level tests for the FastAPI app skeleton (M006)."""

from __future__ import annotations

from typing import Any, cast

from fastapi.middleware.cors import CORSMiddleware
from src.core.config import get_settings
from src.main import create_app

from tests.conftest import _client


async def test_root_returns_app_metadata() -> None:
    async with await _client() as client:
        response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "AgriN API"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "dev"


async def test_openapi_schema_available() -> None:
    async with await _client() as client:
        response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AgriN API"


async def test_versioned_router_mounted() -> None:
    async with await _client() as client:
        response = await client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_cors_is_not_wildcard() -> None:
    app = create_app()
    cors = [m for m in app.user_middleware if m.cls is CORSMiddleware]
    assert cors, "CORSMiddleware must be registered"
    allow_origins = cast(Any, cors[0]).kwargs.get("allow_origins")
    assert allow_origins != ["*"]
    assert "*" not in allow_origins
    assert get_settings().cors_origins == allow_origins
