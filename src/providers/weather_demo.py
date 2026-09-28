"""Weather demo provider (M022): deterministic, network-free weather.

Registered on the default registry under ``("weather", "demo")``, so the
default ``weather_provider = "demo"`` flag resolves to it through the
normal M021 path. Values derive from a sha256 seed of the coordinates
(4-decimal precision) — the same point always yields the same reading,
which is what makes the demo and its tests stable. Documented ranges
(tested): temperature 18.0–32.9 C, humidity 40–90 %, rainfall
0.0–11.9 mm/24h, wind 1–45 km/h, condition from a 5-value vocabulary.

Real upstreams (Open-Meteo) land in M024 under ``("weather", "live")``.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from src.providers.registry import register
from src.providers.weather import WeatherProvider, WeatherReading

DEMO_NAME = "demo-weather-v1"

CONDITIONS: tuple[str, ...] = (
    "clear",
    "partly_cloudy",
    "cloudy",
    "light_rain",
    "thunderstorm",
)


def _seed(lat: float, lon: float) -> int:
    """Stable 64-bit seed per point (4-decimal ≈ 11 m precision)."""
    digest = hashlib.sha256(f"{lat:.4f},{lon:.4f}".encode()).hexdigest()
    return int(digest[:16], 16)


@register
class DemoWeatherProvider(WeatherProvider):
    """Synthetic weather for any WGS84 point. No I/O by design."""

    mode = "demo"
    name = DEMO_NAME

    async def fetch(self, lat: float, lon: float) -> WeatherReading:
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"coordinates out of WGS84 bounds: lat={lat}, lon={lon}")
        seed = _seed(lat, lon)
        return WeatherReading(
            fetched_at=datetime.now(UTC),
            source=self.name,
            temperature_c=round(18 + (seed % 150) / 10, 1),
            humidity_pct=float(40 + (seed >> 8) % 51),
            rainfall_mm_24h=round(((seed >> 16) % 120) / 10, 1),
            wind_speed_kmh=float(1 + (seed >> 24) % 45),
            condition=CONDITIONS[(seed >> 32) % len(CONDITIONS)],
        )
