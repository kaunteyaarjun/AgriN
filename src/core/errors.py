"""Application error hierarchy and FastAPI exception handlers.

Client-facing responses are always sanitized: an ``AppError`` exposes only its
stable ``error_code`` and human-safe ``message``; any unhandled exception is
reported to the client as a generic 500 while the full traceback goes only to
the server log (M005).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("agrin.errors")


class AppError(Exception):
    """Base class for expected, safe-to-report application errors."""

    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "An internal error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class ValidationFailed(AppError):
    status_code = 422
    error_code = "validation_failed"
    message = "The request was invalid."


class NotFound(AppError):
    status_code = 404
    error_code = "not_found"
    message = "The requested resource was not found."


class NotAuthenticated(AppError):
    status_code = 401
    error_code = "not_authenticated"
    message = "Authentication is required."


class InvalidCredentials(AppError):
    """Login failed. Identical body for unknown-email and wrong-password so
    the response cannot be used to enumerate accounts (M009)."""

    status_code = 401
    error_code = "invalid_credentials"
    message = "Invalid email or password."


class InvalidToken(AppError):
    status_code = 401
    error_code = "invalid_token"
    message = "The provided token is invalid or expired."


class AccountDisabled(AppError):
    status_code = 403
    error_code = "account_disabled"
    message = "This account has been disabled."


class PermissionDenied(AppError):
    status_code = 403
    error_code = "permission_denied"
    message = "You do not have permission to perform this action."


class Conflict(AppError):
    status_code = 409
    error_code = "conflict"
    message = "The request conflicts with the current state."


class PayloadTooLarge(AppError):
    status_code = 413
    error_code = "payload_too_large"
    message = "The uploaded file is too large."


class ImageTooLarge(AppError):
    status_code = 413
    error_code = "image_too_large"
    message = "The image dimensions are too large."


class UnsupportedMediaType(AppError):
    status_code = 415
    error_code = "unsupported_media_type"
    message = "The media type is not supported."


class InvalidImage(AppError):
    status_code = 422
    error_code = "invalid_image"
    message = "The image file is corrupt or invalid."


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the AgriN exception handlers to ``app``."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            extra={"error_code": exc.error_code, "status_code": exc.status_code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error_code": "internal_error", "message": "An internal error occurred."},
        )
