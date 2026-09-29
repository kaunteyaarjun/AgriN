"""Advisory generation tests (M041): prompt rendering (verbatim facts,
bounded action list, the M040 system/prompt split), M041-owned caveats,
the end-to-end default (demo) path, and the output policy.

Pure unit - no DB, no network, no clock.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from src.ai import (
    ADVISORY_MAX_CHARS,
    ADVISORY_SYSTEM,
    PROMPT_ACTION_LIMIT,
    Advisory,
    advisory_caveats,
    build_request,
    generate_advisory,
)
from src.engines import DecisionAction, FarmDecision
from src.providers import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderError,
    ProviderResponseInvalid,
    ProviderUnavailable,
)
from src.providers.llm import CHARS_PER_TOKEN, PROMPT_MAX_CHARS, SYSTEM_MAX_CHARS
from src.providers.llm_demo import DEMO_NAME, OPENINGS

FARM_ID = uuid.UUID("00000000-0000-0000-0000-00000000f00d")
FIXED_AT = datetime(2026, 9, 30, 8, 0, 0, tzinfo=UTC)


def _action(position: int, *, priority: str = "soon") -> DecisionAction:
    return DecisionAction(
        code=f"action_{position}",
        category="irrigation",
        priority=priority,
        title=f"Action {position} on Plot {position}",
        detail=f"Evidence line {position}: soil moisture measured at {position}%.",
        origin="recommendation",
        plot_id=uuid.uuid4(),
        plot_name=f"Plot {position}",
    )


def _decision(
    *,
    actions: list[DecisionAction] | None = None,
    stale_families: list[str] | None = None,
    plots_with_unknown: int = 0,
    plot_count: int = 4,
    stance: str = "monitor",
) -> FarmDecision:
    items = actions if actions is not None else [_action(1, priority="urgent"), _action(2)]
    return FarmDecision(
        farm_id=FARM_ID,
        stance=stance,
        health_level="watch",
        risk_score=62,
        risk_band="high" if stance == "act_now" else "moderate",
        disease_verdicts={"not_detected": 2, "uncertain": 1, "suspected": 0, "detected": 1},
        actions=items,
        action_counts={"urgent": 0, "soon": 0, "routine": 0},
        stale_families=stale_families if stale_families is not None else [],
        plots_with_unknown_factors=plots_with_unknown,
        plot_count=plot_count,
        computed_at=FIXED_AT,
    )


class StubLLM(LLMProvider):
    """Injected provider: fixed text or a fixed failure, records the
    request it was asked to complete."""

    mode = "demo"
    name = "stub-llm"

    def __init__(self, text: str = "Advisory body.", *, error: ProviderError | None = None) -> None:
        self._text = text
        self._error = error
        self.seen: LLMRequest | None = None

    async def complete(self, request: LLMRequest) -> LLMResponse:
        self.seen = request
        if self._error is not None:
            raise self._error
        return LLMResponse(
            source=self.name,
            text=self._text,
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            generated_at=FIXED_AT,
        )


# ---------- prompt construction ----------


def test_build_request_is_deterministic() -> None:
    decision = _decision()
    assert build_request(decision).model_dump() == build_request(decision).model_dump()


def test_system_holds_instructions_and_prompt_holds_facts() -> None:
    request = build_request(_decision())
    assert request.system == ADVISORY_SYSTEM
    assert ADVISORY_SYSTEM not in request.prompt  # instructions never leak into facts
    assert "You are an agronomist" not in request.prompt
    assert "Risk: 62/100 (moderate)" in request.prompt
    assert "Stance: monitor" in request.prompt
    assert "Health level: watch" in request.prompt
    assert "Plots: 4" in request.prompt


def test_action_evidence_is_copied_verbatim() -> None:
    actions = [_action(1, priority="urgent"), _action(2), _action(3, priority="routine")]
    prompt = build_request(_decision(actions=actions)).prompt
    for action in actions:
        assert f"[{action.priority}] {action.title}: {action.detail}" in prompt


def test_action_order_follows_the_decision() -> None:
    actions = [_action(3, priority="routine"), _action(1, priority="urgent"), _action(2)]
    prompt = build_request(_decision(actions=actions)).prompt
    assert prompt.index("Action 3 on Plot 3") < prompt.index("Action 1 on Plot 1")
    assert prompt.index("Action 1 on Plot 1") < prompt.index("Action 2 on Plot 2")


def test_actions_are_capped_with_a_remainder_line() -> None:
    actions = [_action(position) for position in range(100)]
    prompt = build_request(_decision(actions=actions)).prompt
    assert f"Actions ({PROMPT_ACTION_LIMIT} of 100, in priority order):" in prompt
    assert "... and 85 more actions not shown" in prompt
    assert "Action 16 on Plot 16" not in prompt
    assert len(prompt) <= PROMPT_MAX_CHARS


def test_prompt_and_system_stay_inside_the_m040_bounds() -> None:
    decision = _decision(actions=[_action(position) for position in range(100)])
    request = build_request(decision)
    assert len(request.system or "") <= SYSTEM_MAX_CHARS
    assert len(request.prompt) <= PROMPT_MAX_CHARS
    assert len(request.prompt) <= request.max_tokens * CHARS_PER_TOKEN  # demo budget


def test_verdict_counts_are_echoed_in_engine_order() -> None:
    prompt = build_request(_decision()).prompt
    assert (
        "Disease verdicts (plots): 2 not_detected, 1 uncertain, 0 suspected, 1 detected" in prompt
    )


# ---------- caveats ----------


def test_clean_decision_has_no_caveats() -> None:
    decision = _decision()
    assert advisory_caveats(decision) == []
    advisory = Advisory(
        farm_id=FARM_ID,
        stance=decision.stance,
        text="Body.",
        caveats=advisory_caveats(decision),
        source="stub-llm",
        finish_reason="stop",
        generated_at=FIXED_AT,
    )
    assert advisory.rendered == "Body."


def test_stale_families_and_blind_plots_each_get_one_caveat() -> None:
    decision = _decision(stale_families=["weather", "soil"], plots_with_unknown=2, plot_count=5)
    caveats = advisory_caveats(decision)
    assert len(caveats) == 2
    assert "weather, soil" in caveats[0]
    assert "freshness window" in caveats[0]
    assert "2 of 5 plots" in caveats[1]
    assert "must not be read as confirmed healthy" in caveats[1]
    advisory = Advisory(
        farm_id=FARM_ID,
        stance=decision.stance,
        text="Body.",
        caveats=caveats,
        source="stub-llm",
        finish_reason="stop",
        generated_at=FIXED_AT,
    )
    assert advisory.rendered == "Body.\n\n" + "\n\n".join(caveats)


def test_single_blind_plot_is_singular() -> None:
    (caveat,) = advisory_caveats(_decision(plots_with_unknown=1, plot_count=3))
    assert "1 of 3 plots has an unknown health factor" in caveat


# ---------- generation ----------


async def test_end_to_end_through_the_default_demo_provider() -> None:
    decision = _decision()
    advisory = await generate_advisory(decision)
    assert advisory.source == DEMO_NAME
    assert advisory.finish_reason == "stop"
    assert advisory.farm_id == FARM_ID
    assert advisory.stance == decision.stance
    assert advisory.text.split("\n\n", 1)[0] in OPENINGS
    assert advisory.text.endswith(build_request(decision).prompt)
    assert advisory.generated_at.tzinfo is not None


async def test_injected_provider_is_used_and_recorded() -> None:
    stub = StubLLM(text="  Trimmed advisory.  ")
    advisory = await generate_advisory(_decision(), provider=stub)
    assert advisory.text == "Trimmed advisory."  # stripped
    assert advisory.source == "stub-llm"
    assert advisory.generated_at == FIXED_AT  # M041 reads no clock itself
    assert stub.seen is not None
    assert stub.seen.system == ADVISORY_SYSTEM


async def test_blank_text_is_rejected() -> None:
    # A fully empty response can never reach M041: ``LLMResponse.text``
    # is min_length=1 (M040 boundary). Whitespace is what slips through
    # and must be caught here, after stripping.
    with pytest.raises(ProviderResponseInvalid, match="empty text"):
        await generate_advisory(_decision(), provider=StubLLM(text="   \n\t  "))


async def test_over_length_text_is_rejected() -> None:
    with pytest.raises(ProviderResponseInvalid, match="over the .* limit"):
        await generate_advisory(_decision(), provider=StubLLM(text="x" * (ADVISORY_MAX_CHARS + 1)))


async def test_instruction_echo_is_rejected() -> None:
    with pytest.raises(ProviderResponseInvalid, match="repeats the system instructions"):
        await generate_advisory(_decision(), provider=StubLLM(text=ADVISORY_SYSTEM))


async def test_provider_errors_propagate_unchanged() -> None:
    failure = ProviderUnavailable("upstream down")
    with pytest.raises(ProviderUnavailable, match="upstream down") as caught:
        await generate_advisory(_decision(), provider=StubLLM(error=failure))
    assert caught.value is failure


async def test_caveats_are_attached_even_when_the_model_omits_them() -> None:
    decision = _decision(stale_families=["satellite"], plots_with_unknown=1, plot_count=2)
    advisory = await generate_advisory(decision, provider=StubLLM(text="No mention of gaps."))
    assert len(advisory.caveats) == 2
    assert all(caveat not in advisory.text for caveat in advisory.caveats)
