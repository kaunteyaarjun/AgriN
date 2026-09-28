"""Satellite/NDVI demo provider (M025): deterministic, network-free scenes.

Registered on the default registry under ``("satellite", "demo")``, so the
default ``satellite_provider = "demo"`` flag resolves to it through the
normal M021 path. Values derive from a sha256 seed of the coordinates
(4-decimal precision) — the same point always yields the same scene,
which is what makes the demo and its tests stable. Documented ranges
(tested): ndvi 0.10–0.90 (2 decimals), cloud_cover_pct 0–100 (step 1),
``captured_at == fetched_at`` (fresh overpass).

Real upstreams (live NDVI API) land in M027 under ``("satellite",
"live")``.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from src.providers.registry import register
from src.providers.satellite import SatelliteProvider, SatelliteReading

DEMO_NAME = "demo-satellite-v1"


def _seed(lat: float, lon: float) -> int:
    """Stable 64-bit seed per point (4-decimal ≈ 11 m precision)."""
    digest = hashlib.sha256(f"{lat:.4f},{lon:.4f}".encode()).hexdigest()
    return int(digest[:16], 16)


@register
class DemoSatelliteProvider(SatelliteProvider):
    """Synthetic NDVI scene for any WGS84 point. No I/O by design."""

    mode = "demo"
    name = DEMO_NAME

    async def fetch(self, lat: float, lon: float) -> SatelliteReading:
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"coordinates out of WGS84 bounds: lat={lat}, lon={lon}")
        seed = _seed(lat, lon)
        now = datetime.now(UTC)
        return SatelliteReading(
            fetched_at=now,
            captured_at=now,  # demo scenes are always "just overflown"
            source=self.name,
            ndvi=round(0.10 + (seed % 81) / 100, 2),
            cloud_cover_pct=float((seed >> 8) % 101),
        )
