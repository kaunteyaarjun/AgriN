"""AgriN FastAPI application.

The app factory wires configuration, structured logging (M005), sanitized
exception handlers (M005), security headers and the optional interactive
docs (M055), the health/readiness probes (M007), the versioned API router,
and an explicit CORS allow-list. Domain endpoints are mounted in later
milestones.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.api.health import router as health_router
from src.api.v1 import api_router
from src.core.config import get_settings
from src.core.errors import register_exception_handlers
from src.core.logging import configure_logging

APP_NAME = "AgriN API"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Self-hostable digital agriculture intelligence platform."

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}
"""Baseline headers on every response (M055). No HSTS — that belongs
to the TLS terminator; no CSP — the future frontend owns its policy."""


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Configure process-wide logging on startup."""
    configure_logging()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
        # M055 kill-switch: /docs, /redoc and /openapi.json vanish when off.
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    @app.middleware("http")
    async def _security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    # Infra probes stay at the root (outside /api/v1) so orchestration tools
    # need no version knowledge; both are public by design (M007/M010 allow-list).
    app.include_router(health_router)
    app.include_router(api_router)

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        """Basic app metadata."""
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "environment": settings.env,
        }

    return app


app = create_app()
