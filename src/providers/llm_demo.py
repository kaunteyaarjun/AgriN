"""LLM demo provider (M040): deterministic, network-free templated text.

Registered on the default registry under ``("llm", "demo")``, so the
default ``llm_provider = "demo"`` flag resolves to it through the normal
M021 path. Output derives from a sha256 seed of the request
(``request_seed``) - the same request always yields the same text, which
is what makes the demo and its tests stable.

Documented behavior (tested):
- template = one opening from ``OPENINGS`` + the caller's ``prompt``;
- ``system`` is **never** echoed - instructions are not advice;
- ``prompt`` is quoted verbatim when it fits the budget;
- budget = ``max_tokens * CHARS_PER_TOKEN``; a longer ``prompt`` is cut
  at a word boundary and reported as ``finish_reason="length"``, else
  ``"stop"``;
- usage is an estimate: ``ceil(chars / CHARS_PER_TOKEN)`` per side,
  ``total = prompt + completion``.

The template has no source of facts other than the request, so it cannot
invent agronomic claims. A live model (M042, locked) registers under
``("llm", "live")`` behind the same ABC.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from math import ceil

from src.providers.llm import (
    CHARS_PER_TOKEN,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from src.providers.registry import register

DEMO_NAME = "demo-llm-v1"

OPENINGS: tuple[str, ...] = (
    "Advisory preview (deterministic demo output, no live model called):",
    "Demo advisory (demo-llm-v1), content quoted from the request:",
    "Simulated advisory - generated locally from the request only:",
)
"""Three fixed openings. ``temperature`` only selects among them - a
template has no other use for it."""


def request_seed(request: LLMRequest) -> int:
    """Stable 64-bit seed per request (full sha256, 16 hex chars)."""
    canonical = "\n".join(
        (
            request.system or "",
            request.prompt,
            str(request.max_tokens),
            repr(request.temperature),
        )
    )
    return int(hashlib.sha256(canonical.encode()).hexdigest()[:16], 16)


def truncate_to_budget(text: str, budget: int) -> tuple[str, bool]:
    """Cut ``text`` back to the last word boundary within ``budget``
    characters. Returns ``(trimmed, was_truncated)``."""
    if len(text) <= budget:
        return text, False
    cut = text.rfind(" ", 0, budget)
    candidate = text[:cut].rstrip() if cut > 0 else ""
    if not candidate:
        candidate = text[:budget].rstrip()
    return candidate, True


@register
class DemoLLMProvider(LLMProvider):
    """Templated text over the request's own content. No I/O, no model
    by design - it renders what the caller supplied, never more."""

    mode = "demo"
    name = DEMO_NAME

    async def complete(self, request: LLMRequest) -> LLMResponse:
        budget = request.max_tokens * CHARS_PER_TOKEN
        body, truncated = truncate_to_budget(request.prompt, budget)
        text = f"{OPENINGS[request_seed(request) % len(OPENINGS)]}\n\n{body}"
        prompt_tokens = ceil(len((request.system or "") + request.prompt) / CHARS_PER_TOKEN)
        completion_tokens = ceil(len(text) / CHARS_PER_TOKEN)
        return LLMResponse(
            source=self.name,
            text=text,
            finish_reason="length" if truncated else "stop",
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            generated_at=datetime.now(UTC),
        )
