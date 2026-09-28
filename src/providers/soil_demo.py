"""Soil demo provider (M028): deterministic, network-free readings.

Registered on the default registry under ``("soil", "demo")``, so the
default ``soil_provider = "demo"`` flag resolves to it through the
normal M021 path. Values derive from the shared sha256 point seed
(``_demo.point_seed``) — the same point always yields the same
reading, which is what makes the demo and its tests stable. Documented
ranges (tested): soil_moisture_pct 20.0–60.0, ph 5.5–7.5,
soil_temperature_c 12.0–28.0 (1 decimal), nitrogen_kg_ha 20–120
(integer).

Real upstreams (live soil API) land in M030 under ``("soil", "live")``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.providers._demo import check_wgs84, point_seed
from src.providers.registry import register
from src.providers.soil import SoilProvider, SoilReading

DEMO_NAME = "demo-soil-v1"


@register
class DemoSoilProvider(SoilProvider):
    """Synthetic soil reading for any WGS84 point. No I/O by design."""

    mode = "demo"
    name = DEMO_NAME

    async def fetch(self, lat: float, lon: float) -> SoilReading:
        check_wgs84(lat, lon)
        seed = point_seed(lat, lon)
        return SoilReading(
            fetched_at=datetime.now(UTC),
            source=self.name,
            soil_moisture_pct=round(20 + (seed % 401) / 10, 1),
            ph=round(5.5 + ((seed >> 8) % 21) / 10, 1),
            soil_temperature_c=round(12 + ((seed >> 16) % 161) / 10, 1),
            nitrogen_kg_ha=float(20 + (seed >> 24) % 101),
        )
