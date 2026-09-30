"""API tests for the Farm State endpoints (M020).

Full authorization matrix (owner/officer/admin/non-owner/anon) for the
four routes, cross-farm and unknown-id paths, validation shapes (both
422 flavors: pydantic ``detail`` and AppError ``error_code``), and
idempotent PUT/DELETE behavior — against dev Postgres. Fixture style
copied from test_farms.py (seeded users, scoped cleanup; farm/plot/
state residue is covered by FK cascade when the users are deleted).
"""

from __future__ import annotations

import asyncio
import functools
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import delete, select, text
from src.api.v1.farm_state import MAX_SIGNAL_JSON_CHARS, PlotStateUpsert, SignalsUpsert
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import create_access_token, hash_password
from src.main import create_app
from src.models import Farm, Farmer, Plot, User, UserRole

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = "/api/v1/farms"
PASSWORD = "Sup3rSecret-Pass!"
SEED_ROLES = (
    ("alpha", UserRole.farmer),  # owner
    ("bravo", UserRole.farmer),  # other tenant
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
)

PLANTED_ON = "2020-01-01"
STATE_BODY = {"crop": "Maize", "growth_stage": "vegetative", "planted_on": PLANTED_ON}


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
            email=f"fsapi-{name}-{uuid.uuid4().hex[:8]}@example.com",
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


async def _seed_farm_with_plot(
    users: dict[str, User], owner: str = "alpha"
) -> tuple[uuid.UUID, uuid.UUID]:
    """Farm + one plot for ``owner`` (setup helper; cascade-cleaned with users)."""
    farmer_id = await _profile_id(users, owner)
    session = get_sessionmaker()()
    try:
        farm = Farm(farmer_id=farmer_id, name=f"State Farm {uuid.uuid4().hex[:6]}", area_hectares=2)
        session.add(farm)
        await session.commit()
        plot = Plot(farm_id=farm.id, name="State Block")
        session.add(plot)
        await session.commit()
        return farm.id, plot.id
    finally:
        await session.close()


def _state_url(farm_id: uuid.UUID, plot_id: uuid.UUID) -> str:
    return f"{BASE}/{farm_id}/plots/{plot_id}/state"


# ---------- request-model validation (pure pydantic, no DB) ----------


def test_plot_state_upsert_validation() -> None:
    PlotStateUpsert.model_validate(STATE_BODY)
    for bad in (
        {**STATE_BODY, "growth_stage": "miracle"},
        {**STATE_BODY, "crop": ""},
        {**STATE_BODY, "crop": "x" * 81},
        {**STATE_BODY, "planted_on": "not-a-date"},
        {**STATE_BODY, "growth_stage": "Vegetative"},
    ):
        with pytest.raises(ValidationError):
            PlotStateUpsert.model_validate(bad)


def test_signals_upsert_validation() -> None:
    small = SignalsUpsert.model_validate({"signals": {"weather": {"temp_c": 25}}})
    assert small.refreshed_at is None

    naive = SignalsUpsert.model_validate({"signals": {}, "refreshed_at": "2026-01-02T03:04:05"})
    assert naive.refreshed_at is not None
    assert naive.refreshed_at.tzinfo is not None  # UTC attached

    aware = SignalsUpsert.model_validate(
        {"signals": {}, "refreshed_at": "2026-01-02T03:04:05+02:00"}
    )
    assert aware.refreshed_at is not None
    assert aware.refreshed_at.utcoffset() is not None
    assert aware.refreshed_at.hour == 3  # preserved, not rewritten

    with pytest.raises(ValidationError):
        SignalsUpsert.model_validate({"signals": {"blob": "x" * (MAX_SIGNAL_JSON_CHARS + 1)}})


# ---------- auth ----------


async def test_anonymous_requests_get_401(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        responses = [
            await client.get(f"{BASE}/{farm_id}/state"),
            await client.put(_state_url(farm_id, plot_id), json=STATE_BODY),
            await client.delete(_state_url(farm_id, plot_id)),
            await client.put(f"{BASE}/{farm_id}/signals", json={"signals": {}}),
        ]
    assert [r.status_code for r in responses] == [401, 401, 401, 401]
    assert all(r.json()["error_code"] == "not_authenticated" for r in responses)


# ---------- GET state ----------


async def test_get_state_full_view_for_owner(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        put = await client.put(
            _state_url(farm_id, plot_id), json=STATE_BODY, headers=_headers(_users["alpha"])
        )
        assert put.status_code == 204, put.text
        sig = await client.put(
            f"{BASE}/{farm_id}/signals",
            json={"signals": {"weather": {"temp_c": 26.5}}},
            headers=_headers(_users["alpha"]),
        )
        assert sig.status_code == 204, sig.text

        got = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["alpha"]))
        assert got.status_code == 200, got.text
        body = got.json()
        assert body["farm_id"] == str(farm_id)
        assert body["plot_count"] == 1
        assert body["planted_plot_count"] == 1
        assert body["crops"] == ["Maize"]
        plot = body["plots"][0]
        assert plot["plot_id"] == str(plot_id)
        assert plot["crop"] == "Maize"
        assert plot["growth_stage"] == "vegetative"
        assert plot["planted_on"] == PLANTED_ON
        assert plot["days_since_planted"] > 2000  # planted 2020-01-01
        assert body["signals"]["signals"] == {"weather": {"temp_c": 26.5}}
        assert body["signals"]["refreshed_at"] is not None
        assert body["signals"]["age_seconds"] >= 0  # just written: sub-second, truncated


