"""API tests for plot CRUD + ownership (M016): full authorization matrix,
plot-within-farm containment (ST_Covers) and GeoJSON round trip.

Fixtures seed users, farmer profiles and one farm per farmer (farm A with
a boundary, farm B without) directly; scoped cleanup via user cascade.
"""

from __future__ import annotations

import asyncio
import functools
import json
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx
import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import delete, func, select, text
from src.api.v1.plots import PlotCreate, PlotPatch
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import create_access_token, hash_password
from src.main import create_app
from src.models import Farm, Farmer, User, UserRole

REPO_ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "Sup3rSecret-Pass!"
SEED_ROLES = (
    ("alpha", UserRole.farmer),
    ("bravo", UserRole.farmer),
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
)

FARM_A_GEO: dict[str, object] = {  # large boundary owned by alpha (covers POLYGON)
    "type": "Polygon",
    "coordinates": [[[36.7, -1.3], [36.8, -1.3], [36.8, -1.2], [36.7, -1.3]]],
}
POLYGON: dict[str, object] = {  # inside FARM_A_GEO
    "type": "Polygon",
    "coordinates": [[[36.75, -1.29], [36.76, -1.29], [36.76, -1.28], [36.75, -1.29]]],
}
OUTSIDE: dict[str, object] = {  # outside FARM_A_GEO
    "type": "Polygon",
    "coordinates": [[[37.0, -2.0], [37.1, -2.0], [37.1, -1.9], [37.0, -2.0]]],
}


def base(farm_id: uuid.UUID) -> str:
    return f"/api/v1/farms/{farm_id}/plots"


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
async def _ctx(_db: None) -> AsyncGenerator[dict[str, Any], None]:
    """users (alpha/bravo/officer/admin) + farm A (alpha, mapped) +
    farm B (bravo, no boundary). Always cleaned up."""
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    password_hash = _seed_password_hash()
    for name, role in SEED_ROLES:
        user = User(
            email=f"plot-{name}-{uuid.uuid4().hex[:8]}@example.com",
            password_hash=password_hash,
            role=role,
        )
        session.add(user)
        users[name] = user
    await session.commit()
    for name in ("alpha", "bravo"):
        session.add(Farmer(user_id=users[name].id, full_name=f"Profile {name.title()}"))
    await session.commit()
    profiles = {
        name: (
            await session.execute(select(Farmer.id).where(Farmer.user_id == users[name].id))
        ).scalar_one()
        for name in ("alpha", "bravo")
    }
    farm_a = Farm(farmer_id=profiles["alpha"], name="Farm A")
    farm_a.geo = func.ST_GeomFromGeoJSON(json.dumps(FARM_A_GEO))
    farm_b = Farm(farmer_id=profiles["bravo"], name="Farm B")
    session.add_all([farm_a, farm_b])
    await session.commit()
    try:
        yield {"users": users, "farm_a": farm_a.id, "farm_b": farm_b.id}
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


def _create_body(**extra: object) -> dict[str, object]:
    body: dict[str, object] = {"name": "Block A"}
    body.update(extra)
    return body


def test_empty_patch_rejected() -> None:
    with pytest.raises(ValidationError):
        PlotPatch.model_validate({})
    with pytest.raises(ValidationError):
        PlotPatch.model_validate({"area_hectares": -1})
    PlotPatch.model_validate({"geo": None})  # explicit clear allowed


def test_create_schema_rejects_bad_geo() -> None:
    with pytest.raises(ValidationError):
        PlotCreate.model_validate({"name": "x", "geo": {"type": "Point", "coordinates": [1, 2]}})
    PlotCreate.model_validate({"name": "x", "geo": POLYGON})


async def test_anonymous_requests_get_401(_ctx: dict[str, Any]) -> None:
    farm_id = _ctx["farm_a"]
    any_id = str(uuid.uuid4())
    async with await _client() as client:
        responses = [
            await client.post(base(farm_id), json=_create_body()),
            await client.get(base(farm_id)),
            await client.get(f"{base(farm_id)}/{any_id}"),
            await client.patch(f"{base(farm_id)}/{any_id}", json={"name": "X"}),
            await client.delete(f"{base(farm_id)}/{any_id}"),
        ]
    assert [r.status_code for r in responses] == [401, 401, 401, 401, 401]
    assert all(r.json()["error_code"] == "not_authenticated" for r in responses)


