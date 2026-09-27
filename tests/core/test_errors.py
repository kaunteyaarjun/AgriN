"""Tests for AppError and the FastAPI exception handlers (M005)."""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI
from src.core.errors import (
    AppError,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationFailed,
    register_exception_handlers,
)


def _app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/app-error")
    async def _app_error() -> None:
        raise NotFound("Farm 42 not found.")

    @app.get("/unhandled")
    async def _unhandled() -> None:
        raise RuntimeError("secret internal detail: db password is hunter2")

    return app


async def _get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


async def test_app_error_returns_mapped_status_and_safe_body() -> None:
    response = await _get("/app-error")
    assert response.status_code == 404
    body = response.json()
    assert body == {"error_code": "not_found", "message": "Farm 42 not found."}


async def test_unhandled_exception_is_generic_and_leaks_nothing() -> None:
    response = await _get("/unhandled")
    assert response.status_code == 500
    body = response.json()
    assert body == {
        "error_code": "internal_error",
        "message": "An internal error occurred.",
    }
    assert "hunter2" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text


def test_default_status_codes() -> None:
    assert AppError().status_code == 500
    assert ValidationFailed().status_code == 422
    assert NotAuthenticated().status_code == 401
    assert PermissionDenied().status_code == 403


def test_app_error_can_override_message_and_code() -> None:
    err = AppError("custom", error_code="custom_code", status_code=418)
    assert err.message == "custom"
    assert err.error_code == "custom_code"
    assert err.status_code == 418
    assert str(err) == "custom"


@pytest.mark.parametrize(
    "exc_cls", [ValidationFailed, NotFound, NotAuthenticated, PermissionDenied]
)
def test_subclasses_have_stable_codes(exc_cls: type[AppError]) -> None:
    assert exc_cls.error_code
    assert exc_cls.message
