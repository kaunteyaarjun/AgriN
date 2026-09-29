"""Disease assessment engine tests (M037): the context blend in full —
crop affinity, healthy-canopy note, verdict thresholds, ordering, and
the caller-bug guards — built on the same fixture style as the M032/
M033/M034 engine tests.

Pure unit: no DB, no network, clock injected.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from src.engines import (
    CROP_MISMATCH_FACTOR,
    DETECTED_MIN,
    DISEASE_VERDICTS,
    HEALTHY_CANOPY_FACTOR,
    SUSPECTED_MIN,
    DiseaseAssessment,
    assess_disease,
    assess_farm_health,
)
from src.engines.disease import DiseaseCandidateAssessment
from src.providers import DiseaseCandidate, DiseaseDetection
from src.providers.disease import DISEASE_CATALOG
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
SOIL_DRY = {**SOIL, "soil_moisture_pct": 10.0}  # maize stress (M032 profile)

DEMO_SOURCE = "demo-disease-v1"


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
) -> NormalizedFarmState:
    doc: dict = {"weather": WEATHER, "satellite": SATELLITE}
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


def _detection(*candidates: tuple[str, float]) -> DiseaseDetection:
    return DiseaseDetection(
        source=DEMO_SOURCE,
        detected_at=OBSERVED,
        detections=[
            DiseaseCandidate(code=code, confidence=confidence) for code, confidence in candidates
        ],
    )


def _assess(
    state: NormalizedFarmState,
    detection: DiseaseDetection,
    plot_id: uuid.UUID,
    *,
    image_id: uuid.UUID | None = None,
) -> DiseaseAssessment:
    health = assess_farm_health(state, now=NOW)
    return assess_disease(state, health, detection, plot_id, image_id=image_id, now=NOW)


def test_empty_detections_is_not_detected() -> None:
    plot = _plot("Maize")
    assessment = _assess(_state([plot]), _detection(), plot.plot_id)
    assert assessment.verdict == "not_detected"
    assert assessment.candidates == []
    assert assessment.verdict in DISEASE_VERDICTS
    assert assessment.image_id is None


def test_image_id_passthrough() -> None:
    plot = _plot("Maize")
    image_id = uuid.uuid4()
    assessment = _assess(
        _state([plot]), _detection(("gray_leaf_spot", 0.8)), plot.plot_id, image_id=image_id
    )
    assert assessment.image_id == image_id


def test_matching_crop_with_stressed_canopy_is_detected() -> None:
    plot = _plot("Maize")
    state = _state([plot], soil=SOIL_DRY)
    assessment = _assess(state, _detection(("gray_leaf_spot", 0.85)), plot.plot_id)
    candidate = assessment.candidates[0]
    assert assessment.verdict == "detected"
    assert assessment.health_level == "stressed"
    assert candidate.effective_confidence == candidate.raw_confidence == 0.85
    assert candidate.reasons == [
        "model confidence 0.85",
        "crop match: maize",
        "effective confidence 0.850",
    ]


def test_crop_mismatch_discounts_and_names_both_sides() -> None:
    plot = _plot("Maize")
    state = _state([plot], soil=SOIL_DRY)
    assessment = _assess(state, _detection(("rust", 0.90)), plot.plot_id)
    candidate = assessment.candidates[0]
    assert assessment.verdict == "suspected"
    assert candidate.effective_confidence == 0.54
    assert candidate.raw_confidence == 0.90
    assert (
        "crop mismatch: Rust typically affects beans, wheat, plot grows maize (x0.6)"
        in candidate.reasons
    )
    assert CROP_MISMATCH_FACTOR == 0.6


def test_healthy_canopy_discounts() -> None:
    plot = _plot("Maize")  # default signals: canopy healthy
    assessment = _assess(_state([plot]), _detection(("gray_leaf_spot", 0.75)), plot.plot_id)
    candidate = assessment.candidates[0]
    assert assessment.health_level == "healthy"
    assert assessment.verdict == "suspected"
    assert candidate.effective_confidence == 0.675
    assert f"plot canopy reads healthy (x{HEALTHY_CANOPY_FACTOR})" in candidate.reasons


def test_combined_discounts_reach_uncertain() -> None:
    plot = _plot("Maize")
    assessment = _assess(_state([plot]), _detection(("rust", 0.90)), plot.plot_id)
    candidate = assessment.candidates[0]
    assert candidate.effective_confidence == 0.486
    assert assessment.verdict == "uncertain"


def test_unregistered_crop_gets_no_discount_only_a_note() -> None:
    plot = _plot(None)
    state = _state([plot], soil=SOIL_DRY)
    assessment = _assess(state, _detection(("leaf_blight", 0.80)), plot.plot_id)
    candidate = assessment.candidates[0]
    assert candidate.effective_confidence == 0.80
    assert "crop not registered - Leaf blight affinity unchecked" in candidate.reasons
    assert assessment.crop is None


@pytest.mark.parametrize(
    ("confidence", "expected"),
    [
        (DETECTED_MIN, "detected"),
        (0.699, "suspected"),
        (SUSPECTED_MIN, "suspected"),
        (0.499, "uncertain"),
    ],
)
def test_verdict_boundaries(confidence: float, expected: str) -> None:
    plot = _plot("Maize")
    state = _state([plot], soil=SOIL_DRY)  # stressed: no canopy discount
    assessment = _assess(state, _detection(("gray_leaf_spot", confidence)), plot.plot_id)
    assert assessment.verdict == expected


def test_candidates_sort_by_effective_then_code() -> None:
    plot = _plot("Maize")
    state = _state([plot], soil=SOIL_DRY)
    assessment = _assess(
        state,
        _detection(
            ("gray_leaf_spot", 0.80),
            ("fusarium_wilt", 0.80),
            ("rust", 0.95),
            ("powdery_mildew", 0.90),
        ),
        plot.plot_id,
    )
    codes = [candidate.code for candidate in assessment.candidates]
    assert codes == ["fusarium_wilt", "gray_leaf_spot", "rust", "powdery_mildew"]
    assert [candidate.effective_confidence for candidate in assessment.candidates] == [
        0.80,
        0.80,
        0.57,
        0.54,
    ]
    labels = [candidate.label for candidate in assessment.candidates]
    assert labels == [DISEASE_CATALOG[code].label for code in codes]


def test_context_never_inflates_confidence() -> None:
    plot = _plot("Maize")
    state = _state([plot])  # healthy canopy: the strongest discount path
    for confidence in (0.30, 0.50, 0.70, 0.95):
        for code in ("gray_leaf_spot", "rust"):
            assessment = _assess(state, _detection((code, confidence)), plot.plot_id)
            candidate = assessment.candidates[0]
            assert candidate.effective_confidence <= candidate.raw_confidence


def test_unknown_plot_is_a_value_error() -> None:
    state = _state([_plot("Maize")])
    with pytest.raises(ValueError, match="not part of farm"):
        assess_disease(
            state,
            assess_farm_health(state, now=NOW),
            _detection(("rust", 0.8)),
            uuid.uuid4(),
            now=NOW,
        )


def test_health_for_another_farm_is_a_value_error() -> None:
    plot = _plot("Maize")
    state = _state([plot])
    other = _state([_plot("Maize")], farm_id=uuid.uuid4())
    with pytest.raises(ValueError, match="health is for farm"):
        assess_disease(
            state,
            assess_farm_health(other, now=NOW),
            _detection(("rust", 0.8)),
            plot.plot_id,
            now=NOW,
        )


def test_plot_missing_from_health_is_a_value_error() -> None:
    plot = _plot("Maize")
    state = _state([plot])
    health = assess_farm_health(state, now=NOW).model_copy(update={"plots": []})
    with pytest.raises(ValueError, match="missing from health"):
        assess_disease(state, health, _detection(("rust", 0.8)), plot.plot_id, now=NOW)


def test_assessment_carries_display_context() -> None:
    plot = _plot("Wheat", name="North 40")
    state = _state([plot], soil=SOIL_DRY)
    assessment = _assess(state, _detection(("rust", 0.88)), plot.plot_id)
    assert assessment.farm_id == FARM_ID
    assert assessment.plot_id == plot.plot_id
    assert assessment.plot_name == "North 40"
    assert assessment.crop == "Wheat"
    assert assessment.source == DEMO_SOURCE
    assert assessment.detected_at == OBSERVED
    assert assessment.computed_at == NOW
    assert isinstance(assessment.candidates[0], DiseaseCandidateAssessment)


def test_no_clock_is_read_when_now_is_given() -> None:
    plot = _plot("Maize")
    state = _state([plot])
    before = datetime.now(UTC)
    _assess(state, _detection(("rust", 0.8)), plot.plot_id)
    after = datetime.now(UTC)
    assert before <= after  # sanity: clock exists; assessment used injected NOW
    assessment = _assess(state, _detection(("rust", 0.8)), plot.plot_id)
    assert assessment.computed_at == NOW
