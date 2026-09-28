"""External provider pattern (M021): base class, errors, registry.

Usage by later milestones:

- implementations (M022/M025/M028/M036/M040+): subclass the family ABC,
  set ``family``/``mode``/``name``, decorate with ``@register``.
- consumers (M023+): ``get_provider(family)`` or the typed per-family
  getter (``get_weather_provider()``); map ``ProviderError`` subclasses
  to retries/skip decisions at the ingestion layer.
"""

from __future__ import annotations

from src.providers.base import KNOWN_FAMILIES, BaseProvider
from src.providers.errors import (
    ProviderError,
    ProviderNotRegistered,
    ProviderResponseInvalid,
    ProviderUnavailable,
)
from src.providers.registry import ProviderRegistry, default_registry, get_provider, register
from src.providers.satellite import (
    SatelliteProvider,
    SatelliteReading,
    get_satellite_provider,
)

# Concrete providers register themselves on import — one grep-able line
# per provider (M021 rule: no auto-discovery/entry-point magic; the
# demo import sorts between its family's contract imports).
from src.providers.satellite_demo import DemoSatelliteProvider  # noqa: F401  (registers on import)
from src.providers.weather import WeatherProvider, WeatherReading, get_weather_provider
from src.providers.weather_demo import DemoWeatherProvider  # noqa: F401  (registers on import)

__all__ = [
    "KNOWN_FAMILIES",
    "BaseProvider",
    "DemoSatelliteProvider",
    "DemoWeatherProvider",
    "ProviderError",
    "ProviderNotRegistered",
    "ProviderRegistry",
    "ProviderResponseInvalid",
    "ProviderUnavailable",
    "SatelliteProvider",
    "SatelliteReading",
    "WeatherProvider",
    "WeatherReading",
    "default_registry",
    "get_provider",
    "get_satellite_provider",
    "get_weather_provider",
    "register",
]
