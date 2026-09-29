"""LLM family interface - follows the disease/weather pattern (M040).

Defines the typed contract every model-backed source must satisfy:
``LLMRequest`` / ``LLMResponse`` / ``LLMUsage`` (validated at the
boundary), the abstract ``LLMProvider.complete`` and the typed
``get_llm_provider`` accessor. The demo implementation registers under
``("llm", "demo")``; the live model (M042, locked) registers under
``("llm", "live")``. M041's advisory service consumes the result - this
module is the single source of truth for the shape of a completion.

Two request fields, two jobs: ``system`` carries the *instructions* to
the model, ``prompt`` carries the *content* a farmer should read. The
split is what lets a templated demo (which has no model) stay honest -
it renders ``prompt`` and drops ``system``. One round-trip, no
streaming, no chat history: M041 asks one question and gets one answer.
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.core.config import ProviderMode
from src.providers.base import BaseProvider
from src.providers.errors import ProviderError
from src.providers.registry import get_provider

CHARS_PER_TOKEN = 4
"""Documented demo heuristic: one token ~ four characters. A live
provider (M042) reports its upstream's real counts instead."""

PROMPT_MAX_CHARS = 16_000
SYSTEM_MAX_CHARS = 4_000
MAX_TOKENS_DEFAULT = 2048
MAX_TOKENS_LIMIT = 8_192
RESPONSE_TEXT_MAX_CHARS = 65_536
"""Upper sanity bound on returned text. Comfortably above the largest
demo output (``MAX_TOKENS_LIMIT * CHARS_PER_TOKEN`` + header), so the
bound only ever trips a genuinely broken live payload."""

FinishReason = Literal["stop", "length"]


class LLMUsage(BaseModel):
    """Token accounting. Demo mode estimates ``ceil(chars /
    CHARS_PER_TOKEN)``; M042 maps whatever its upstream reports."""

    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class LLMRequest(BaseModel):
    """One completion request.

    ``prompt`` must be non-blank: an empty prompt is a caller bug and
    fails at construction, before any provider (or upstream) is touched.
    """

    system: str | None = Field(default=None, max_length=SYSTEM_MAX_CHARS)
    prompt: str = Field(min_length=1, max_length=PROMPT_MAX_CHARS)
    max_tokens: int = Field(default=MAX_TOKENS_DEFAULT, gt=0, le=MAX_TOKENS_LIMIT)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)

    @field_validator("prompt")
    @classmethod
    def _prompt_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("prompt must not be blank")
        return value


class LLMResponse(BaseModel):
    """Result of one completion. ``text`` is bounded so an absurd
    upstream payload fails at the model boundary (M036 rule: the
    implementation maps that ``ValidationError`` to
    ``ProviderResponseInvalid``)."""

    source: str
    text: str = Field(min_length=1, max_length=RESPONSE_TEXT_MAX_CHARS)
    finish_reason: FinishReason
    usage: LLMUsage
    generated_at: datetime


class LLMProvider(BaseProvider):
    """Abstract model source: one prompt in, one validated answer out."""

    family = "llm"

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Return a validated completion. Raise ``ProviderUnavailable`` /
        ``ProviderResponseInvalid`` on failure (never raw upstream
        exceptions - mapping is the implementation's job)."""


def get_llm_provider(*, mode: ProviderMode | None = None) -> LLMProvider:
    """Typed accessor - same lookup as ``get_provider``, no casts for
    callers."""
    provider = get_provider("llm", mode=mode)
    if not isinstance(provider, LLMProvider):
        raise ProviderError(f"Registered LLM provider {provider!r} does not implement LLMProvider.")
    return provider
