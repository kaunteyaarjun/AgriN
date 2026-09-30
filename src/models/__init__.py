"""ORM models package.

Importing this package registers every model on ``Base.metadata`` — Alembic's
``env.py`` relies on that for ``--autogenerate`` (M004/M008).
"""

from __future__ import annotations

from src.models.base import Base
from src.models.farm import Farm
from src.models.farm_signal_cache import FarmSignalCache
from src.models.farmer import Farmer
from src.models.plot import Plot
from src.models.plot_image import PlotImage
from src.models.plot_state import GROWTH_STAGES, PlotState
from src.models.refresh_token import RefreshToken
from src.models.satellite_observation import SatelliteObservation
from src.models.soil_observation import SoilObservation
from src.models.user import User, UserRole
from src.models.weather_observation import WeatherObservation

__all__ = [
    "Base",
    "Farm",
    "FarmSignalCache",
    "Farmer",
    "GROWTH_STAGES",
    "Plot",
    "PlotImage",
    "PlotState",
    "RefreshToken",
    "SatelliteObservation",
    "SoilObservation",
    "User",
    "UserRole",
    "WeatherObservation",
]
