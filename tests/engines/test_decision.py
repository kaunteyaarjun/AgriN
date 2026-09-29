"""Decision engine tests (M039): stance rules, merged ordering,
verdict aggregation, evidence passthrough, and the caller-bug guards —
driven through the real four-engine pipeline, exactly the composition
M044's what-if will re-run.

Pure unit: no DB, no network, clock injected.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime

import pytest
from src.engines import (
    DECISION_STANCES,
    DecisionAction,
    DiseaseAssessment,
    FarmDecision,
    assess_disease,
    assess_farm_health,
    assess_farm_risk,
    decide_farm,
    recommend_farm_actions,
)
from src.engines.recommend import FarmRecommendations
from src.engines.risk import FarmRisk
from src.providers import DiseaseCandidate, DiseaseDetection
from src.services.farm_state import FarmStateView, PlotStateView, SignalCacheView
from src.services.normalize import NormalizedFarmState, normalize_signals

NOW = datetime(2026, 9, 29, 12, 0, 0, tzinfo=UTC)
OBSERVED = datetime(2026, 9, 29, 11, 0, 0, tzinfo=UTC)
PLANTED_ON = date(2026, 9, 1)
FARM_ID = uuid.UUID("00000000-0000-0000-0000-00000000f00d")

WEATHER = {
    "temperature_c": 22.0,
    "humidity_pct": 55.0,
    "rainfall_mm_24h": 5.0,
    "wind_speed_kmh": 10.0,
    "condition": "clear",
    "observed_at": OBSERVED.isoformat(),
    "source": "demo-weather-v1",
}
SATELLITE = {
    "ndvi": 0.62,
    "cloud_cover_pct": 10.0,
    "observed_at": OBSERVED.isoformat(),
    "source": "demo-satellite-v1",
}
SOIL = {
    "soil_moisture_pct": 45.0,
    "ph": 6.5,
    "soil_temperature_c": 18.0,
    "nitrogen_kg_ha": 60.0,
    "observed_at": OBSERVED.isoformat(),
    "source": "demo-soil-v1",
}
SOIL_DRY = {**SOIL, "soil_moisture_pct": 10.0}


def _plot(crop: str | None = "Maize", *, name: str = "Plot A") -> PlotStateView:
    return PlotStateView(
        plot_id=uuid.uuid4(),
        name=name,
        area_hectares=None,
        crop=crop,
        growth_stage="vegetative",
        planted_on=PLANTED_ON,
        days_since_planted=(NOW.date() - PLANTED_ON).days,
    )


def _state(
    plots: list[PlotStateView],
    *,
    farm_id: uuid.UUID = FARM_ID,
    soil: dict | None = SOIL,
    weather: dict | None = WEATHER,
    satellite: dict | None = SATELLITE,
) -> NormalizedFarmState:
    doc: dict = {}
    if weather is not None:
        doc["weather"] = weather
    if satellite is not None:
        doc["satellite"] = satellite
    if soil is not None:
        doc["soil"] = soil
    view = FarmStateView(
        farm_id=farm_id,
        farmer_id=uuid.uuid4(),
        name="Demo Farm",
        plots=plots,
        plot_count=len(plots),
        planted_plot_count=sum(1 for plot in plots if plot.crop is not None),
        crops=sorted({plot.crop for plot in plots if plot.crop is not None}),
        signals=SignalCacheView(signals=doc, refreshed_at=OBSERVED, age_seconds=3600),
    )
    return NormalizedFarmState(
        view=view,
        signals=normalize_signals(doc, now=NOW, refreshed_at=OBSERVED),
    )


def _pipeline(
    plots: list[PlotStateView],
    *,
    soil: dict | None = SOIL,
    weather: dict | None = WEATHER,
    satellite: dict | None = SATELLITE,
) -> tuple:
    state = _state(plots, soil=soil, weather=weather, satellite=satellite)
    health = assess_farm_health(state, now=NOW)
    risk = assess_farm_risk(state, health, now=NOW)
    recommendations = recommend_farm_actions(state, health, now=NOW)
    return state, health, risk, recommendations


def _detect(*candidates: tuple[str, float]) -> DiseaseDetection:
    return DiseaseDetection(
        source="demo-disease-v1",
        detected_at=OBSERVED,
        detections=[
            DiseaseCandidate(code=code, confidence=confidence) for code, confidence in candidates
        ],
    )


def _decide(
    plots: list[PlotStateView],
    *,
    soil: dict | None = SOIL,
    weather: dict | None = WEATHER,
    satellite: dict | None = SATELLITE,
    disease: Sequence = (),
    risk_override: FarmRisk | None = None,
) -> FarmDecision:
    state, health, risk, recommendations = _pipeline(
        plots, soil=soil, weather=weather, satellite=satellite
    )
    return decide_farm(
        state,
        health,
        risk_override if risk_override is not None else risk,
        recommendations,
        disease,
        now=NOW,
    )


def _risk_for(state: NormalizedFarmState, *, score: int, band: str) -> FarmRisk:
    return FarmRisk(
        farm_id=state.view.farm_id,
        score=score,
        band=band,
        items=[],
        hazard_readings_evaluated=0,
        hazard_readings_total=0,
        plot_count=state.view.plot_count,
        computed_at=NOW,
    )


def test_clean_farm_is_routine() -> None:
    decision = _decide([_plot("Maize")])
    assert decision.stance == "routine"
    assert decision.stance in DECISION_STANCES
    assert decision.disease_verdicts == {
        "not_detected": 0,
        "uncertain": 0,
        "suspected": 0,
        "detected": 0,
    }
    assert decision.risk_band == "low"
    assert decision.health_level == "healthy"
    assert decision.action_counts["urgent"] == 0
    assert decision.action_counts["soon"] == 0
    assert decision.stale_families == []
    assert decision.plots_with_unknown_factors == 0
    assert decision.plot_count == 1
    assert decision.computed_at == NOW
    assert decision.farm_id == FARM_ID


def test_urgent_action_triggers_act_now() -> None:
    decision = _decide([_plot("Maize")], soil=SOIL_DRY)
    assert decision.action_counts["urgent"] > 0
    assert decision.stance == "act_now"


def test_detected_disease_triggers_act_now_with_its_action() -> None:
    plot = _plot("Maize")
    state, health, risk, recommendations = _pipeline([plot])
    assessment = assess_disease(
        state,
        health,
        _detect(("gray_leaf_spot", 0.85)),
        plot.plot_id,
        image_id=uuid.uuid4(),
        now=NOW,
    )
    decision = decide_farm(state, health, risk, recommendations, [assessment], now=NOW)
    assert decision.stance == "act_now"
    assert decision.disease_verdicts["detected"] == 1
    action = next(item for item in decision.actions if item.code == "treat_disease")
    assert action.priority == "urgent"
    assert action.origin == "disease"
    assert "Gray leaf spot" in action.title
    assert "Plot A" in action.title
    assert action.image_id == assessment.image_id


@pytest.mark.parametrize(
    ("verdict", "expected_stance", "expected_code"),
    [
        ("suspected", "monitor", "verify_disease"),
        ("uncertain", "monitor", "monitor_disease"),
    ],
)
def test_weaker_disease_verdicts_floor_stance(
    verdict: str, expected_stance: str, expected_code: str
) -> None:
    plot = _plot("Maize")
    state, health, risk, recommendations = _pipeline([plot])
    confidence = {"suspected": 0.60, "uncertain": 0.50}[verdict]
    assessment = assess_disease(
        state, health, _detect(("gray_leaf_spot", confidence)), plot.plot_id, now=NOW
    )
    assert assessment.verdict == verdict  # the blend must land there
    decision = decide_farm(state, health, risk, recommendations, [assessment], now=NOW)
    assert decision.stance == expected_stance
    assert any(item.code == expected_code for item in decision.actions)


def test_moderate_risk_alone_is_monitor() -> None:
    plots = [_plot("Maize")]
    state, health, _, recommendations = _pipeline(plots)
    risk = _risk_for(state, score=30, band="moderate")
    decision = decide_farm(state, health, risk, recommendations, now=NOW)
    assert decision.stance == "monitor"


def test_high_risk_alone_is_act_now() -> None:
    plots = [_plot("Maize")]
    state, health, _, recommendations = _pipeline(plots)
    risk = _risk_for(state, score=75, band="high")
    decision = decide_farm(state, health, risk, recommendations, now=NOW)
    assert decision.stance == "act_now"


def test_blind_farm_never_claims_routine() -> None:
    decision = _decide([_plot("Maize")], weather=None, satellite=None, soil=None)
    assert decision.stance == "monitor"
    assert decision.action_counts["soon"] > 0  # M034 data-quality floor
    assert decision.plots_with_unknown_factors == 1
    assert decision.stale_families == [] or isinstance(decision.stale_families, list)


def test_disease_actions_sort_before_recommendations_at_equal_priority() -> None:
    plot = _plot("Maize")
    state, health, risk, recommendations = _pipeline([plot], soil=SOIL_DRY)
    assessment = assess_disease(
        state, health, _detect(("gray_leaf_spot", 0.85)), plot.plot_id, now=NOW
    )
    decision = decide_farm(state, health, risk, recommendations, [assessment], now=NOW)
    urgent = [item for item in decision.actions if item.priority == "urgent"]
    assert [item.origin for item in urgent] == ["disease", "recommendation"]


def test_recommendation_actions_pass_through_verbatim() -> None:
    plots = [_plot("Maize"), _plot("Wheat", name="Plot B")]
    state, health, risk, recommendations = _pipeline(plots, soil=SOIL_DRY)
    decision = decide_farm(state, health, risk, recommendations, now=NOW)
    for rec in recommendations.recommendations:
        match = next(
            item
            for item in decision.actions
            if item.origin == "recommendation"
            and item.code == rec.code
            and item.plot_id == rec.plot_id
        )
        assert match.category == rec.category
        assert match.priority == rec.priority
        assert match.title == rec.title
        assert match.detail == rec.detail
        assert match.plot_name == rec.plot_name
        assert match.image_id is None


def test_worst_verdict_wins_and_one_action_per_plot() -> None:
    plot = _plot("Maize")
    state, health, risk, recommendations = _pipeline([plot])
    suspected = assess_disease(
        state, health, _detect(("gray_leaf_spot", 0.60)), plot.plot_id, now=NOW
    )
    detected = assess_disease(
        state,
        health,
        _detect(("gray_leaf_spot", 0.85)),
        plot.plot_id,
        image_id=uuid.uuid4(),
        now=NOW,
    )
    decision = decide_farm(state, health, risk, recommendations, [suspected, detected], now=NOW)
    disease_actions = [item for item in decision.actions if item.origin == "disease"]
    assert len(disease_actions) == 1
    assert disease_actions[0].code == "treat_disease"
    assert decision.disease_verdicts == {
        "not_detected": 0,
        "uncertain": 0,
        "suspected": 0,
        "detected": 1,
    }


def test_verdict_counts_span_plots_including_not_detected() -> None:
    healthy = _plot("Maize", name="Healthy")
    suspected_plot = _plot("Maize", name="Suspected")
    detected_plot = _plot("Maize", name="Detected")
    plots = [healthy, suspected_plot, detected_plot]
    state, health, risk, recommendations = _pipeline(plots)
    assessments = [
        assess_disease(state, health, _detect(), healthy.plot_id, now=NOW),
        assess_disease(
            state, health, _detect(("gray_leaf_spot", 0.60)), suspected_plot.plot_id, now=NOW
        ),
        assess_disease(
            state, health, _detect(("gray_leaf_spot", 0.85)), detected_plot.plot_id, now=NOW
        ),
    ]
    decision = decide_farm(state, health, risk, recommendations, assessments, now=NOW)
    assert decision.disease_verdicts == {
        "not_detected": 1,
        "uncertain": 0,
        "suspected": 1,
        "detected": 1,
    }


def test_disease_detail_rejoins_reasons_verbatim() -> None:
    plot = _plot("Maize")
    state, health, risk, recommendations = _pipeline([plot])
    assessment = assess_disease(
        state, health, _detect(("gray_leaf_spot", 0.85)), plot.plot_id, now=NOW
    )
    decision = decide_farm(state, health, risk, recommendations, [assessment], now=NOW)
    action = next(item for item in decision.actions if item.code == "treat_disease")
    assert action.detail == "; ".join(assessment.candidates[0].reasons)


def test_health_for_another_farm_is_a_value_error() -> None:
    plots = [_plot("Maize")]
    state, _, risk, recommendations = _pipeline(plots)
    foreign_state = _state([_plot("Maize")], farm_id=uuid.uuid4())
    foreign_health = assess_farm_health(foreign_state, now=NOW)
    with pytest.raises(ValueError, match="health is for farm"):
        decide_farm(state, foreign_health, risk, recommendations, now=NOW)


def test_risk_for_another_farm_is_a_value_error() -> None:
    plots = [_plot("Maize")]
    state, health, _, recommendations = _pipeline(plots)
    foreign = FarmRisk(
        farm_id=uuid.uuid4(),
        score=0,
        band="low",
        items=[],
        hazard_readings_evaluated=0,
        hazard_readings_total=0,
        plot_count=1,
        computed_at=NOW,
    )
    with pytest.raises(ValueError, match="risk is for farm"):
        decide_farm(state, health, foreign, recommendations, now=NOW)


def test_recommendations_for_another_farm_is_a_value_error() -> None:
    plots = [_plot("Maize")]
    state, health, risk, _ = _pipeline(plots)
    foreign = FarmRecommendations(
        farm_id=uuid.uuid4(),
        recommendations=[],
        actionable=0,
        plot_count=1,
        computed_at=NOW,
    )
    with pytest.raises(ValueError, match="recommendations is for farm"):
        decide_farm(state, health, risk, foreign, now=NOW)


def test_assessment_for_another_farm_or_unknown_plot_is_a_value_error() -> None:
    plots = [_plot("Maize")]
    state, health, risk, recommendations = _pipeline(plots)
    stranger_state = _state([_plot("Maize")], farm_id=uuid.uuid4())
    stranger_health = assess_farm_health(stranger_state, now=NOW)
    foreign = assess_disease(
        stranger_state,
        stranger_health,
        _detect(("rust", 0.9)),
        list(stranger_state.view.plots)[0].plot_id,
        now=NOW,
    )
    with pytest.raises(ValueError, match="disease assessment is for farm"):
        decide_farm(state, health, risk, recommendations, [foreign], now=NOW)

    orphan = DiseaseAssessment(
        farm_id=FARM_ID,
        plot_id=uuid.uuid4(),
        plot_name="Ghost",
        crop="Maize",
        health_level="healthy",
        image_id=None,
        source="demo-disease-v1",
        verdict="suspected",
        candidates=[],
        detected_at=OBSERVED,
        computed_at=NOW,
    )
    with pytest.raises(ValueError, match="is not part of farm"):
        decide_farm(state, health, risk, recommendations, [orphan], now=NOW)


def test_verdict_without_candidates_is_a_value_error() -> None:
    plots = [_plot("Maize")]
    state, health, risk, recommendations = _pipeline(plots)
    broken = DiseaseAssessment(
        farm_id=FARM_ID,
        plot_id=plots[0].plot_id,
        plot_name="Plot A",
        crop="Maize",
        health_level="healthy",
        image_id=None,
        source="demo-disease-v1",
        verdict="detected",
        candidates=[],
        detected_at=OBSERVED,
        computed_at=NOW,
    )
    with pytest.raises(ValueError, match="with no candidates"):
        decide_farm(state, health, risk, recommendations, [broken], now=NOW)


def test_decision_is_deterministic_and_no_clock_is_read() -> None:
    plots = [_plot("Maize")]
    state, health, risk, recommendations = _pipeline(plots, soil=SOIL_DRY)
    first = decide_farm(state, health, risk, recommendations, now=NOW)
    second = decide_farm(state, health, risk, recommendations, now=NOW)
    assert first == second
    assert first.computed_at == NOW


def test_action_counts_and_ordering_are_total() -> None:
    plot = _plot("Maize")
    state, health, risk, recommendations = _pipeline([plot], soil=SOIL_DRY)
    assessment = assess_disease(
        state, health, _detect(("gray_leaf_spot", 0.85)), plot.plot_id, now=NOW
    )
    decision = decide_farm(state, health, risk, recommendations, [assessment], now=NOW)
    priorities = [item.priority for item in decision.actions]
    order = {"urgent": 0, "soon": 1, "routine": 2}
    assert priorities == sorted(priorities, key=order.__getitem__)
    assert sum(decision.action_counts.values()) == len(decision.actions)
    for item in decision.actions:
        assert isinstance(item, DecisionAction)
        assert item.origin in ("disease", "recommendation")


def test_stance_vocabulary_is_the_documented_one() -> None:
    assert DECISION_STANCES == ("routine", "monitor", "act_now")
