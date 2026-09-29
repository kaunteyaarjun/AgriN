"""Weather live provider tests (M024): Open-Meteo mapping, the WMO
condition table, the failure taxonomy (Unavailable vs ResponseInvalid),
client lifecycle, and settings-driven resolution.

Pure unit — every response comes from ``httpx.MockTransport``; no test
in this file touches the network (the real call happens only in the
manual live check recorded in the milestone notes).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import httpx
import pytest
from src.providers import (
    DemoWeatherProvider,
    LiveWeatherProvider,
    ProviderResponseInvalid,
    ProviderUnavailable,
    WeatherProvider,
    get_provider,
    get_weather_provider,
)
from src.providers.weather_live import (
    OPEN_METEO_URL,
    SOURCE_NAME,
    TIMEOUT_S,
    _condition,
)

NAIROBI = (-1.2921, 36.8219)

CANNED: dict[str, object] = {
    "latitude": -1.29,
    "longitude": 36.82,
    "elevation": 1795.0,
    "timezone": "Africa/Nairobi",
    "current": {
        "time": "2026-09-29T12:00",
        "interval": 900,
        "temperature_2m": 27.4,
        "relative_humidity_2m": 61.0,
        "precipitation": 0.6,
        "weather_code": 2,
        "wind_speed_10m": 13.5,
    },
}

Handler = Callable[[httpx.Request], httpx.Response]


def live_provider(handler: Handler) -> LiveWeatherProvider:
    """Provider wired to an offline MockTransport."""
    return LiveWeatherProvider(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def canned_handler(captured: dict[str, httpx.Request] | None = None) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        if captured is not None:
            captured["request"] = request
        return httpx.Response(200, json=CANNED)

    return handler


def error_handler(
    status: int, *, body: bytes = b"{}", media_type: str = "application/json"
) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=body, headers={"content-type": media_type})

    return handler


# ---------- registration / settings resolution ----------


async def test_live_registered_and_default_still_demo() -> None:
    from src.providers.registry import default_registry

    try:
        provider = get_provider("weather", mode="live")
        assert isinstance(provider, LiveWeatherProvider)
        assert isinstance(provider, WeatherProvider)
        assert provider.family == "weather"
        assert provider.mode == "live"
        assert provider.name == SOURCE_NAME
        assert get_weather_provider(mode="live") is provider  # registry caches one instance

        default = get_provider("weather")  # settings default: demo
        assert isinstance(default, DemoWeatherProvider)
        assert get_weather_provider().mode == "demo"
    finally:
        await default_registry.aclose_all()  # release the registry-built client


# ---------- request shape ----------


async def test_request_targets_open_meteo_with_expected_params() -> None:
    captured: dict[str, httpx.Request] = {}
    await live_provider(canned_handler(captured)).fetch(*NAIROBI)

    request = captured["request"]
    url = request.url
    assert f"{url.scheme}://{url.host}" in OPEN_METEO_URL
    assert url.path.endswith("/v1/forecast")
    assert float(url.params["latitude"]) == NAIROBI[0]
    assert float(url.params["longitude"]) == NAIROBI[1]
    assert url.params["timezone"] == "auto"
    assert "temperature_2m" in url.params["current"]
    assert "weather_code" in url.params["current"]
    assert "api_key" not in url.params  # keyless endpoint


# ---------- field mapping ----------


async def test_full_payload_maps_to_reading() -> None:
    reading = await live_provider(canned_handler()).fetch(*NAIROBI)

    assert reading.temperature_c == 27.4
    assert reading.humidity_pct == 61.0
    assert reading.rainfall_mm_24h == 0.6  # current-hour mm into the 24h slot (documented)
    assert reading.wind_speed_kmh == 13.5
    assert reading.condition == "partly_cloudy"  # weather_code 2
    assert reading.source == SOURCE_NAME
    now = datetime.now(UTC)
    assert reading.fetched_at.tzinfo is not None
    assert abs((now - reading.fetched_at).total_seconds()) < 60


async def test_missing_optional_current_fields_are_none() -> None:
    provider = live_provider(lambda request: httpx.Response(200, json={"current": {}}))
    reading = await provider.fetch(*NAIROBI)

    assert reading.temperature_c is None
    assert reading.humidity_pct is None
    assert reading.rainfall_mm_24h is None
    assert reading.wind_speed_kmh is None
    assert reading.condition is None  # no weather_code = no data, not a guess
    assert reading.source == SOURCE_NAME


async def test_null_weather_code_is_none_but_garbage_is_cloudy() -> None:
    null_code = await live_provider(
        lambda request: httpx.Response(200, json={"current": {"weather_code": None}})
    ).fetch(*NAIROBI)
    assert null_code.condition is None

    string_code = await live_provider(
        lambda request: httpx.Response(200, json={"current": {"weather_code": "2"}})
    ).fetch(*NAIROBI)
    assert string_code.condition == "cloudy"


async def test_non_numeric_values_become_none() -> None:
    provider = live_provider(
        lambda request: httpx.Response(
            200,
            json={
                "current": {
                    "temperature_2m": "27.4",
                    "relative_humidity_2m": None,
                    "precipitation": True,
                    "wind_speed_10m": 13.5,
                    "weather_code": 0,
                }
            },
        )
    )
    reading = await provider.fetch(*NAIROBI)
    assert reading.temperature_c is None  # string is not a number
    assert reading.humidity_pct is None
    assert reading.rainfall_mm_24h is None  # bool is not a number
    assert reading.wind_speed_kmh == 13.5
    assert reading.condition == "clear"


# ---------- WMO weather_code → condition table (spec: M024) ----------


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (0, "clear"),
        (1, "partly_cloudy"),
        (2, "partly_cloudy"),
        (3, "cloudy"),
        (45, "cloudy"),
        (48, "cloudy"),
        (51, "light_rain"),
        (56, "light_rain"),
        (61, "light_rain"),
        (67, "light_rain"),
        (80, "light_rain"),
        (82, "light_rain"),
        (71, "cloudy"),  # snow has no vocabulary value → cloudy
        (75, "cloudy"),
        (77, "cloudy"),
        (85, "cloudy"),
        (86, "cloudy"),
        (95, "thunderstorm"),
        (96, "thunderstorm"),
        (99, "thunderstorm"),
        (91, "cloudy"),  # unknown code
        (123, "cloudy"),
        (-1, "cloudy"),
        (True, "cloudy"),  # bool is not a code
        (False, "cloudy"),
        ("0", "cloudy"),  # wrong JSON type
        (None, None),  # absent = no data
    ],
)
def test_weather_code_table(code: object, expected: str | None) -> None:
    assert _condition(code) == expected


async def test_snow_code_end_to_end_maps_to_cloudy() -> None:
    provider = live_provider(
        lambda request: httpx.Response(200, json={"current": {"weather_code": 73}})
    )
    reading = await provider.fetch(*NAIROBI)
    assert reading.condition == "cloudy"


# ---------- failure taxonomy (M021 contract) ----------


async def test_timeout_maps_to_provider_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    with pytest.raises(ProviderUnavailable, match="timeout"):
        await live_provider(handler).fetch(*NAIROBI)


@pytest.mark.parametrize(
    ("error", "match"),
    [
        (httpx.ConnectError("connection refused"), "unreachable"),
        (httpx.ReadError("connection reset"), "unreachable"),
        (httpx.ConnectTimeout("connect timed out"), "timeout"),
    ],
)
async def test_transport_errors_map_to_provider_unavailable(
    error: httpx.TransportError, match: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    with pytest.raises(ProviderUnavailable, match=match):
        await live_provider(handler).fetch(*NAIROBI)


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
async def test_rate_limit_and_server_errors_are_unavailable(status: int) -> None:
    with pytest.raises(ProviderUnavailable, match=f"HTTP {status}"):
        await live_provider(error_handler(status)).fetch(*NAIROBI)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
async def test_other_client_errors_are_response_invalid(status: int) -> None:
    with pytest.raises(ProviderResponseInvalid, match=f"HTTP {status}"):
        await live_provider(error_handler(status)).fetch(*NAIROBI)


async def test_unparseable_body_is_response_invalid() -> None:
    provider = live_provider(error_handler(200, body=b"<html>nope</html>", media_type="text/html"))
    with pytest.raises(ProviderResponseInvalid, match="unparseable"):
        await provider.fetch(*NAIROBI)


@pytest.mark.parametrize(
    "payload",
    [
        ["not", "an", "object"],
        {"latitude": -1.29},
        {"current": [1, 2, 3]},
        {"current": "now"},
        {},
    ],
)
async def test_malformed_shapes_are_response_invalid(payload: object) -> None:
    provider = live_provider(lambda request: httpx.Response(200, json=payload))
    with pytest.raises(ProviderResponseInvalid):
        await provider.fetch(*NAIROBI)


async def test_no_raw_exception_escapes_the_contract() -> None:
    """Every failure mode surfaces as a ProviderError subclass."""
    with pytest.raises(ProviderUnavailable):
        await live_provider(error_handler(503)).fetch(*NAIROBI)
    with pytest.raises(ProviderResponseInvalid):
        await live_provider(error_handler(400)).fetch(*NAIROBI)
    with pytest.raises(ProviderUnavailable):

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

        await live_provider(handler).fetch(*NAIROBI)


# ---------- client lifecycle ----------


async def test_aclose_closes_owned_client() -> None:
    provider = LiveWeatherProvider()
    client = provider._client
    assert client.timeout.read == TIMEOUT_S
    assert not client.is_closed

    await provider.aclose()

    assert client.is_closed
    await provider.aclose()  # idempotent


async def test_aclose_closes_injected_client_too() -> None:
    provider = live_provider(canned_handler())
    await provider.fetch(*NAIROBI)
    await provider.aclose()
    assert provider._client.is_closed