async def test_owner_create_geo_round_trip(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_id = _ctx["farm_a"]
    async with await _client() as client:
        created = await client.post(
            base(farm_id), json=_create_body(geo=POLYGON), headers=_headers(users["alpha"])
        )
        assert created.status_code == 201, created.text
        assert created.json()["geo"] == POLYGON
        assert created.json()["farm_id"] == str(farm_id)

        fetched = await client.get(
            f"{base(farm_id)}/{created.json()['id']}", headers=_headers(users["alpha"])
        )
        assert fetched.status_code == 200
        assert fetched.json()["geo"] == POLYGON


async def test_non_owner_farmer_gets_404_everywhere(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_a = _ctx["farm_a"]
    farm_b = _ctx["farm_b"]
    async with await _client() as client:
        owner_headers = _headers(users["alpha"])
        created = await client.post(base(farm_a), json=_create_body(), headers=owner_headers)
        plot_id = created.json()["id"]
        stranger = _headers(users["bravo"])
        responses = [
            await client.post(base(farm_a), json=_create_body(), headers=stranger),
            await client.get(base(farm_a), headers=stranger),
            await client.get(f"{base(farm_a)}/{plot_id}", headers=stranger),
            await client.patch(f"{base(farm_a)}/{plot_id}", json={"name": "H"}, headers=stranger),
            await client.delete(f"{base(farm_a)}/{plot_id}", headers=stranger),
            # cross-farm plot id through the stranger's own farm URL
            await client.get(f"{base(farm_b)}/{plot_id}", headers=stranger),
        ]
    assert [r.status_code for r in responses] == [404, 404, 404, 404, 404, 404]


async def test_officer_read_only(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_id = _ctx["farm_a"]
    async with await _client() as client:
        created = await client.post(
            base(farm_id), json=_create_body(), headers=_headers(users["alpha"])
        )
        plot_id = created.json()["id"]
        officer = _headers(users["officer"])
        post = await client.post(base(farm_id), json=_create_body(), headers=officer)
        listing = await client.get(base(farm_id), headers=officer)
        fetched = await client.get(f"{base(farm_id)}/{plot_id}", headers=officer)
        patch = await client.patch(
            f"{base(farm_id)}/{plot_id}", json={"name": "X"}, headers=officer
        )
        delete = await client.delete(f"{base(farm_id)}/{plot_id}", headers=officer)
    assert post.status_code == 403
    assert listing.status_code == 200 and listing.json()["total"] == 1
    assert fetched.status_code == 200
    assert patch.status_code == 403
    assert delete.status_code == 403


async def test_admin_full_access(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_id = _ctx["farm_a"]
    async with await _client() as client:
        created = await client.post(
            base(farm_id), json=_create_body(area_hectares="2.5"), headers=_headers(users["admin"])
        )
        assert created.status_code == 201, created.text
        plot_id = created.json()["id"]
        patched = await client.patch(
            f"{base(farm_id)}/{plot_id}",
            json={"area_hectares": 3},
            headers=_headers(users["admin"]),
        )
        removed = await client.delete(
            f"{base(farm_id)}/{plot_id}", headers=_headers(users["admin"])
        )
    assert patched.status_code == 200
    assert patched.json()["area_hectares"] == "3.00"
    assert removed.status_code == 204


async def test_duplicate_name_scope_per_farm(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_a = _ctx["farm_a"]
    farm_b = _ctx["farm_b"]
    async with await _client() as client:
        first = await client.post(
            base(farm_a), json=_create_body(), headers=_headers(users["alpha"])
        )
        dup = await client.post(base(farm_a), json=_create_body(), headers=_headers(users["alpha"]))
        other_farm = await client.post(
            base(farm_b), json=_create_body(), headers=_headers(users["admin"])
        )
    assert first.status_code == 201
    assert dup.status_code == 409
    assert dup.json()["error_code"] == "conflict"
    assert other_farm.status_code == 201  # same name in a different farm is fine


async def test_containment_outside_farm_rejected(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_id = _ctx["farm_a"]
    async with await _client() as client:
        headers = _headers(users["alpha"])
        rejected = await client.post(base(farm_id), json=_create_body(geo=OUTSIDE), headers=headers)
        inside = await client.post(base(farm_id), json=_create_body(geo=POLYGON), headers=headers)
        listing = await client.get(base(farm_id), headers=headers)
    assert rejected.status_code == 422
    assert rejected.json()["error_code"] == "validation_failed"
    assert inside.status_code == 201
    assert listing.json()["total"] == 1  # the rejected one never persisted


async def test_unmapped_farm_skips_containment(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_b = _ctx["farm_b"]
    async with await _client() as client:
        # farm B has no boundary yet — any valid geo is accepted
        response = await client.post(
            base(farm_b), json=_create_body(geo=OUTSIDE), headers=_headers(users["admin"])
        )
    assert response.status_code == 201, response.text


async def test_list_per_farm_with_privileged_views(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_a = _ctx["farm_a"]
    farm_b = _ctx["farm_b"]
    async with await _client() as client:
        await client.post(
            base(farm_a), json=_create_body(name="A1"), headers=_headers(users["alpha"])
        )
        await client.post(
            base(farm_a), json=_create_body(name="A2"), headers=_headers(users["alpha"])
        )
        await client.post(
            base(farm_b), json=_create_body(name="B1"), headers=_headers(users["admin"])
        )
        alpha_on_a = await client.get(base(farm_a), headers=_headers(users["alpha"]))
        officer_on_a = await client.get(base(farm_a), headers=_headers(users["officer"]))
        admin_on_b = await client.get(base(farm_b), headers=_headers(users["admin"]))
    assert alpha_on_a.json()["total"] == 2
    assert {i["name"] for i in alpha_on_a.json()["items"]} == {"A1", "A2"}
    assert officer_on_a.json()["total"] == 2
    assert admin_on_b.json()["total"] == 1
    assert admin_on_b.json()["items"][0]["name"] == "B1"


async def test_patch_matrix_and_geo_containment(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_id = _ctx["farm_a"]
    async with await _client() as client:
        created = await client.post(
            base(farm_id), json=_create_body(geo=POLYGON), headers=_headers(users["alpha"])
        )
        plot_id = created.json()["id"]
        stranger = await client.patch(
            f"{base(farm_id)}/{plot_id}", json={"name": "H"}, headers=_headers(users["bravo"])
        )
        officer = await client.patch(
            f"{base(farm_id)}/{plot_id}", json={"name": "H"}, headers=_headers(users["officer"])
        )
        outside = await client.patch(
            f"{base(farm_id)}/{plot_id}", json={"geo": OUTSIDE}, headers=_headers(users["alpha"])
        )
        owner = await client.patch(
            f"{base(farm_id)}/{plot_id}", json={"name": "Renamed"}, headers=_headers(users["alpha"])
        )
        state = await client.get(f"{base(farm_id)}/{plot_id}", headers=_headers(users["alpha"]))
    assert stranger.status_code == 404
    assert officer.status_code == 403
    assert outside.status_code == 422
    assert owner.status_code == 200 and owner.json()["name"] == "Renamed"
    assert state.json()["geo"] == POLYGON  # rejected patch left geo untouched


async def test_delete_matrix(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_id = _ctx["farm_a"]
    async with await _client() as client:
        created = await client.post(
            base(farm_id), json=_create_body(), headers=_headers(users["alpha"])
        )
        plot_id = created.json()["id"]
        owner = await client.delete(f"{base(farm_id)}/{plot_id}", headers=_headers(users["alpha"]))
        officer = await client.delete(
            f"{base(farm_id)}/{plot_id}", headers=_headers(users["officer"])
        )
        admin = await client.delete(f"{base(farm_id)}/{plot_id}", headers=_headers(users["admin"]))
        after = await client.get(f"{base(farm_id)}/{plot_id}", headers=_headers(users["alpha"]))
    assert owner.status_code == 403
    assert officer.status_code == 403
    assert admin.status_code == 204
    assert after.status_code == 404
