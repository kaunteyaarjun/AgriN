"""Structured agricultural decision engine (M039): aggregation.

The pipeline's last analysis step before advisory generation: folds
M032 health, M033 risk, M034 recommendations and M037 disease
assessments into one deterministic ``FarmDecision``. Implemented as
pure aggregation — every input is computed by its own engine and
handed in, no thresholds are invented here and no evidence string is
re-derived (M044 re-runs the four engines, then this one).

Headline call (``stance``) has three documented rules: ``act_now`` if
risk band high, any urgent action, or any plot ``detected``; else
``monitor`` if risk band moderate, any soon action, or any plot
``suspected``/``uncertain``; else ``routine``. Blind farms can never
read ``routine`` because M034 already floors them with ``soon``
data-quality actions.

Human checkpoint approved 2026-09-30 (decision D9).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Final

from pydantic import BaseModel

from src.engines.disease import DISEASE_VERDICTS, DiseaseAssessment
from src.engines.health import FarmHealth
from src.engines.recommend import RECOMMENDATION_PRIORITY, FarmRecommendations
from src.engines.risk import FarmRisk
from src.services.normalize import NormalizedFarmState

DECISION_STANCES: Final[tuple[str, ...]] = ("routine", "monitor", "act_now")
ACTION_ORIGINS: Final[tuple[str, ...]] = ("disease", "recommendation")

DISEASE_VERDICT_ACTIONS: Final[dict[str, tuple[str, str, str, str]]] = {
    # verdict -> (code, category, priority, title template)
    "uncertain": ("monitor_disease", "monitoring", "routine", "Monitor {label} on {plot}"),
    "suspected": ("verify_disease", "scouting", "soon", "Verify suspected {label} on {plot}"),
    "detected": ("treat_disease", "disease_control", "urgent", "Treat {label} on {plot}"),
}
"""M039-owned disease action vocabulary. ``disease_control`` is a new
category (M034's category list stays untouched); ``scouting`` and
``monitoring`` are reused."""


class DecisionAction(BaseModel):
    """One item of the farm's action queue — a recommendation passed
    through verbatim or a verdict-derived disease action."""

    code: str
    category: str
    priority: str
    title: str
    detail: str
    origin: str
    plot_id: uuid.UUID | None = None
    plot_name: str | None = None
    image_id: uuid.UUID | None = None


class FarmDecision(BaseModel):
    """The structured decision for one farm, ready for M041/M043/M050."""

    farm_id: uuid.UUID
    stance: str
    health_level: str
    risk_score: int
    risk_band: str
    disease_verdicts: dict[str, int]
    actions: list[DecisionAction]
    action_counts: dict[str, int]
    stale_families: list[str]
    plots_with_unknown_factors: int
    plot_count: int
    computed_at: datetime


def _check_farm(name: str, farm_id: uuid.UUID, state: NormalizedFarmState) -> None:
    if farm_id != state.view.farm_id:
        raise ValueError(f"{name} is for farm {farm_id}, state is for farm {state.view.farm_id}")


def _recommendation_actions(recommendations: FarmRecommendations) -> list[DecisionAction]:
    return [
        DecisionAction(
            code=rec.code,
            category=rec.category,
            priority=rec.priority,
            title=rec.title,
            detail=rec.detail,
            origin="recommendation",
            plot_id=rec.plot_id,
            plot_name=rec.plot_name,
        )
        for rec in recommendations.recommendations
    ]


def _disease_views(
    state: NormalizedFarmState,
    assessments: Sequence[DiseaseAssessment],
) -> tuple[list[DecisionAction], dict[str, int]]:
    """Worst verdict per plot → counts + one action per affected plot."""
    counts = {verdict: 0 for verdict in DISEASE_VERDICTS}
    plot_ids = {plot.plot_id for plot in state.view.plots}
    worst: dict[uuid.UUID, DiseaseAssessment] = {}
    for assessment in assessments:
        _check_farm("disease assessment", assessment.farm_id, state)
        if assessment.plot_id not in plot_ids:
            raise ValueError(
                f"disease assessment for plot {assessment.plot_id} "
                f"is not part of farm {state.view.farm_id}"
            )
        current = worst.get(assessment.plot_id)
        if current is None or (
            DISEASE_VERDICTS.index(assessment.verdict),
            assessment.detected_at,
        ) > (DISEASE_VERDICTS.index(current.verdict), current.detected_at):
            worst[assessment.plot_id] = assessment

    actions: list[DecisionAction] = []
    for assessment in sorted(worst.values(), key=lambda item: str(item.plot_id)):
        counts[assessment.verdict] += 1
        if assessment.verdict == "not_detected":
            continue
        if not assessment.candidates:
            raise ValueError(
                f"disease assessment for plot {assessment.plot_id} claims "
                f"{assessment.verdict!r} with no candidates"
            )
        code, category, priority, template = DISEASE_VERDICT_ACTIONS[assessment.verdict]
        top = assessment.candidates[0]
        actions.append(
            DecisionAction(
                code=code,
                category=category,
                priority=priority,
                title=template.format(label=top.label, plot=assessment.plot_name),
                detail="; ".join(top.reasons),
                origin="disease",
                plot_id=assessment.plot_id,
                plot_name=assessment.plot_name,
                image_id=assessment.image_id,
            )
        )
    return actions, counts


def _stance(risk_band: str, actions: list[DecisionAction], verdicts: dict[str, int]) -> str:
    if (
        risk_band == "high"
        or verdicts["detected"] > 0
        or any(action.priority == "urgent" for action in actions)
    ):
        return "act_now"
    if (
        risk_band == "moderate"
        or verdicts["suspected"] > 0
        or verdicts["uncertain"] > 0
        or any(action.priority == "soon" for action in actions)
    ):
        return "monitor"
    return "routine"


def _sort_key(action: DecisionAction) -> tuple[int, int, str, bool, str, str]:
    return (
        RECOMMENDATION_PRIORITY.index(action.priority),
        ACTION_ORIGINS.index(action.origin),
        action.code,
        action.plot_name is None,
        action.plot_name or "",
        str(action.plot_id or ""),
    )


def decide_farm(
    state: NormalizedFarmState,
    health: FarmHealth,
    risk: FarmRisk,
    recommendations: FarmRecommendations,
    disease: Sequence[DiseaseAssessment] = (),
    *,
    now: datetime | None = None,
) -> FarmDecision:
    """Aggregate the four engines into one decision. Raises
    ``ValueError`` on caller bugs: any input for another farm, a
    disease assessment for a plot outside the state, or a non-clean
    verdict with no candidates."""
    moment = now or datetime.now(UTC)
    _check_farm("health", health.farm_id, state)
    _check_farm("risk", risk.farm_id, state)
    _check_farm("recommendations", recommendations.farm_id, state)

    disease_actions, verdict_counts = _disease_views(state, disease)
    actions = sorted(
        _recommendation_actions(recommendations) + disease_actions,
        key=_sort_key,
    )
    action_counts = {
        priority: sum(1 for action in actions if action.priority == priority)
        for priority in RECOMMENDATION_PRIORITY
    }
    return FarmDecision(
        farm_id=state.view.farm_id,
        stance=_stance(risk.band, actions, verdict_counts),
        health_level=health.level,
        risk_score=risk.score,
        risk_band=risk.band,
        disease_verdicts=verdict_counts,
        actions=actions,
        action_counts=action_counts,
        stale_families=list(health.stale_families),
        plots_with_unknown_factors=sum(
            1 for plot in health.plots if plot.factors_evaluated < plot.factor_count
        ),
        plot_count=state.view.plot_count,
        computed_at=moment,
    )


__all__ = [
    "ACTION_ORIGINS",
    "DECISION_STANCES",
    "DISEASE_VERDICT_ACTIONS",
    "DecisionAction",
    "FarmDecision",
    "decide_farm",
]
