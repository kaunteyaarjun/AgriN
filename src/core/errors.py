"""Application error hierarchy and FastAPI exception handlers.

Client-facing responses are always sanitized: an ``AppError`` exposes only its
stable ``error_code`` and human-safe ``message``; any unhandled exception is
reported to the client as a generic 500 while the full traceback goes only to
the server log (M005).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("agrin.errors")


class AppError(Exception):
    """Base class for expected, safe-to-report application errors."""

    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "An internal error occurred."
    headers: dict[str, str] | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        if headers is not None:
            self.headers = headers
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


class UpstreamUnavailable(AppError):
    status_code = 502
    error_code = "upstream_unavailable"
    message = "An upstream service could not be reached. Please try again later."


class RateLimited(AppError):
    """Too many requests from one client (M055). Carries Retry-After."""

    status_code = 429
    error_code = "rate_limited"
    message = "Too many requests. Please try again later."

    def __init__(self, *, retry_after: int) -> None:
        super().__init__(headers={"Retry-After": str(retry_after)})


_HTTP_STATUS_CODES: dict[int, tuple[str, str]] = {
    400: ("bad_request", "The request was malformed."),
    401: ("not_authenticated", "Authentication is required."),
    403: ("permission_denied", "You do not have permission to perform this action."),
    404: ("not_found", "The requested resource was not found."),
    405: ("method_not_allowed", "That HTTP method is not allowed for this path."),
    409: ("conflict", "The request conflicts with the current state."),
    413: ("payload_too_large", "The request payload is too large."),
    415: ("unsupported_media_type", "The media type is not supported."),
    422: ("validation_failed", "The request was invalid."),
    429: ("rate_limited", "Too many requests. Please try again later."),
}
"""Static status → stable code mapping for framework-raised errors
(Starlette route-mismatch 404/405 live here — M017's debt, paid M055)."""

_VALIDATION_MESSAGE_CAP = 512


def _validation_message(exc: RequestValidationError) -> str:
    """Fold pydantic's field errors into one safe message (no `detail` key)."""
    parts: list[str] = []
    for err in exc.errors()[:5]:
        location = ".".join(str(item) for item in err.get("loc", ()) if item != "body")
        text = str(err.get("msg", "invalid"))
        parts.append(f"{location}: {text}" if location else text)
    message = "; ".join(parts) or "The request was invalid."
    if len(message) > _VALIDATION_MESSAGE_CAP:
        message = message[:_VALIDATION_MESSAGE_CAP] + "…"
    return message


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
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        """One envelope for every 422 (M055 unification: no `{detail}`)."""
        return JSONResponse(
            status_code=422,
            content={"error_code": "validation_failed", "message": _validation_message(exc)},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Framework-raised errors (route 404, 405, …) in the same envelope.

        Only Starlette's static phrases are ever echoed; status codes
        outside the table get a generic message (M017: no leaks).
        """
        error_code, message = _HTTP_STATUS_CODES.get(
            exc.status_code, ("http_error", "The request could not be completed.")
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": error_code, "message": message},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error_code": "internal_error", "message": "An internal error occurred."},
        )
