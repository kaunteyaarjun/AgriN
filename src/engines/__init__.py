"""Analysis engines (M032+): pure deterministic computation.

A peer of ``src/services``: services do I/O (sessions, providers),
engines do rules over data they are handed. Nothing in this package
talks to the database, the network or the clock beyond an injectable
``now`` — that keeps every engine answer reproducible and unit-testable
without fixtures.

M032 crop health (``health``) ships first; M033 risk, M034
recommendations and M039's decision aggregation land here too.
"""

from src.engines.health import (
    CROP_PROFILES,
    DEFAULT_CROP_PROFILE,
    FACTOR_NAMES,
    FACTOR_STATUSES,
    HEALTH_LEVELS,
    STALE_AFTER_SECONDS,
    CropProfile,
    FarmHealth,
    HealthFactor,
    PlotHealth,
    assess_farm_health,
    assess_plot_health,
)

__all__ = [
    "CROP_PROFILES",
    "DEFAULT_CROP_PROFILE",
    "FACTOR_NAMES",
    "FACTOR_STATUSES",
    "HEALTH_LEVELS",
    "STALE_AFTER_SECONDS",
    "CropProfile",
    "FarmHealth",
    "HealthFactor",
    "PlotHealth",
    "assess_farm_health",
    "assess_plot_health",
]
