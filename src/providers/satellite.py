"""Satellite family interface — follows the M021 weather pattern (M025).

Defines the typed contract every satellite provider must satisfy:
``SatelliteReading`` (validated at the boundary) and the abstract
``SatelliteProvider.fetch``. The demo implementation registers under
``("satellite", "demo")``, the live one (M027) under
``("satellite", "live")``; ingestion (M026) consumes
``get_satellite_provider().fetch(lat, lon)``.

``captured_at`` distinguishes overpass time from fetch time — a scene
observed earlier is still the latest available; the demo sets it equal
to ``fetched_at``. Payload ranges are deliberately unconstrained here
(consistent with ``WeatherReading``): documented demo ranges are
test-enforced, quality policy lands in M031.
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime

from pydantic import BaseModel

from src.core.config import ProviderMode
from src.providers.base import BaseProvider
from src.providers.errors import ProviderError
from src.providers.registry import get_provider


class SatelliteReading(BaseModel):
    """One upstream satellite scene for a point. Payload fields optional —
    cloud-covered scenes may omit NDVI; ingestion folds what exists into
    the farm signal cache (M026)."""

    fetched_at: datetime
    source: str
    ndvi: float | None = None
    cloud_cover_pct: float | None = None
    captured_at: datetime | None = None


class SatelliteProvider(BaseProvider):
    """Abstract satellite source: fetch the latest scene for a WGS84 point."""

    family = "satellite"

    @abstractmethod
    async def fetch(self, lat: float, lon: float) -> SatelliteReading:
        """Return a validated reading. Raise ``ProviderUnavailable`` /
        ``ProviderResponseInvalid`` on failure (never raw exceptions from
        upstreams — mapping is the implementation's job)."""


def get_satellite_provider(*, mode: ProviderMode | None = None) -> SatelliteProvider:
    """Typed accessor — same lookup as ``get_provider``, no casts for callers."""
    provider = get_provider("satellite", mode=mode)
    if not isinstance(provider, SatelliteProvider):
        raise ProviderError(
            f"Registered satellite provider {provider!r} does not implement SatelliteProvider."
        )
    return provider
