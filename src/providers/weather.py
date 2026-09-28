"""Weather family interface — the reference implementation of M021's pattern.

Defines the typed contract every weather provider must satisfy:
``WeatherReading`` (validated at the boundary) and the abstract
``WeatherProvider.fetch``. M022 registers the demo implementation under
``("weather", "demo")``, M024 the live one under ``("weather", "live")``;
ingestion (M023) consumes ``get_weather_provider().fetch(lat, lon)``.

Satellite/soil/disease/LLM families follow this same shape in their own
milestones (M025/M028/M036/M040) — no speculative interfaces here.
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime

from pydantic import BaseModel

from src.core.config import ProviderMode
from src.providers.base import BaseProvider
from src.providers.errors import ProviderError
from src.providers.registry import get_provider


class WeatherReading(BaseModel):
    """One upstream weather observation for a point. All values optional —
    upstreams legitimately omit fields; ingestion folds what exists into
    the farm signal cache (M023)."""

    fetched_at: datetime
    source: str
    temperature_c: float | None = None
    humidity_pct: float | None = None
    rainfall_mm_24h: float | None = None
    wind_speed_kmh: float | None = None
    condition: str | None = None


class WeatherProvider(BaseProvider):
    """Abstract weather source: fetch a reading for a WGS84 point."""

    family = "weather"

    @abstractmethod
    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        """Return a validated reading. Raise ``ProviderUnavailable`` /
        ``ProviderResponseInvalid`` on failure (never raw exceptions from
        upstreams — mapping is the implementation's job)."""


def get_weather_provider(*, mode: ProviderMode | None = None) -> WeatherProvider:
    """Typed accessor — same lookup as ``get_provider``, no casts for callers."""
    provider = get_provider("weather", mode=mode)
    if not isinstance(provider, WeatherProvider):
        raise ProviderError(
            f"Registered weather provider {provider!r} does not implement WeatherProvider."
        )
    return provider
