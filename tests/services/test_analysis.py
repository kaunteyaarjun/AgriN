"""Pipeline + analysis service tests (M043): the engine order once,
one clock, and the DB read path that feeds it.

The ``run_analysis`` tests are pure (no DB, no network, clock
injected); the ``analyze_farm`` tests run against dev Postgres and
SKIP when it is unreachable, with cleanup scoped to seeded users (M019
lesson). The service does no authorization — that is the route's job
(M043 contract) — so every direct call here works with an anonymous
session, which is the assertion of that rule.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, select, text
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.errors import NotFound
from src.engines import (
    FarmAnalysis,
    assess_disease,
    assess_farm_health,
    assess_farm_risk,
    decide_farm,
    recommend_farm_actions,
    run_analysis,
)
from src.models import Farm, Farmer, Plot, User
from src.providers import DiseaseCandidate, DiseaseDetection
from src.services.analysis import analyze_farm
from src.services.farm_state import (
    FarmStateView,
    PlotStateView,
    SignalCacheView,
    put_signals,
    set_plot_state,
)
from src.services.normalize import NormalizedFarmState, normalize_signals

REPO_ROOT = Path(__file__).resolve().parents[2]
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
WEATHER_STALE = {**WEATHER, "observed_at": (NOW - timedelta(days=2)).isoformat()}


# ---------- pure: run_analysis ----------


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


def _detect(*candidates: tuple[str, float]) -> DiseaseDetection:
    return DiseaseDetection(
        source="demo-disease-v1",
        detected_at=OBSERVED,
        detections=[
            DiseaseCandidate(code=code, confidence=confidence) for code, confidence in candidates
        ],
    )


def test_run_analysis_is_the_documented_chain_and_is_deterministic() -> None:
    state = _state([_plot("Maize")])

    first = run_analysis(state, now=NOW)
    second = run_analysis(state, now=NOW)
    assert first == second  # pure: same inputs -> same outputs

    health = assess_farm_health(state, now=NOW)
    risk = assess_farm_risk(state, health, now=NOW)
    recommendations = recommend_farm_actions(state, health, now=NOW)
    decision = decide_farm(state, health, risk, recommendations, (), now=NOW)
    assert first == FarmAnalysis(
        state=state,
        health=health,
        risk=risk,
        recommendations=recommendations,
        decision=decision,
    )


def test_run_analysis_one_clock_serves_every_engine() -> None:
    analysis = run_analysis(_state([_plot("Maize")]), now=NOW)
    assert analysis.health.computed_at == NOW
    assert analysis.risk.computed_at == NOW
    assert analysis.recommendations.computed_at == NOW
    assert analysis.decision.computed_at == NOW
    # the decision echoes the engines it was built from, not a re-derivation
    assert analysis.decision.health_level == analysis.health.level
    assert analysis.decision.risk_score == analysis.risk.score
    assert analysis.decision.risk_band == analysis.risk.band
    assert analysis.decision.stale_families == analysis.health.stale_families
    assert analysis.state.view.farm_id == analysis.decision.farm_id


def test_run_analysis_passes_disease_assessments_through() -> None:
    plot = _plot("Maize")
    state = _state([plot])
    health = assess_farm_health(state, now=NOW)
    assessment = assess_disease(
        state,
        health,
        _detect(("gray_leaf_spot", 0.85)),
        plot.plot_id,
        image_id=uuid.uuid4(),
        now=NOW,
    )

    analysis = run_analysis(state, [assessment], now=NOW)
    assert analysis.decision.disease_verdicts["detected"] == 1
    assert analysis.decision.stance == "act_now"

    bare = run_analysis(_state([_plot("Maize")]), now=NOW)
    assert bare.decision.disease_verdicts == {
        "not_detected": 0,
        "uncertain": 0,
        "suspected": 0,
        "detected": 0,
    }


# ---------- DB: analyze_farm ----------


async def _db_reachable() -> bool:
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _alembic_config() -> Config:
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return cfg


@pytest.fixture
async def _db() -> AsyncGenerator[None, None]:
    if not await _db_reachable():
        pytest.skip("dev Postgres not reachable; start `docker compose up -d db`")
    await asyncio.to_thread(command.upgrade, _alembic_config(), "head")
    yield
    await dispose_engine()


async def _seed(session, seeded: list[uuid.UUID]) -> uuid.UUID:
    """user + farmer + farm + one plot -> farm_id (cleanup: user cascade)."""
    user = User(email=f"an-{uuid.uuid4().hex[:12]}@example.com", password_hash="stored-hash")
    session.add(user)
    await session.commit()
    seeded.append(user.id)
    farmer = Farmer(user_id=user.id, full_name="Analysis Owner")
    session.add(farmer)
    await session.commit()
    farm = Farm(farmer_id=farmer.id, name="Analysis Farm")
    session.add(farm)
    await session.commit()
    session.add(Plot(farm_id=farm.id, name="Block A"))
    await session.commit()
    return farm.id


async def _cleanup(session, seeded_user_ids: list[uuid.UUID]) -> None:
    await session.rollback()
    if seeded_user_ids:
        await session.execute(delete(User).where(User.id.in_(seeded_user_ids)))
    await session.commit()
    await session.close()


async def test_analyze_farm_reads_the_stored_twin(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        farm_id = await _seed(session, seeded)
        plot = (await session.execute(select(Plot.id).where(Plot.farm_id == farm_id))).scalar_one()
        await set_plot_state(
            session, plot, crop="Maize", growth_stage="vegetative", planted_on=date(2026, 9, 19)
        )
        await put_signals(
            session,
            farm_id,
            signals={"weather": WEATHER, "satellite": SATELLITE, "soil": SOIL_DRY},
            refreshed_at=OBSERVED,
        )

        analysis = await analyze_farm(session, farm_id, now=NOW)

        assert analysis.decision.farm_id == farm_id
        assert analysis.state.view.name == "Analysis Farm"
        assert analysis.state.view.plot_count == 1
        assert analysis.state.signals.soil is not None  # cache -> normalize seam
        assert analysis.decision.health_level == analysis.health.level
        assert analysis.decision.risk_score == analysis.risk.score
        # dry soil in the cache reached the engines, not just the view
        assert analysis.decision.stance == "act_now"
        assert analysis.decision.action_counts["urgent"] > 0
    finally:
        await _cleanup(session, seeded)


async def test_analyze_farm_staleness_follows_the_injected_clock(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        farm_id = await _seed(session, seeded)
        plot = (await session.execute(select(Plot.id).where(Plot.farm_id == farm_id))).scalar_one()
        await set_plot_state(
            session, plot, crop="Maize", growth_stage="vegetative", planted_on=date(2026, 9, 19)
        )
        stale_at = NOW - timedelta(days=2)
        await put_signals(
            session,
            farm_id,
            signals={"weather": WEATHER_STALE, "satellite": SATELLITE, "soil": SOIL},
            refreshed_at=stale_at,
        )

        analysis = await analyze_farm(session, farm_id, now=NOW)

        assert analysis.decision.computed_at == NOW
        assert "weather" in analysis.decision.stale_families  # 48 h > 24 h threshold
        assert analysis.state.signals.refreshed_at == stale_at
    finally:
        await _cleanup(session, seeded)


async def test_analyze_farm_blind_farm_carries_the_data_gap(_db: None) -> None:
    session = get_sessionmaker()()
    seeded: list[uuid.UUID] = []
    try:
        farm_id = await _seed(session, seeded)
        plot = (await session.execute(select(Plot.id).where(Plot.farm_id == farm_id))).scalar_one()
        await set_plot_state(
            session, plot, crop="Maize", growth_stage="vegetative", planted_on=date(2026, 9, 19)
        )

        analysis = await analyze_farm(session, farm_id, now=NOW)

        assert analysis.state.signals.weather is None  # never ingested
        assert analysis.decision.plots_with_unknown_factors == 1
        assert analysis.decision.stance == "monitor"
    finally:
        await _cleanup(session, seeded)


async def test_analyze_farm_unknown_farm_is_not_found(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        with pytest.raises(NotFound):
            await analyze_farm(session, uuid.uuid4(), now=NOW)
    finally:
        await session.close()
