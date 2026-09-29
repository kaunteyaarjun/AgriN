"""AI advisory generation (M041): decision -> prompt -> validated text.

The seam between the structured analysis stack (M032-M039) and the LLM
provider family (M040): prompt construction is pure and lives here, the
provider call is the only I/O, and the output policy (what counts as a
usable advisory) is applied before anything is returned.

Two rules this module exists to keep:
- **the M040 split** - instructions go in ``system``, every
  farmer-visible fact goes in ``prompt``, so a templated demo (which
  renders only ``prompt``) can never quote instructions as advice;
- **honesty is never delegated** - data gaps travel twice: as M034's
  data-quality actions inside the facts, and as ``Advisory.caveats``,
  which M041 appends itself. A model may repeat them; it cannot drop
  them.

M043 (endpoint) and M044 (what-if re-run) both call
``generate_advisory``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Final

from pydantic import BaseModel

from src.engines import DISEASE_VERDICTS, FarmDecision
from src.providers import LLMProvider, LLMRequest, get_llm_provider
from src.providers.errors import ProviderResponseInvalid
from src.providers.llm import FinishReason

ADVISORY_SYSTEM: Final[str] = (
    "You are an agronomist writing a short advisory for a smallholder farmer. "
    "Write 3-5 sentences (at most 150 words) in plain, practical language. "
    "Use only the facts given in the request: never invent numbers, crops, plots, "
    "diseases or dates, and never contradict the listed actions. "
    "Lead with the single most important action, in the order it is listed. "
    "Output plain text only: no markdown, no headings, no bullet points, "
    "no greeting and no sign-off."
)
"""Instructions only - never a fact. M041 checks that none of this text
comes back in the answer (a model echoing instructions as advice)."""

ADVISORY_MAX_CHARS: Final[int] = 4_000
"""Sanity cap on returned text. The model is told <= 150 words; anything
past this cap means it ignored its instructions, which is an unusable
answer, not a long one."""

PROMPT_ACTION_LIMIT: Final[int] = 15
"""How many actions are spelled out in the prompt. Keeps a 100-action
farm inside ``PROMPT_MAX_CHARS`` and inside the demo's
``max_tokens * 4`` budget, so demo mode never truncates an advisory."""


class Advisory(BaseModel):
    """One generated advisory plus the caveats M041 guarantees.

    Built only by :func:`generate_advisory`, which applies the output
    policy (``text`` is stripped, non-empty and within
    ``ADVISORY_MAX_CHARS``); the model itself stays a permissive DTO,
    the way ``FarmDecision`` is.
    """

    farm_id: uuid.UUID
    stance: str
    text: str
    caveats: list[str]
    source: str
    finish_reason: FinishReason
    generated_at: datetime

    @property
    def rendered(self) -> str:
        """Plain-text form: the advisory body followed by its caveats."""
        return "\n\n".join([self.text, *self.caveats])


def advisory_caveats(decision: FarmDecision) -> list[str]:
    """The data-quality caveats M041 appends outside the model's
    control. Order is fixed: staleness first, then blind plots."""
    caveats: list[str] = []
    if decision.stale_families:
        families = ", ".join(decision.stale_families)
        caveats.append(
            f"Stale signals: {families} readings are past their freshness "
            "window and may no longer reflect conditions on the ground."
        )
    if decision.plots_with_unknown_factors:
        count = decision.plots_with_unknown_factors
        total = decision.plot_count
        if count == 1:
            caveats.append(
                f"1 of {total} plots has an unknown health factor: that reading "
                "is incomplete and must not be read as confirmed healthy."
            )
        else:
            caveats.append(
                f"{count} of {total} plots have unknown health factors: those "
                "readings are incomplete and must not be read as confirmed healthy."
            )
    return caveats


def build_request(decision: FarmDecision) -> LLMRequest:
    """Render a decision into one completion request. Pure and
    deterministic: facts are copied in the decision's own order, never
    re-derived, and no clock is read."""
    shown = decision.actions[:PROMPT_ACTION_LIMIT]
    lines = [
        f"Farm {decision.farm_id}",
        f"Stance: {decision.stance}",
        f"Health level: {decision.health_level}",
        f"Risk: {decision.risk_score}/100 ({decision.risk_band})",
        f"Plots: {decision.plot_count}",
        "Disease verdicts (plots): "
        + ", ".join(
            f"{decision.disease_verdicts.get(verdict, 0)} {verdict}" for verdict in DISEASE_VERDICTS
        ),
        f"Actions ({len(shown)} of {len(decision.actions)}, in priority order):",
    ]
    for position, action in enumerate(shown, start=1):
        lines.append(f"  {position}. [{action.priority}] {action.title}: {action.detail}")
    if len(decision.actions) > len(shown):
        lines.append(f"  ... and {len(decision.actions) - len(shown)} more actions not shown")
    return LLMRequest(system=ADVISORY_SYSTEM, prompt="\n".join(lines))


async def generate_advisory(
    decision: FarmDecision,
    *,
    provider: LLMProvider | None = None,
) -> Advisory:
    """Build the prompt, ask the provider, validate the answer.

    Blank text, over-length text and instruction echo all raise
    ``ProviderResponseInvalid`` (the M021 taxonomy, so M043 has one
    error path for an unusable upstream answer); any other
    ``ProviderError`` from the provider propagates untouched.
    """
    active = provider if provider is not None else get_llm_provider()
    request = build_request(decision)
    response = await active.complete(request)

    text = response.text.strip()
    if not text:
        raise ProviderResponseInvalid("advisory provider returned empty text")
    if len(text) > ADVISORY_MAX_CHARS:
        raise ProviderResponseInvalid(
            f"advisory text is {len(text)} characters, over the {ADVISORY_MAX_CHARS} limit"
        )
    if ADVISORY_SYSTEM in text:
        raise ProviderResponseInvalid("advisory text repeats the system instructions")

    return Advisory(
        farm_id=decision.farm_id,
        stance=decision.stance,
        text=text,
        caveats=advisory_caveats(decision),
        source=response.source,
        finish_reason=response.finish_reason,
        generated_at=response.generated_at,
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
