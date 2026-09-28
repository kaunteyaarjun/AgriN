"""Provider error hierarchy (M021).

Every provider failure an application layer should ever see is one of
these; messages are safe to log/report (no URLs with keys, no raw
payloads). Retries/backoff are deliberately NOT a provider concern —
the ingestion layer (M023+) decides what is worth retrying.
"""

from __future__ import annotations


class ProviderError(Exception):
    """Base for expected provider failures with a human-safe message."""


class ProviderNotRegistered(ProviderError):
    """No provider registered for the requested family/mode."""


class ProviderUnavailable(ProviderError):
    """Upstream could not be reached — retryable by the caller."""


class ProviderResponseInvalid(ProviderError):
    """Upstream payload violates the typed contract — not retryable."""
