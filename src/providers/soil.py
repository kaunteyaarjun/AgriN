"""Soil family interface — follows the weather/satellite pattern (M028).

Defines the typed contract every soil provider must satisfy:
``SoilReading`` (validated at the boundary) and the abstract
``SoilProvider.fetch``. The demo implementation registers under
``("soil", "demo")``, the live one (M030) under ``("soil", "live")``;
ingestion (M029) consumes ``get_soil_provider().fetch(lat, lon)``.

Soil is an in-situ measurement at the farm's point — there is no
``captured_at`` (fetch time == observation time, like weather; unlike
satellite scenes). Payload ranges are deliberately unconstrained here
(consistent with the other families): documented demo ranges are
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


class SoilReading(BaseModel):
    """One upstream soil reading for a point. Payload fields optional —
    upstreams legitimately omit fields; ingestion folds what exists into
    the farm signal cache (M029)."""

    fetched_at: datetime
    source: str
    soil_moisture_pct: float | None = None
    ph: float | None = None
    soil_temperature_c: float | None = None
    nitrogen_kg_ha: float | None = None


class SoilProvider(BaseProvider):
    """Abstract soil source: fetch a reading for a WGS84 point."""

    family = "soil"

    @abstractmethod
    async def fetch(self, lat: float, lon: float) -> SoilReading:
        """Return a validated reading. Raise ``ProviderUnavailable`` /
        ``ProviderResponseInvalid`` on failure (never raw exceptions from
        upstreams — mapping is the implementation's job)."""


def get_soil_provider(*, mode: ProviderMode | None = None) -> SoilProvider:
    """Typed accessor — same lookup as ``get_provider``, no casts for callers."""
    provider = get_provider("soil", mode=mode)
    if not isinstance(provider, SoilProvider):
        raise ProviderError(
            f"Registered soil provider {provider!r} does not implement SoilProvider."
        )
    return provider
