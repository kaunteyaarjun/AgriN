"""Analysis engines (M032+): pure deterministic computation.

A peer of ``src/services``: services do I/O (sessions, providers),
engines do rules over data they are handed. Nothing in this package
talks to the database, the network or the clock beyond an injectable
``now`` — that keeps every engine answer reproducible and unit-testable
without fixtures.

M032 crop health (``health``) and M033 risk (``risk``) ship first;
M034 recommendations and M039's decision aggregation land here too.
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
    crop_label_for,
    crop_profile_for,
)
from src.engines.risk import (
    BAND_THRESHOLDS,
    HAZARD_FACTORS,
    RISK_BANDS,
    RISK_ORDER,
    SEVERITY_POINTS,
    FarmRisk,
    RiskItem,
    assess_farm_risk,
    risk_band,
)

__all__ = [
    "BAND_THRESHOLDS",
    "CROP_PROFILES",
    "DEFAULT_CROP_PROFILE",
    "FACTOR_NAMES",
    "FACTOR_STATUSES",
    "HAZARD_FACTORS",
    "HEALTH_LEVELS",
    "RISK_BANDS",
    "RISK_ORDER",
    "SEVERITY_POINTS",
    "STALE_AFTER_SECONDS",
    "CropProfile",
    "FarmHealth",
    "FarmRisk",
    "HealthFactor",
    "PlotHealth",
    "RiskItem",
    "assess_farm_health",
    "assess_farm_risk",
    "assess_plot_health",
    "crop_label_for",
    "crop_profile_for",
    "risk_band",
]
