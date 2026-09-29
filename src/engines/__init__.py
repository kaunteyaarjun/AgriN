"""Analysis engines (M032+): pure deterministic computation.

A peer of ``src/services``: services do I/O (sessions, providers),
engines do rules over data they are handed. Nothing in this package
talks to the database, the network or the clock beyond an injectable
``now`` — that keeps every engine answer reproducible and unit-testable
without fixtures.

Five engines ship so far: M032 health (``health``), M033 risk
(``risk``), M034 recommendations (``recommend``), M037 disease
(``disease``), M039 decision (``decision``) — and M043's ``pipeline``
chains them in that order behind one injectable clock; M044's
``whatif`` re-runs that chain on a perturbed state.
"""

from src.engines.decision import (
    ACTION_ORIGINS,
    DECISION_STANCES,
    DISEASE_VERDICT_ACTIONS,
    DecisionAction,
    FarmDecision,
    decide_farm,
)
from src.engines.disease import (
    CROP_MISMATCH_FACTOR,
    DETECTED_MIN,
    DISEASE_VERDICTS,
    HEALTHY_CANOPY_FACTOR,
    SUSPECTED_MIN,
    DiseaseAssessment,
    DiseaseCandidateAssessment,
    assess_disease,
)
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
from src.engines.pipeline import FarmAnalysis, run_analysis
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
from src.engines.whatif import WHAT_IF_KNOBS, WhatIfChanges, WhatIfResult, simulate_what_if

__all__ = [
    "ACTION_ORIGINS",
    "BAND_THRESHOLDS",
    "CROP_MISMATCH_FACTOR",
    "CROP_PROFILES",
    "DECISION_STANCES",
    "DEFAULT_CROP_PROFILE",
    "DETECTED_MIN",
    "DISEASE_VERDICTS",
    "DISEASE_VERDICT_ACTIONS",
    "FACTOR_NAMES",
    "FACTOR_STATUSES",
    "HAZARD_FACTORS",
    "HEALTHY_CANOPY_FACTOR",
    "HEALTH_LEVELS",
    "RECOMMENDATION_CATEGORIES",
    "RECOMMENDATION_ORDER",
    "RECOMMENDATION_PRIORITY",
    "RECOMMENDATION_SPECS",
    "RISK_BANDS",
    "RISK_ORDER",
    "SEVERITY_POINTS",
    "STALE_AFTER_SECONDS",
    "SUSPECTED_MIN",
    "WHAT_IF_KNOBS",
    "CropProfile",
    "DecisionAction",
    "DiseaseAssessment",
    "DiseaseCandidateAssessment",
    "FarmAnalysis",
    "FarmDecision",
    "FarmHealth",
    "FarmRecommendations",
    "FarmRisk",
    "HealthFactor",
    "PlotHealth",
    "Recommendation",
    "RiskItem",
    "WhatIfChanges",
    "WhatIfResult",
    "assess_disease",
    "assess_farm_health",
    "assess_farm_risk",
    "assess_plot_health",
    "crop_label_for",
    "crop_profile_for",
    "decide_farm",
    "recommend_farm_actions",
    "risk_band",
    "run_analysis",
    "simulate_what_if",
]
