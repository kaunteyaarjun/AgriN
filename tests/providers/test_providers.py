"""Provider pattern tests (M021): registry behavior, base metadata
validation, the Weather reference interface, and settings-driven mode
resolution.

Pure unit — no DB, no network, no app state. Every test that would
touch the process-wide registry monkeypatches ``default_registry`` with
a fresh local one (house rule: never pollute shared registries; a
later milestone's import must not collide with these tests).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest
import src.providers.registry as registry_module
from pydantic import ValidationError
from src.providers import (
    KNOWN_FAMILIES,
    BaseProvider,
    ProviderError,
    ProviderNotRegistered,
    ProviderRegistry,
    ProviderResponseInvalid,
    ProviderUnavailable,
    WeatherProvider,
    WeatherReading,
    get_provider,
    get_weather_provider,
)

NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


class DemoWeather(WeatherProvider):
    """Compliant fake: closable, returns a fixed reading."""

    mode = "demo"
    name = "fake-weather-demo"

    def __init__(self) -> None:
        self.closed = False

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        return WeatherReading(
            fetched_at=NOW, source=self.name, temperature_c=21.5, condition="clear"
        )

    async def aclose(self) -> None:
        self.closed = True


class LiveWeather(WeatherProvider):
    mode = "live"
    name = "fake-weather-live"

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        raise ProviderUnavailable("upstream down")


class WrongWeather(BaseProvider):
    """Claims family=weather but does not implement WeatherProvider."""

    family = "weather"
    mode = "demo"
    name = "wrong-shape"


# ---------- registry basics (local registries only) ----------


async def test_register_and_get_caches_one_instance() -> None:
    registry = ProviderRegistry()
    registry.register(DemoWeather)
    first = registry.get("weather", "demo")
    second = registry.get("weather", "demo")
    assert first is second
    assert isinstance(first, WeatherProvider)
    reading = await first.fetch(-1.3, 36.8)
    assert reading.temperature_c == 21.5
    assert reading.source == "fake-weather-demo"


def test_duplicate_family_mode_rejected() -> None:
    registry = ProviderRegistry()
    registry.register(DemoWeather)
    with pytest.raises(ProviderError, match="already registered"):
        registry.register(DemoWeather)


def test_metadata_validation() -> None:
    registry = ProviderRegistry()

    class BadFamily(BaseProvider):
        family = "bogus"
        mode: ClassVar[Any] = "demo"
        name = "x"

    class BadMode(BaseProvider):
        family = "weather"
        mode: ClassVar[Any] = "staging"
        name = "x"

    class BadName(BaseProvider):
        family = "weather"
        mode: ClassVar[Any] = "demo"
        name = "   "

    for bad in (BadFamily, BadMode, BadName):
        with pytest.raises(ProviderError):
            registry.register(bad)


def test_unknown_family_get_names_known_families() -> None:
    registry = ProviderRegistry()
    with pytest.raises(ProviderNotRegistered) as exc:
        registry.get("weather", "demo")
    for family in KNOWN_FAMILIES:
        assert family in str(exc.value)


def test_unregistered_mode_lists_what_exists() -> None:
    registry = ProviderRegistry()
    registry.register(DemoWeather)
    with pytest.raises(ProviderNotRegistered) as exc:
        registry.get("weather", "live")
    message = str(exc.value)
    assert "weather/demo" in message
    assert "mode='live'" in message


def test_registry_instances_are_isolated() -> None:
    a, b = ProviderRegistry(), ProviderRegistry()
    a.register(DemoWeather)
    assert isinstance(a.get("weather", "demo"), DemoWeather)
    with pytest.raises(ProviderNotRegistered):
        b.get("weather", "demo")


# ---------- settings-driven resolution (get_provider) ----------


def test_get_provider_defaults_to_settings_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ProviderRegistry()
    registry.register(DemoWeather)
    registry.register(LiveWeather)
    monkeypatch.setattr(registry_module, "default_registry", registry)
    monkeypatch.setattr(
        registry_module,
        "get_settings",
        lambda: SimpleNamespace(weather_provider="live"),
    )

    assert get_provider("weather").mode == "live"  # settings picks live
    assert get_provider("weather", mode="demo").mode == "demo"  # explicit wins


def test_get_provider_unknown_family_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(registry_module, "get_settings", lambda: SimpleNamespace())
    with pytest.raises(ProviderNotRegistered, match="Unknown provider family"):
        get_provider("bogus")
    # explicit mode still can't save an unknown family
    with pytest.raises(ProviderNotRegistered, match="Known families"):
        get_provider("bogus", mode="demo")


# ---------- weather reference interface ----------


def test_incomplete_weather_provider_cannot_instantiate() -> None:
    class MissingFetch(WeatherProvider):
        mode = "demo"
        name = "missing-fetch"

    with pytest.raises(TypeError):
        MissingFetch()  # type: ignore[abstract]


async def test_get_weather_provider_typed_round_trip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ProviderRegistry()
    registry.register(DemoWeather)
    monkeypatch.setattr(registry_module, "default_registry", registry)

    provider = get_weather_provider(mode="demo")
    assert isinstance(provider, WeatherProvider)
    reading = await provider.fetch(-1.3, 36.8)
    assert reading == WeatherReading(
        fetched_at=NOW,
        source="fake-weather-demo",
        temperature_c=21.5,
        condition="clear",
    )


def test_get_weather_provider_rejects_wrong_implementation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ProviderRegistry()
    registry.register(WrongWeather)
    monkeypatch.setattr(registry_module, "default_registry", registry)

    with pytest.raises(ProviderError, match="does not implement WeatherProvider"):
        get_weather_provider(mode="demo")


def test_weather_reading_contract() -> None:
    reading = WeatherReading(fetched_at=NOW, source="x")
    assert reading.temperature_c is None  # upstreams may omit fields
    assert reading.condition is None
    with pytest.raises(ValidationError):
        WeatherReading.model_validate({"source": "x"})  # fetched_at required
    with pytest.raises(ValidationError):
        WeatherReading.model_validate({"fetched_at": NOW})  # source required


# ---------- lifecycle ----------


async def test_aclose_all_closes_and_forces_reconstruction() -> None:
    registry = ProviderRegistry()
    registry.register(DemoWeather)
    instance = registry.get("weather", "demo")
    assert isinstance(instance, DemoWeather)

    await registry.aclose_all()

    assert instance.closed is True
    rebuilt = registry.get("weather", "demo")
    assert rebuilt is not instance  # cache was cleared


async def test_aclose_all_on_empty_registry_is_a_noop() -> None:
    await ProviderRegistry().aclose_all()


def test_error_hierarchy_and_repr() -> None:
    assert issubclass(ProviderNotRegistered, ProviderError)
    assert issubclass(ProviderUnavailable, ProviderError)
    assert issubclass(ProviderResponseInvalid, ProviderError)
    provider = DemoWeather()
    text = repr(provider)
    assert "DemoWeather" in text
    assert "weather" in text
    assert "demo" in text
