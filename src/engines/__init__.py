"""Analysis engines (M032+): pure deterministic computation.

A peer of ``src/services``: services do I/O (sessions, providers),
engines do rules over data they are handed. Nothing in this package
talks to the database, the network or the clock beyond an injectable
``now`` — that keeps every engine answer reproducible and unit-testable
without fixtures.

Three engines ship so far: M032 health (``health``), M033 risk
(``risk``), M034 recommendations (``recommend``); M039's decision
aggregation lands here too.
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
from src.engines.recommend import (
    RECOMMENDATION_CATEGORIES,
    RECOMMENDATION_ORDER,
    RECOMMENDATION_PRIORITY,
    RECOMMENDATION_SPECS,
    FarmRecommendations,
    Recommendation,
    recommend_farm_actions,
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
    "RECOMMENDATION_CATEGORIES",
    "RECOMMENDATION_ORDER",
    "RECOMMENDATION_PRIORITY",
    "RECOMMENDATION_SPECS",
    "RISK_BANDS",
    "RISK_ORDER",
    "SEVERITY_POINTS",
    "STALE_AFTER_SECONDS",
    "CropProfile",
    "FarmHealth",
    "FarmRecommendations",
    "FarmRisk",
    "HealthFactor",
    "PlotHealth",
    "Recommendation",
    "RiskItem",
    "assess_farm_health",
    "assess_farm_risk",
    "assess_plot_health",
    "crop_label_for",
    "crop_profile_for",
    "recommend_farm_actions",
    "risk_band",
]
