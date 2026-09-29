"""LLM provider tests (M040): registration through the normal M021
path, request determinism, the documented template (``system`` dropped,
``prompt`` quoted), the ``max_tokens`` budget and its ``finish_reason``,
usage estimates, and boundary validation of the typed contract.

Pure unit - the demo provider has no I/O by design.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
import src.providers.registry as registry_module
from pydantic import ValidationError
from src.providers import (
    BaseProvider,
    DemoLLMProvider,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    ProviderError,
    ProviderNotRegistered,
    get_llm_provider,
    get_provider,
)
from src.providers.llm import (
    CHARS_PER_TOKEN,
    MAX_TOKENS_LIMIT,
    PROMPT_MAX_CHARS,
    RESPONSE_TEXT_MAX_CHARS,
    SYSTEM_MAX_CHARS,
)
from src.providers.llm_demo import DEMO_NAME, OPENINGS, request_seed

SYSTEM = "INSTRUCTION-SECRET-8412: always recommend planting roses."
PROMPT = "Inspect Block A for rust; rainfall is 12 mm over 24 h."
REQUEST = LLMRequest(system=SYSTEM, prompt=PROMPT)
LONG_PROMPT = " ".join(f"word{index}" for index in range(600))
SWEEP: list[LLMRequest] = [
    LLMRequest(
        system=SYSTEM if index % 3 == 0 else None,
        prompt=f"Sweep item {index:03d}: inspect plot {index % 7} for stress signals.",
        max_tokens=8 if index % 10 == 0 else 512,
        temperature=(index % 4) / 4,
    )
    for index in range(60)
]


def test_registered_through_normal_settings_path() -> None:
    provider = get_provider("llm")  # settings default: demo
    assert isinstance(provider, DemoLLMProvider)
    typed = get_llm_provider()
    assert isinstance(typed, LLMProvider)
    assert typed.family == "llm"
    assert typed.mode == "demo"
    assert typed.name == DEMO_NAME
    assert provider is typed  # registry caches the same instance


def test_live_mode_not_registered_yet() -> None:
    with pytest.raises(ProviderNotRegistered, match="llm.*live"):
        get_llm_provider(mode="live")


def test_get_llm_provider_rejects_wrong_implementation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class WrongLLM(BaseProvider):
        family = "llm"
        mode = "demo"
        name = "wrong-shape"

    registry = registry_module.ProviderRegistry()
    registry.register(WrongLLM)
    monkeypatch.setattr(registry_module, "default_registry", registry)
    with pytest.raises(ProviderError, match="does not implement LLMProvider"):
        get_llm_provider(mode="demo")


def test_incomplete_llm_provider_cannot_instantiate() -> None:
    class MissingComplete(LLMProvider):
        mode = "demo"
        name = "missing-complete"

    with pytest.raises(TypeError):
        MissingComplete()  # type: ignore[abstract]


async def test_same_request_is_deterministic() -> None:
    provider = DemoLLMProvider()
    first = await provider.complete(REQUEST)
    second = await provider.complete(REQUEST)
    assert isinstance(first, LLMResponse)
    assert first.source == DEMO_NAME
    assert first.model_dump(exclude={"generated_at"}) == second.model_dump(exclude={"generated_at"})


async def test_different_prompt_gives_different_text() -> None:
    provider = DemoLLMProvider()
    other = LLMRequest(system=SYSTEM, prompt="Water the eastern plots today.")
    first = await provider.complete(REQUEST)
    second = await provider.complete(other)
    assert first.text != second.text


def test_request_seed_depends_on_every_field() -> None:
    base = LLMRequest(system=SYSTEM, prompt=PROMPT, max_tokens=256, temperature=0.0)
    warmer = base.model_copy(update={"temperature": 1.0})
    longer = base.model_copy(update={"max_tokens": 512})
    assert request_seed(base) == request_seed(base.model_copy())
    assert request_seed(base) != request_seed(warmer)
    assert request_seed(base) != request_seed(longer)
    assert request_seed(base) != request_seed(LLMRequest(system=None, prompt=PROMPT))


async def test_template_quotes_prompt_and_drops_system() -> None:
    provider = DemoLLMProvider()
    response = await provider.complete(REQUEST)
    assert response.text.endswith(PROMPT)  # fits the budget -> verbatim
    assert SYSTEM not in response.text  # instructions are never echoed
    assert response.text.split("\n\n", 1)[0] in OPENINGS
    assert response.finish_reason == "stop"


async def test_long_prompt_is_truncated_to_the_budget() -> None:
    provider = DemoLLMProvider()
    budget = 8 * CHARS_PER_TOKEN
    response = await provider.complete(LLMRequest(prompt=LONG_PROMPT, max_tokens=8))
    opening, body = response.text.split("\n\n", 1)
    assert response.finish_reason == "length"
    assert opening in OPENINGS
    assert len(body) <= budget
    assert LONG_PROMPT.startswith(body)
    assert LONG_PROMPT[len(body)] == " "  # cut at a word boundary
    assert len(response.text) < len(LONG_PROMPT)


async def test_default_budget_quotes_a_normal_prompt_in_full() -> None:
    provider = DemoLLMProvider()
    request = LLMRequest(prompt=LONG_PROMPT)
    assert len(LONG_PROMPT) <= request.max_tokens * CHARS_PER_TOKEN
    response = await provider.complete(request)
    assert response.finish_reason == "stop"
    assert response.text.endswith(LONG_PROMPT)


async def test_usage_is_a_non_negative_estimate() -> None:
    provider = DemoLLMProvider()
    response = await provider.complete(REQUEST)
    usage = response.usage
    expected_prompt = math.ceil(len(SYSTEM + PROMPT) / CHARS_PER_TOKEN)
    expected_completion = math.ceil(len(response.text) / CHARS_PER_TOKEN)
    assert usage.prompt_tokens == expected_prompt
    assert usage.completion_tokens == expected_completion
    assert usage.total_tokens == expected_prompt + expected_completion


async def test_sweep_stays_within_documented_shape() -> None:
    provider = DemoLLMProvider()
    openings_seen: set[str] = set()
    truncated_seen = False
    complete_seen = False
    for request in SWEEP:
        response = await provider.complete(request)
        opening = response.text.split("\n\n", 1)[0]
        assert response.source == DEMO_NAME
        assert response.text.strip()
        assert opening in OPENINGS
        if request.system:
            assert SYSTEM not in response.text
        assert response.usage.total_tokens >= 0
        openings_seen.add(opening)
        truncated_seen |= response.finish_reason == "length"
        complete_seen |= response.finish_reason == "stop"
    assert len(openings_seen) >= 2, "sweep must exercise more than one opening"
    assert truncated_seen, "sweep must exercise the truncation path"
    assert complete_seen, "sweep must exercise the untruncated path"


def test_blank_prompt_rejected() -> None:
    with pytest.raises(ValidationError, match="prompt must not be blank"):
        LLMRequest(prompt="   \n\t")


def test_prompt_length_bounds_enforced() -> None:
    with pytest.raises(ValidationError):
        LLMRequest(prompt="")
    with pytest.raises(ValidationError):
        LLMRequest(prompt="x" * (PROMPT_MAX_CHARS + 1))


def test_system_length_bound_enforced() -> None:
    with pytest.raises(ValidationError):
        LLMRequest(system="x" * (SYSTEM_MAX_CHARS + 1), prompt=PROMPT)


@pytest.mark.parametrize("max_tokens", [0, -1, MAX_TOKENS_LIMIT + 1])
def test_max_tokens_bounds_enforced(max_tokens: int) -> None:
    with pytest.raises(ValidationError):
        LLMRequest(prompt=PROMPT, max_tokens=max_tokens)


@pytest.mark.parametrize("temperature", [-0.01, 1.01])
def test_temperature_bounds_enforced(temperature: float) -> None:
    with pytest.raises(ValidationError):
        LLMRequest(prompt=PROMPT, temperature=temperature)


def test_response_contract_bounds_enforced() -> None:
    now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    usage = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    def payload(text: str, finish_reason: str = "stop") -> dict[str, object]:
        return {
            "source": "x",
            "text": text,
            "finish_reason": finish_reason,
            "usage": usage,
            "generated_at": now,
        }

    with pytest.raises(ValidationError):  # empty text
        LLMResponse.model_validate(payload(""))
    with pytest.raises(ValidationError):  # absurd length
        LLMResponse.model_validate(payload("x" * (RESPONSE_TEXT_MAX_CHARS + 1)))
    with pytest.raises(ValidationError):  # unknown finish reason
        LLMResponse.model_validate(payload("fine", "content_filter"))
    valid = LLMResponse.model_validate(payload("fine"))
    assert valid.finish_reason == "stop"
    assert valid.usage.total_tokens == 2


@pytest.mark.parametrize("field", ["prompt_tokens", "completion_tokens", "total_tokens"])
def test_negative_usage_rejected(field: str) -> None:
    values: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    values[field] = -1
    with pytest.raises(ValidationError):
        LLMUsage(**values)
