"""Weather live provider (M024): Open-Meteo forecast API.

First network-backed provider in the platform. Registered under
``("weather", "live")``; default settings stay ``demo`` — switch with
``weather_provider=live`` (or ``get_weather_provider(mode="live")``).

Request (keyless, free tier)::

    GET https://api.open-meteo.com/v1/forecast
        ?latitude=..&longitude=..
        &current=temperature_2m,relative_humidity_2m,precipitation,
                 weather_code,wind_speed_10m
        &timezone=auto

Mapping notes (spec: M024): ``precipitation`` is the *current hour*
in mm but lands in the contract's ``rainfall_mm_24h`` slot — the only
precipitation field the contract has; the raw value travels in the
signals doc and M031 owns the semantics. ``weather_code`` (WMO)
folds into the 5-value condition vocabulary via :data:`WEATHER_CODES`
(snow maps to ``cloudy`` — the vocabulary has no snow value).

Failure taxonomy: transport errors/timeouts/5xx/429 →
``ProviderUnavailable``; other 4xx and malformed bodies →
``ProviderResponseInvalid`` (never a raw exception — M021 contract).

Client ownership: the provider owns one pooled ``httpx.AsyncClient``
(10 s timeout) unless one is injected (tests/MockTransport, live
unreachable checks); ``aclose()`` closes it.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from src.providers.errors import ProviderResponseInvalid, ProviderUnavailable
from src.providers.registry import register
from src.providers.weather import WeatherProvider, WeatherReading

logger = logging.getLogger("agrin.providers.weather_live")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_S = 10.0
SOURCE_NAME = "open-meteo-v1"  # source label stored on readings

CURRENT_FIELDS = "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"

# WMO weather code → contract condition vocabulary (spec: M024).
# Snow codes (71-77, 85-86) fold to "cloudy"; unknown codes → "cloudy".
WEATHER_CODES: dict[int, str] = {
    0: "clear",
    1: "partly_cloudy",
    2: "partly_cloudy",
    3: "cloudy",
    45: "cloudy",
    48: "cloudy",
    95: "thunderstorm",
    96: "thunderstorm",
    99: "thunderstorm",
}


def _condition(weather_code: object) -> str | None:
    """Fold a WMO code into the 5-value condition vocabulary.

    An absent/null code is *no data* → ``None`` (the contract's optional
    fields); a present-but-unreadable or unknown code → ``cloudy``.
    """
    if weather_code is None:
        return None
    if isinstance(weather_code, bool) or not isinstance(weather_code, int):
        return "cloudy"
    if weather_code in WEATHER_CODES:
        return WEATHER_CODES[weather_code]
    if 51 <= weather_code <= 67 or 80 <= weather_code <= 82:
        return "light_rain"
    if 95 <= weather_code <= 99:
        return "thunderstorm"
    # 71-77 / 85-86 (snow) and anything unknown land here
    return "cloudy"


@register
class LiveWeatherProvider(WeatherProvider):
    """Open-Meteo-backed weather source for any WGS84 point."""

    mode = "live"
    name = SOURCE_NAME

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        base_url: str = OPEN_METEO_URL,
    ) -> None:
        self._base_url = base_url
        self._client = client if client is not None else httpx.AsyncClient(timeout=TIMEOUT_S)

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        params: dict[str, str | float] = {
            "latitude": lat,
            "longitude": lon,
            "current": CURRENT_FIELDS,
            "timezone": "auto",
        }
        try:
            response = await self._client.get(self._base_url, params=params)
        except httpx.TimeoutException as exc:
            logger.warning("open-meteo timeout: %s", exc)
            raise ProviderUnavailable(f"open-meteo timeout: {exc}") from exc
        except httpx.TransportError as exc:
            logger.warning("open-meteo transport error: %s", exc)
            raise ProviderUnavailable(f"open-meteo unreachable: {exc}") from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise ProviderUnavailable(f"open-meteo HTTP {response.status_code}")
        if response.status_code != 200:
            raise ProviderResponseInvalid(f"open-meteo HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseInvalid("open-meteo returned unparseable body") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("current"), dict):
            raise ProviderResponseInvalid("open-meteo response missing 'current' object")
        current: dict[str, Any] = payload["current"]

        return WeatherReading(
            fetched_at=datetime.now(UTC),
            source=self.name,
            temperature_c=_as_float(current.get("temperature_2m")),
            humidity_pct=_as_float(current.get("relative_humidity_2m")),
            rainfall_mm_24h=_as_float(current.get("precipitation")),
            wind_speed_kmh=_as_float(current.get("wind_speed_10m")),
            condition=_condition(current.get("weather_code")),
        )

    async def aclose(self) -> None:
        await self._client.aclose()


def _as_float(value: object) -> float | None:
    """Numbers arrive as JSON ints/floats; anything else → None."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
