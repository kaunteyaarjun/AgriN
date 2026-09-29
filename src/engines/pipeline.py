"""Decision pipeline (M043): the engine order, once.

``run_analysis`` chains the four pure engines over one
``NormalizedFarmState`` and bundles every intermediate result: the
assembly M043's advisory endpoint, M044's what-if re-run and the
M047-M050 read endpoints all need, without any of them re-deriving the
order (health -> risk -> recommendations -> decision) or the clock rule.

Pure, like the rest of the package: no I/O, no clock read beyond the
injectable ``now`` — one moment serves every engine, so an answer can
never mix two clocks.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from pydantic import BaseModel

from src.engines.decision import FarmDecision, decide_farm
from src.engines.disease import DiseaseAssessment
from src.engines.health import FarmHealth, assess_farm_health
from src.engines.recommend import FarmRecommendations, recommend_farm_actions
from src.engines.risk import FarmRisk, assess_farm_risk
from src.services.normalize import NormalizedFarmState


class FarmAnalysis(BaseModel):
    """One pipeline run: the state it ran on plus every engine's answer."""

    state: NormalizedFarmState
    health: FarmHealth
    risk: FarmRisk
    recommendations: FarmRecommendations
    decision: FarmDecision


def run_analysis(
    state: NormalizedFarmState,
    disease: Sequence[DiseaseAssessment] = (),
    *,
    now: datetime | None = None,
) -> FarmAnalysis:
    """Run health -> risk -> recommendations -> decision with one clock.

    ``disease`` is the M037 assessments for this farm (empty today: no
    milestone persists them — M049 feeds real ones in).
    """
    moment = now or datetime.now(UTC)
    health = assess_farm_health(state, now=moment)
    risk = assess_farm_risk(state, health, now=moment)
    recommendations = recommend_farm_actions(state, health, now=moment)
    decision = decide_farm(state, health, risk, recommendations, disease, now=moment)
    return FarmAnalysis(
        state=state,
        health=health,
        risk=risk,
        recommendations=recommendations,
        decision=decision,
    )