async def test_get_state_matrix_and_path_validation(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        officer = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["officer"]))
        admin = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["admin"]))
        non_owner = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["bravo"]))
        malformed = await client.get(f"{BASE}/not-a-uuid/state", headers=_headers(_users["alpha"]))
    assert officer.status_code == 200
    assert admin.status_code == 200
    assert non_owner.status_code == 404
    assert non_owner.json()["error_code"] == "not_found"
    assert malformed.status_code == 422  # uuid path param shape


# ---------- PUT plot state ----------


async def test_put_plot_state_idempotent_second_wins(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    first = {**STATE_BODY, "growth_stage": "germination"}
    second = {**STATE_BODY, "crop": "Wheat", "growth_stage": "flowering"}
    async with await _client() as client:
        r1 = await client.put(
            _state_url(farm_id, plot_id), json=first, headers=_headers(_users["alpha"])
        )
        r2 = await client.put(
            _state_url(farm_id, plot_id), json=second, headers=_headers(_users["alpha"])
        )
        got = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["alpha"]))
    assert [r1.status_code, r2.status_code] == [204, 204]
    plot = got.json()["plots"][0]
    assert plot["crop"] == "Wheat"
    assert plot["growth_stage"] == "flowering"
    assert got.json()["planted_plot_count"] == 1


async def test_put_plot_state_matrix(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    other_farm_id, other_plot_id = await _seed_farm_with_plot(_users, owner="bravo")
    async with await _client() as client:
        officer = await client.put(
            _state_url(farm_id, plot_id), json=STATE_BODY, headers=_headers(_users["officer"])
        )
        non_owner = await client.put(
            _state_url(farm_id, plot_id), json=STATE_BODY, headers=_headers(_users["bravo"])
        )
        admin = await client.put(
            _state_url(farm_id, plot_id), json=STATE_BODY, headers=_headers(_users["admin"])
        )
        unknown_plot = await client.put(
            _state_url(farm_id, uuid.uuid4()), json=STATE_BODY, headers=_headers(_users["alpha"])
        )
        cross_farm = await client.put(
            _state_url(farm_id, other_plot_id),
            json=STATE_BODY,
            headers=_headers(_users["alpha"]),
        )
        unknown_farm = await client.put(
            _state_url(uuid.uuid4(), plot_id), json=STATE_BODY, headers=_headers(_users["alpha"])
        )
    assert officer.status_code == 403
    assert officer.json()["error_code"] == "permission_denied"
    assert non_owner.status_code == 404
    assert admin.status_code == 204
    assert unknown_plot.status_code == 404
    assert cross_farm.status_code == 404  # plot scoped to URL farm
    assert unknown_farm.status_code == 404
    assert other_farm_id != farm_id and other_plot_id != plot_id  # sanity


async def test_put_plot_state_validation_shapes(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        bad_stage = await client.put(
            _state_url(farm_id, plot_id),
            json={**STATE_BODY, "growth_stage": "miracle"},
            headers=_headers(_users["alpha"]),
        )
        blank_crop = await client.put(
            _state_url(farm_id, plot_id),
            json={**STATE_BODY, "crop": "   "},
            headers=_headers(_users["alpha"]),
        )
    # M055: every 422 answers the same envelope, whatever raised it
    assert bad_stage.status_code == 422
    assert bad_stage.json()["error_code"] == "validation_failed"
    assert "growth_stage" in bad_stage.json()["message"]
    # AppError shape: {error_code, message} from the service
    assert blank_crop.status_code == 422
    assert blank_crop.json()["error_code"] == "validation_failed"
    # rejected calls wrote nothing
    async with await _client() as client:
        got = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["alpha"]))
    assert got.json()["planted_plot_count"] == 0


# ---------- DELETE plot state ----------


