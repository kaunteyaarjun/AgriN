"""API tests for the advisory endpoint (M043).

Authorization matrix (owner/officer/admin/non-owner/anon) against dev
Postgres, response shape (prose + decision from one run), the blind-farm
data gap travelling into the advisory's caveats, and the single
provider-failure path: any ``ProviderError`` — unreachable upstream or
M041's output policy rejecting the answer — becomes one sanitized 502.
Fixture style copied from test_farm_state.py (seeded users, scoped
cleanup; farm/plot/state residue is covered by FK cascade).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import delete, select
from src.ai.advisory import Advisory
from src.core.db import get_sessionmaker
from src.engines import DECISION_STANCES, FarmDecision
from src.models import Farm, Farmer, Plot, User, UserRole
from src.providers.errors import ProviderResponseInvalid, ProviderUnavailable
from src.services.farm_state import put_signals, set_plot_state

from tests.conftest import _client, _headers, _seed_password_hash

BASE = "/api/v1/farms"
SEED_ROLES = (
    ("alpha", UserRole.farmer),  # owner
    ("bravo", UserRole.farmer),  # other tenant
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
)
OBSERVED = datetime.now(UTC) - timedelta(minutes=30)
SIGNALS = {
    "weather": {
        "temperature_c": 22.0,
        "humidity_pct": 55.0,
        "rainfall_mm_24h": 5.0,
        "wind_speed_kmh": 10.0,
        "condition": "clear",
        "observed_at": OBSERVED.isoformat(),
        "source": "demo-weather-v1",
    },
    "satellite": {
        "ndvi": 0.62,
        "cloud_cover_pct": 10.0,
        "observed_at": OBSERVED.isoformat(),
        "source": "demo-satellite-v1",
    },
    "soil": {
        "soil_moisture_pct": 45.0,
        "ph": 6.5,
        "soil_temperature_c": 18.0,
        "nitrogen_kg_ha": 60.0,
        "observed_at": OBSERVED.isoformat(),
        "source": "demo-soil-v1",
    },
}


@pytest.fixture
async def _users(_db: None) -> AsyncGenerator[dict[str, User], None]:
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    password_hash = _seed_password_hash()
    for name, role in SEED_ROLES:
        user = User(
            email=f"adv-{name}-{uuid.uuid4().hex[:8]}@example.com",
            password_hash=password_hash,
            role=role,
        )
        session.add(user)
        users[name] = user
    await session.commit()
    for name in ("alpha", "bravo"):
        session.add(Farmer(user_id=users[name].id, full_name=f"Profile {name.title()}"))
    await session.commit()
    try:
        yield users
    finally:
        await session.rollback()
        await session.execute(delete(User).where(User.email.in_([u.email for u in users.values()])))
        await session.commit()
        await session.close()


async def _profile_id(users: dict[str, User], name: str) -> uuid.UUID:
    session = get_sessionmaker()()
    try:
        profile_id = await session.scalar(select(Farmer.id).where(Farmer.user_id == users[name].id))
        assert profile_id is not None
        return profile_id
    finally:
        await session.close()


async def _seed_ready_farm(
    users: dict[str, User], owner: str = "alpha", *, with_signals: bool = True
) -> uuid.UUID:
    """Farm + one planted plot (+ full signal cache) for ``owner``.

    Seeded through the services directly: M043's route must not depend
    on M020's endpoints for its own setup.
    """
    farmer_id = await _profile_id(users, owner)
    session = get_sessionmaker()()
    try:
        farm = Farm(farmer_id=farmer_id, name=f"Adv Farm {uuid.uuid4().hex[:6]}")
        session.add(farm)
        await session.commit()
        plot = Plot(farm_id=farm.id, name="Block A")
        session.add(plot)
        await session.commit()
        await set_plot_state(
            session,
            plot.id,
            crop="Maize",
            growth_stage="vegetative",
            planted_on=date.today() - timedelta(days=20),
        )
        if with_signals:
            await put_signals(session, farm.id, signals=SIGNALS, refreshed_at=OBSERVED)
        return farm.id
    finally:
        await session.close()


async def _get_advisory(
    client: httpx.AsyncClient, farm_id: uuid.UUID, user: User | None
) -> httpx.Response:
    headers = None if user is None else _headers(user)
    return await client.get(f"{BASE}/{farm_id}/advisory", headers=headers)


# ---------- shape ----------


async def test_owner_gets_prose_and_decision_from_one_run(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_ready_farm(_users)
    async with await _client() as client:
        got = await _get_advisory(client, farm_id, _users["alpha"])
    assert got.status_code == 200, got.text
    body = got.json()
    assert set(body) == {"advisory", "decision"}

    advisory = Advisory.model_validate(body["advisory"])
    decision = FarmDecision.model_validate(body["decision"])
    assert advisory.farm_id == farm_id == decision.farm_id
    assert advisory.stance == decision.stance
    assert advisory.stance in DECISION_STANCES
    assert advisory.text.strip()
    assert advisory.source and advisory.finish_reason
    assert decision.plot_count == 1
    assert decision.health_level == "healthy"
    assert decision.computed_at is not None


async def test_blind_farm_still_answers_and_carries_the_data_gap(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_ready_farm(_users, with_signals=False)
    async with await _client() as client:
        got = await _get_advisory(client, farm_id, _users["alpha"])
    assert got.status_code == 200, got.text
    body = got.json()
    assert body["advisory"]["caveats"]  # M041 honesty, now over HTTP
    assert body["decision"]["plots_with_unknown_factors"] == 1
    assert body["decision"]["stance"] == "monitor"


# ---------- authorization matrix ----------


async def test_read_matrix(_users: dict[str, User]) -> None:
    farm_id = await _seed_ready_farm(_users)
    unknown = uuid.uuid4()
    async with await _client() as client:
        officer = await _get_advisory(client, farm_id, _users["officer"])
        admin = await _get_advisory(client, farm_id, _users["admin"])
        non_owner = await _get_advisory(client, farm_id, _users["bravo"])
        anon = await _get_advisory(client, farm_id, None)
        missing = await _get_advisory(client, unknown, _users["admin"])
        malformed = await client.get(
            f"{BASE}/not-a-uuid/advisory", headers=_headers(_users["alpha"])
        )
    assert [officer.status_code, admin.status_code] == [200, 200]
    assert non_owner.status_code == 404  # no existence oracle
    assert non_owner.json()["error_code"] == "not_found"
    assert anon.status_code == 401
    assert anon.json()["error_code"] == "not_authenticated"
    assert missing.status_code == 404
    assert malformed.status_code == 422


# ---------- provider failure: one sanitized 502 ----------


async def test_unreachable_provider_maps_to_502(
    _users: dict[str, User], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _boom(_decision: FarmDecision) -> Advisory:
        raise ProviderUnavailable("connection refused to internal host")

    monkeypatch.setattr("src.api.v1.advisory.generate_advisory", _boom)
    farm_id = await _seed_ready_farm(_users)
    async with await _client() as client:
        got = await _get_advisory(client, farm_id, _users["alpha"])
    assert got.status_code == 502
    body = got.json()
    assert body["error_code"] == "upstream_unavailable"
    assert "internal host" not in body["message"]  # sanitized for the client


async def test_rejected_model_output_maps_to_the_same_502(
    _users: dict[str, User], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _invalid(_decision: FarmDecision) -> Advisory:
        raise ProviderResponseInvalid("text echoed the system instruction")

    monkeypatch.setattr("src.api.v1.advisory.generate_advisory", _invalid)
    farm_id = await _seed_ready_farm(_users)
    async with await _client() as client:
        got = await _get_advisory(client, farm_id, _users["alpha"])
    assert got.status_code == 502
    assert got.json()["error_code"] == "upstream_unavailable"
    assert "system instruction" not in got.json()["message"]
