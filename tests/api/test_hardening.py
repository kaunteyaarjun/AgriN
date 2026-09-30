"""Security headers and the /docs kill-switch (M055)."""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI
from src.core.config import get_settings
from src.main import SECURITY_HEADERS, create_app


def _client(app: FastAPI | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app or create_app()), base_url="http://t"
    )


@pytest.mark.parametrize("path", ["/", "/api/v1/does-not-exist", "/healthz"])
async def test_security_headers_on_success_and_error_responses(path: str) -> None:
    async with _client() as client:
        response = await client.get(path)
    for header, value in SECURITY_HEADERS.items():
        assert response.headers[header] == value


async def test_docs_and_openapi_are_served_by_default() -> None:
    async with _client() as client:
        docs = await client.get("/docs")
        openapi = await client.get("/openapi.json")
    assert docs.status_code == 200
    assert openapi.status_code == 200


async def test_docs_flag_hides_everything_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "docs_enabled", False)
    async with _client(create_app()) as client:
        for path in ("/docs", "/redoc", "/openapi.json"):
            response = await client.get(path)
            assert response.status_code == 404, path
            assert response.json()["error_code"] == "not_found"  # unified envelope
        api = await client.get("/")  # the API itself is untouched
    assert api.status_code == 200
