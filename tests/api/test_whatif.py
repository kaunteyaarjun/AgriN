"""API tests for the what-if endpoint (M045).

Authorization matrix (owner/officer/admin/non-owner/anon), response
shape (both runs + the diff, one clock), a real knob over HTTP, the
two accepted 422 flavors (pydantic structure vs M044's engine
semantics), and the read-only guarantee: a simulation never mutates
the stored twin. Fixture style copied from test_advisory.py (seeded
users, scoped cleanup; farm/plot/state residue is covered by FK
cascade).
"""

from __future__ import annotations

import asyncio
import functools
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, select, text
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import create_access_token, hash_password
from src.main import create_app
from src.models import Farm, Farmer, Plot, User, UserRole
from src.services.farm_state import get_farm_state, put_signals, set_plot_state

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = "/api/v1/farms"
PASSWORD = "Sup3rSecret-Pass!"
SEED_ROLES = (
    ("alpha", UserRole.farmer),  # owner
    ("bravo", UserRole.farmer),  # other tenant
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
)
OBSERVED = datetime.now(UTC) - timedelta(minutes=30)
SIGNALS: dict[str, dict[str, Any]] = {
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
DRY_SIGNALS: dict[str, dict[str, Any]] = {
    **SIGNALS,
    "soil": {**SIGNALS["soil"], "soil_moisture_pct": 10.0},
}
# weather family deliberately has no `source`: the rainfall knob must be
# rejected (unknown measurement window) rather than invent a timeframe.
WINDOWLESS_SIGNALS: dict[str, dict[str, Any]] = {
    "weather": {
        "temperature_c": 22.0,
        "rainfall_mm_24h": 5.0,
        "observed_at": OBSERVED.isoformat(),
    },
    "satellite": SIGNALS["satellite"],
    "soil": SIGNALS["soil"],
}


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


@functools.lru_cache(maxsize=1)
def _seed_password_hash() -> str:
    return hash_password(PASSWORD)


@pytest.fixture
async def _users(_db: None) -> AsyncGenerator[dict[str, User], None]:
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    password_hash = _seed_password_hash()
    for name, role in SEED_ROLES:
        user = User(
            email=f"wif-{name}-{uuid.uuid4().hex[:8]}@example.com",
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


async def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app())
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _profile_id(users: dict[str, User], name: str) -> uuid.UUID:
    session = get_sessionmaker()()
    try:
        profile_id = await session.scalar(select(Farmer.id).where(Farmer.user_id == users[name].id))
        assert profile_id is not None
        return profile_id
    finally:
        await session.close()


async def _seed_ready_farm(
    users: dict[str, User],
    owner: str = "alpha",
    *,
    signals: dict[str, dict[str, Any]] | None = SIGNALS,
) -> uuid.UUID:
    """Farm + one planted plot (+ optional signal cache) for ``owner``.

    Seeded through the services directly: M045's route must not depend
    on M020's endpoints for its own setup.
    """
    farmer_id = await _profile_id(users, owner)
    session = get_sessionmaker()()
    try:
        farm = Farm(farmer_id=farmer_id, name=f"Wif Farm {uuid.uuid4().hex[:6]}")
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
        if signals is not None:
            await put_signals(session, farm.id, signals=signals, refreshed_at=OBSERVED)
        return farm.id
    finally:
        await session.close()


async def _what_if(
    client: httpx.AsyncClient,
    farm_id: uuid.UUID,
    user: User | None,
    overrides: dict[str, dict[str, Any]],
) -> httpx.Response:
    headers = None if user is None else _headers(user)
    return await client.post(
        f"{BASE}/{farm_id}/what-if", json={"overrides": overrides}, headers=headers
    )


# ---------- shape ----------


async def test_response_carries_both_runs_the_diff_and_no_advisory(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_ready_farm(_users)
    async with await _client() as client:
        got = await _what_if(client, farm_id, _users["alpha"], {"soil": {"ph": 7.9}})
    assert got.status_code == 200, got.text
    body = got.json()
    assert set(body) == {
        "baseline",
        "hypothetical",
        "changes",
        "overrides_applied",
        "simulated_families",
    }
    assert "advisory" not in body  # M041 is never called (decision 2026-09-30)

    baseline, hypothetical = body["baseline"], body["hypothetical"]
    assert baseline["state"]["view"]["farm_id"] == str(farm_id)
    assert hypothetical["state"]["view"]["farm_id"] == str(farm_id)
    for engine in ("health", "risk", "recommendations", "decision"):
        assert baseline[engine]["computed_at"] == hypothetical[engine]["computed_at"]  # one clock
    assert baseline["decision"]["farm_id"] == str(farm_id)
    assert body["overrides_applied"] == {"soil": {"ph": 7.9}}
    assert body["simulated_families"] == ["soil"]


# ---------- authorization matrix ----------


async def test_read_matrix(_users: dict[str, User]) -> None:
    farm_id = await _seed_ready_farm(_users)
    unknown = uuid.uuid4()
    async with await _client() as client:
        officer = await _what_if(client, farm_id, _users["officer"], {"soil": {"ph": 7.0}})
        admin = await _what_if(client, farm_id, _users["admin"], {"soil": {"ph": 7.0}})
        non_owner = await _what_if(client, farm_id, _users["bravo"], {"soil": {"ph": 7.0}})
        anon = await _what_if(client, farm_id, None, {"soil": {"ph": 7.0}})
        missing = await _what_if(client, unknown, _users["admin"], {"soil": {"ph": 7.0}})
        malformed = await client.post(
            f"{BASE}/not-a-uuid/what-if",
            json={"overrides": {"soil": {"ph": 7.0}}},
            headers=_headers(_users["alpha"]),
        )
    assert [officer.status_code, admin.status_code] == [200, 200]
    assert non_owner.status_code == 404  # no existence oracle
    assert non_owner.json()["error_code"] == "not_found"
    assert anon.status_code == 401
    assert anon.json()["error_code"] == "not_authenticated"
    assert missing.status_code == 404
    assert malformed.status_code == 422


# ---------- a knob over HTTP really moves the answer ----------


async def test_knob_reaches_the_engine_and_drops_the_urgent_action(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_ready_farm(_users, signals=DRY_SIGNALS)
    async with await _client() as client:
        got = await _what_if(
            client, farm_id, _users["alpha"], {"soil": {"soil_moisture_pct": 45.0}}
        )
    assert got.status_code == 200, got.text
    body = got.json()
    assert body["baseline"]["decision"]["stance"] == "act_now"
    changes = body["changes"]
    assert changes["actions_removed"]  # the irrigation action left the list
    assert changes["action_counts_delta"]["urgent"] < 0


# ---------- both 422 origins, one envelope (M055) ----------


async def test_structural_errors_are_pydantic_422(_users: dict[str, User]) -> None:
    farm_id = await _seed_ready_farm(_users)
    async with await _client() as client:
        missing = await client.post(
            f"{BASE}/{farm_id}/what-if", json={}, headers=_headers(_users["alpha"])
        )
        not_a_mapping = await _what_if(
            client,
            farm_id,
            _users["alpha"],
            {"weather": "oops"},  # type: ignore[dict-item]
        )
    assert missing.status_code == 422
    assert missing.json()["error_code"] == "validation_failed"
    assert "overrides" in missing.json()["message"]
    assert not_a_mapping.status_code == 422
    assert not_a_mapping.json()["error_code"] == "validation_failed"
    assert "detail" not in not_a_mapping.json()  # M055: one shape everywhere


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({}, "no what-if overrides"),
        ({"rain": {"mm": 1.0}}, "unknown what-if family"),
        ({"weather": {"dew_point_c": 5.0}}, "unknown what-if knob"),
        ({"soil": {"ph": 20.0}}, "outside the allowed range"),
        ({"satellite": {"ndvi": 2.0}}, "outside the allowed range"),
    ],
)
async def test_engine_rejections_are_validation_failed(
    _users: dict[str, User], overrides: dict[str, dict[str, Any]], fragment: str
) -> None:
    farm_id = await _seed_ready_farm(_users)
    async with await _client() as client:
        got = await _what_if(client, farm_id, _users["alpha"], overrides)
    assert got.status_code == 422, got.text
    body = got.json()
    assert body["error_code"] == "validation_failed"
    assert fragment in body["message"]  # the message names the offending knob


async def test_windowless_rainfall_is_rejected_over_http(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_ready_farm(_users, signals=WINDOWLESS_SIGNALS)
    async with await _client() as client:
        got = await _what_if(
            client, farm_id, _users["alpha"], {"weather": {"rainfall_mm_24h": 0.0}}
        )
    assert got.status_code == 422, got.text
    assert got.json()["error_code"] == "validation_failed"
    assert "measurement window" in got.json()["message"]


# ---------- a simulation never writes ----------


async def test_simulation_leaves_the_stored_twin_untouched(
    _users: dict[str, User],
) -> None:
    farm_id = await _seed_ready_farm(_users)
    async with await _client() as client:
        got = await _what_if(client, farm_id, _users["alpha"], {"satellite": {"ndvi": 0.1}})
    assert got.status_code == 200, got.text

    session = get_sessionmaker()()
    try:
        view = await get_farm_state(session, farm_id)
    finally:
        await session.close()
    assert view.signals.signals == SIGNALS  # byte-identical to what was seeded
    assert view.signals.refreshed_at == OBSERVED
