"""AI advisory package (M041): decision -> prompt -> validated text.

Owns the boundary between the structured analysis stack (M032-M039) and
the LLM provider family (M040). Prompt construction is pure
(``build_request``), the provider call is the only I/O
(``generate_advisory``), and the data-gap caveats are M041's own - never
delegated to a model.

M043 (advisory endpoint) and M044 (what-if) both call
``generate_advisory``.
"""

from __future__ import annotations

from src.ai.advisory import (
    ADVISORY_MAX_CHARS,
    ADVISORY_SYSTEM,
    PROMPT_ACTION_LIMIT,
    Advisory,
    advisory_caveats,
    build_request,
    generate_advisory,
)

__all__ = [
    "ADVISORY_MAX_CHARS",
    "ADVISORY_SYSTEM",
    "PROMPT_ACTION_LIMIT",
    "Advisory",
    "advisory_caveats",
    "build_request",
    "generate_advisory",
]