async def test_delete_plot_state_idempotent(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        await client.put(
            _state_url(farm_id, plot_id), json=STATE_BODY, headers=_headers(_users["alpha"])
        )
        d1 = await client.delete(_state_url(farm_id, plot_id), headers=_headers(_users["alpha"]))
        d2 = await client.delete(_state_url(farm_id, plot_id), headers=_headers(_users["alpha"]))
        got = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["alpha"]))
    assert [d1.status_code, d2.status_code] == [204, 204]
    assert got.json()["planted_plot_count"] == 0
    assert got.json()["plots"][0]["crop"] is None
    assert got.json()["plots"][0]["days_since_planted"] is None


async def test_delete_plot_state_matrix(_users: dict[str, User]) -> None:
    farm_id, plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        await client.put(
            _state_url(farm_id, plot_id), json=STATE_BODY, headers=_headers(_users["alpha"])
        )
        officer = await client.delete(
            _state_url(farm_id, plot_id), headers=_headers(_users["officer"])
        )
        non_owner = await client.delete(
            _state_url(farm_id, plot_id), headers=_headers(_users["bravo"])
        )
        unknown = await client.delete(
            _state_url(farm_id, uuid.uuid4()), headers=_headers(_users["alpha"])
        )
        admin = await client.delete(_state_url(farm_id, plot_id), headers=_headers(_users["admin"]))
    assert officer.status_code == 403
    assert non_owner.status_code == 404
    assert unknown.status_code == 404
    assert admin.status_code == 204


# ---------- PUT signals ----------


async def test_put_signals_reflected_in_state(_users: dict[str, User]) -> None:
    farm_id, _plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        put = await client.put(
            f"{BASE}/{farm_id}/signals",
            json={"signals": {"satellite": {"ndvi": 0.61}}, "refreshed_at": "2026-01-02T03:04:05"},
            headers=_headers(_users["alpha"]),
        )
        assert put.status_code == 204, put.text
        got = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["alpha"]))
    signals = got.json()["signals"]
    assert signals["signals"] == {"satellite": {"ndvi": 0.61}}
    # naive input stored as UTC (timestamptz column), echoed aware
    assert datetime.fromisoformat(signals["refreshed_at"]) == datetime(
        2026, 1, 2, 3, 4, 5, tzinfo=UTC
    )
    assert isinstance(signals["age_seconds"], int)


async def test_put_signals_matrix_and_validation(_users: dict[str, User]) -> None:
    farm_id, _plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        officer = await client.put(
            f"{BASE}/{farm_id}/signals",
            json={"signals": {}},
            headers=_headers(_users["officer"]),
        )
        non_owner = await client.put(
            f"{BASE}/{farm_id}/signals", json={"signals": {}}, headers=_headers(_users["bravo"])
        )
        unknown_farm = await client.put(
            f"{BASE}/{uuid.uuid4()}/signals",
            json={"signals": {}},
            headers=_headers(_users["alpha"]),
        )
        admin = await client.put(
            f"{BASE}/{farm_id}/signals",
            json={"signals": {"soil": {"moisture": 0.3}}},
            headers=_headers(_users["admin"]),
        )
        oversize = await client.put(
            f"{BASE}/{farm_id}/signals",
            json={"signals": {"blob": "x" * (MAX_SIGNAL_JSON_CHARS + 1)}},
            headers=_headers(_users["alpha"]),
        )
        empty_doc = await client.put(
            f"{BASE}/{farm_id}/signals", json={"signals": {}}, headers=_headers(_users["alpha"])
        )
    assert officer.status_code == 403
    assert non_owner.status_code == 404
    assert unknown_farm.status_code == 404
    assert admin.status_code == 204
    assert oversize.status_code == 422
    assert empty_doc.status_code == 204  # wholesale replace with {} is legal


async def test_signals_wholesale_replace(_users: dict[str, User]) -> None:
    farm_id, _plot_id = await _seed_farm_with_plot(_users)
    async with await _client() as client:
        await client.put(
            f"{BASE}/{farm_id}/signals",
            json={"signals": {"weather": {"temp_c": 30}, "soil": {"ph": 6.5}}},
            headers=_headers(_users["alpha"]),
        )
        await client.put(
            f"{BASE}/{farm_id}/signals",
            json={"signals": {"satellite": {"ndvi": 0.42}}},
            headers=_headers(_users["alpha"]),
        )
        got = await client.get(f"{BASE}/{farm_id}/state", headers=_headers(_users["alpha"]))
    assert got.json()["signals"]["signals"] == {"satellite": {"ndvi": 0.42}}  # old keys gone


async def test_datetime_helpers_are_utc_safe() -> None:
    """Spot-check: SignalsUpsert's tz attach yields aware UTC datetimes."""
    value = SignalsUpsert.model_validate(
        {"signals": {}, "refreshed_at": datetime(2026, 1, 2, 3, 4, 5)}
    ).refreshed_at
    assert value == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
