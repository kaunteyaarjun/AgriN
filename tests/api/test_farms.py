"""API tests for farm CRUD + ownership (M014): full authorization matrix,
GeoJSON validation and API-level geo round trip against dev Postgres.

Same fixture style as test_farmers.py: seeded users/profiles with scoped
cleanup, tokens minted via `create_access_token` (login covered elsewhere).
"""

from __future__ import annotations

import asyncio
import functools
import json
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import delete, func, select, text
from src.api.v1.farms import FarmCreate, FarmPatch
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import create_access_token, hash_password
from src.main import create_app
from src.models import Farm, Farmer, User, UserRole

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = "/api/v1/farms"
PASSWORD = "Sup3rSecret-Pass!"
SEED_ROLES = (
    ("alpha", UserRole.farmer),
    ("bravo", UserRole.farmer),
    ("nop", UserRole.farmer),  # farmer-role user without a profile
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
)

POLYGON: dict[str, object] = {
    "type": "Polygon",
    "coordinates": [
        [
            [36.75, -1.29],
            [36.76, -1.29],
            [36.76, -1.28],
            [36.75, -1.29],
        ]
    ],
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
    """alpha/bravo farmers WITH profiles, nop without, officer + admin."""
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    profiles: dict[str, Farmer] = {}
    password_hash = _seed_password_hash()
    for name, role in SEED_ROLES:
        user = User(
            email=f"farm-{name}-{uuid.uuid4().hex[:8]}@example.com",
            password_hash=password_hash,
            role=role,
        )
        session.add(user)
        users[name] = user
    await session.commit()
    for name in ("alpha", "bravo"):
        profile = Farmer(user_id=users[name].id, full_name=f"Profile {name.title()}")
        session.add(profile)
        profiles[name] = profile
    await session.commit()
    try:
        yield users
    finally:
        await session.rollback()
        # Scoped delete; FK cascade removes farmer profiles and their farms.
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


async def _make_farm(
    users: dict[str, User], name: str, *, geo: dict[str, object] | None = None
) -> uuid.UUID:
    """Seed one farm directly (setup helper, not the subject under test)."""
    farmer_id = await _profile_id(users, "alpha")
    session = get_sessionmaker()()
    try:
        farm = Farm(farmer_id=farmer_id, name=name, area_hectares=2)
        if geo is not None:
            farm.geo = func.ST_GeomFromGeoJSON(json.dumps(geo))
        session.add(farm)
        await session.commit()
        return farm.id
    finally:
        await session.close()


def _create_body(farmer_id: uuid.UUID | None = None, **extra: object) -> dict[str, object]:
    body: dict[str, object] = {"name": "Meadow North"}
    if farmer_id is not None:
        body["farmer_id"] = str(farmer_id)
    body.update(extra)
    return body


def test_geojson_validator_accepts_polygon_and_multipolygon() -> None:
    FarmCreate.model_validate({"name": "ok", "geo": POLYGON})
    FarmCreate.model_validate(
        {"name": "ok", "geo": {"type": "MultiPolygon", "coordinates": [POLYGON["coordinates"]]}}
    )
    FarmCreate.model_validate({"name": "ok", "geo": None})


def test_geojson_validator_rejects_bad_shapes() -> None:
    for bad in (
        {"type": "Point", "coordinates": [36.75, -1.29]},
        {"type": "Polygon", "coordinates": [[[36.75, -1.29], [36.76, -1.29], [36.76, -1.28]]]},
        {
            "type": "Polygon",
            "coordinates": [[[36.75, -1.29], [200, -1.29], [36.76, -95], [36.75, -1.29]]],
        },
        {"type": "Polygon", "coordinates": []},
        {"type": "Polygon", "coordinates": [["not", "numbers"]]},
        {"type": "Polygon"},
    ):
        with pytest.raises(ValidationError):
            FarmCreate.model_validate({"name": "bad", "geo": bad})


def test_patch_field_validation() -> None:
    with pytest.raises(ValidationError):
        FarmPatch.model_validate({})
    with pytest.raises(ValidationError):
        FarmPatch.model_validate({"area_hectares": -1})
    with pytest.raises(ValidationError):
        FarmPatch.model_validate({"name": ""})
    FarmPatch.model_validate({"geo": None})  # explicit clear is allowed


async def test_anonymous_requests_get_401(_users: dict[str, User]) -> None:
    any_id = str(uuid.uuid4())
    async with await _client() as client:
        responses = [
            await client.get(BASE),
            await client.post(BASE, json=_create_body()),
            await client.get(f"{BASE}/{any_id}"),
            await client.patch(f"{BASE}/{any_id}", json={"name": "X"}),
            await client.delete(f"{BASE}/{any_id}"),
        ]
    assert [r.status_code for r in responses] == [401, 401, 401, 401, 401]
    assert all(r.json()["error_code"] == "not_authenticated" for r in responses)


async def test_farmer_create_own_farm_geo_round_trip(_users: dict[str, User]) -> None:
    async with await _client() as client:
        created = await client.post(
            BASE, json=_create_body(geo=POLYGON), headers=_headers(_users["alpha"])
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["name"] == "Meadow North"
        assert body["geo"] == POLYGON

        fetched = await client.get(f"{BASE}/{body['id']}", headers=_headers(_users["alpha"]))
        assert fetched.status_code == 200
        assert fetched.json()["geo"] == POLYGON
        assert fetched.json()["geo"]["type"] == "Polygon"


async def test_farmer_create_for_other_profile_forbidden(_users: dict[str, User]) -> None:
    bravo_profile = await _profile_id(_users, "bravo")
    async with await _client() as client:
        response = await client.post(
            BASE, json=_create_body(farmer_id=bravo_profile), headers=_headers(_users["alpha"])
        )
    assert response.status_code == 403
    assert response.json()["error_code"] == "permission_denied"


async def test_farmer_without_profile_conflicts(_users: dict[str, User]) -> None:
    async with await _client() as client:
        response = await client.post(BASE, json=_create_body(), headers=_headers(_users["nop"]))
    assert response.status_code == 409
    assert response.json()["error_code"] == "conflict"


async def test_officer_cannot_create(_users: dict[str, User]) -> None:
    async with await _client() as client:
        response = await client.post(BASE, json=_create_body(), headers=_headers(_users["officer"]))
    assert response.status_code == 403


async def test_admin_create_requires_existing_profile(_users: dict[str, User]) -> None:
    alpha_profile = await _profile_id(_users, "alpha")
    async with await _client() as client:
        missing_id = await client.post(BASE, json=_create_body(), headers=_headers(_users["admin"]))
        unknown = await client.post(
            BASE, json=_create_body(farmer_id=uuid.uuid4()), headers=_headers(_users["admin"])
        )
        created = await client.post(
            BASE,
            json=_create_body(farmer_id=alpha_profile, area_hectares="1.5"),
            headers=_headers(_users["admin"]),
        )
    assert missing_id.status_code == 422
    assert unknown.status_code == 404
    assert created.status_code == 201, created.text
    assert created.json()["area_hectares"] == "1.50"  # numeric(10,2) fixed scale


async def test_duplicate_name_same_farmer_conflicts(_users: dict[str, User]) -> None:
    async with await _client() as client:
        first = await client.post(BASE, json=_create_body(), headers=_headers(_users["alpha"]))
        assert first.status_code == 201
        second = await client.post(BASE, json=_create_body(), headers=_headers(_users["alpha"]))
        # Same name under a DIFFERENT farmer is fine.
        bravo_profile = await _profile_id(_users, "bravo")
        other = await client.post(
            BASE,
            json=_create_body(farmer_id=bravo_profile),
            headers=_headers(_users["admin"]),
        )
    assert second.status_code == 409
    assert second.json()["error_code"] == "conflict"
    assert other.status_code == 201


async def test_invalid_geo_rejected_and_nothing_persisted(_users: dict[str, User]) -> None:
    async with await _client() as client:
        headers = _headers(_users["alpha"])
        bad = await client.post(
            BASE,
            json=_create_body(geo={"type": "Polygon", "coordinates": [[[1, 2], [3, 4]]]}),
            headers=headers,
        )
        after = await client.get(BASE, headers=headers)
    assert bad.status_code == 422
    assert after.json()["total"] == 0


async def test_list_scoped_per_farmer_and_privileged_views(
    _users: dict[str, User],
) -> None:
    alpha_profile = await _profile_id(_users, "alpha")
    bravo_profile = await _profile_id(_users, "bravo")
    async with await _client() as client:
        await client.post(BASE, json=_create_body(), headers=_headers(_users["alpha"]))
        await client.post(
            BASE,
            json=_create_body(farmer_id=bravo_profile),
            headers=_headers(_users["admin"]),
        )
        alpha_list = await client.get(BASE, headers=_headers(_users["alpha"]))
        bravo_list = await client.get(BASE, headers=_headers(_users["bravo"]))
        officer_list = await client.get(BASE, headers=_headers(_users["officer"]))
        admin_filtered = await client.get(
            BASE, params={"farmer_id": str(bravo_profile)}, headers=_headers(_users["admin"])
        )
        nop_list = await client.get(BASE, headers=_headers(_users["nop"]))
    assert alpha_list.json()["total"] == 1
    assert alpha_list.json()["items"][0]["farmer_id"] == str(alpha_profile)
    assert bravo_list.json()["total"] == 1
    assert bravo_list.json()["items"][0]["farmer_id"] == str(bravo_profile)
    assert officer_list.json()["total"] == 2
    assert admin_filtered.json()["total"] == 1
    assert admin_filtered.json()["items"][0]["farmer_id"] == str(bravo_profile)
    assert nop_list.json()["total"] == 0


async def test_get_ownership_matrix(_users: dict[str, User]) -> None:
    farm_id = await _make_farm(_users, "Matrix Read Farm", geo=POLYGON)
    async with await _client() as client:
        owner = await client.get(f"{BASE}/{farm_id}", headers=_headers(_users["alpha"]))
        officer = await client.get(f"{BASE}/{farm_id}", headers=_headers(_users["officer"]))
        admin = await client.get(f"{BASE}/{farm_id}", headers=_headers(_users["admin"]))
        stranger = await client.get(f"{BASE}/{farm_id}", headers=_headers(_users["bravo"]))
        missing = await client.get(f"{BASE}/{uuid.uuid4()}", headers=_headers(_users["admin"]))
    assert owner.status_code == 200 and owner.json()["geo"] == POLYGON
    assert officer.status_code == 200
    assert admin.status_code == 200
    assert stranger.status_code == 404  # no existence oracle
    assert missing.status_code == 404


async def test_patch_matrix_and_farmer_id_immutable(_users: dict[str, User]) -> None:
    farm_id = await _make_farm(_users, "Matrix Patch Farm")
    alpha_profile = await _profile_id(_users, "alpha")
    bravo_profile = await _profile_id(_users, "bravo")
    async with await _client() as client:
        stranger = await client.patch(
            f"{BASE}/{farm_id}", json={"name": "Hijacked"}, headers=_headers(_users["bravo"])
        )
        officer = await client.patch(
            f"{BASE}/{farm_id}", json={"name": "Nope"}, headers=_headers(_users["officer"])
        )
        owner = await client.patch(
            f"{BASE}/{farm_id}",
            json={"name": "Renamed", "geo": POLYGON},
            headers=_headers(_users["alpha"]),
        )
        steal = await client.patch(
            f"{BASE}/{farm_id}",
            json={"farmer_id": str(bravo_profile), "area_hectares": 9},
            headers=_headers(_users["admin"]),
        )
        state = await client.get(f"{BASE}/{farm_id}", headers=_headers(_users["admin"]))
    assert stranger.status_code == 404
    assert officer.status_code == 403
    assert owner.status_code == 200
    assert owner.json()["name"] == "Renamed"
    assert owner.json()["geo"] == POLYGON
    assert steal.status_code == 200
    body = state.json()
    assert body["farmer_id"] == str(alpha_profile)  # farmer_id never changes
    assert body["area_hectares"] == "9.00"  # numeric(10,2) fixed scale
    assert str(bravo_profile) not in (body["farmer_id"],)


async def test_delete_matrix(_users: dict[str, User]) -> None:
    owner_farm = await _make_farm(_users, "Owner Keep Farm")
    officer_farm = await _make_farm(_users, "Officer Target Farm")
    admin_farm = await _make_farm(_users, "Admin Target Farm")
    async with await _client() as client:
        owner = await client.delete(f"{BASE}/{owner_farm}", headers=_headers(_users["alpha"]))
        officer = await client.delete(f"{BASE}/{officer_farm}", headers=_headers(_users["officer"]))
        stranger = await client.delete(f"{BASE}/{admin_farm}", headers=_headers(_users["bravo"]))
        admin = await client.delete(f"{BASE}/{admin_farm}", headers=_headers(_users["admin"]))
        after = await client.get(f"{BASE}/{admin_farm}", headers=_headers(_users["admin"]))
    assert owner.status_code == 403
    assert officer.status_code == 403
    assert stranger.status_code == 404
    assert admin.status_code == 204
    assert after.status_code == 404
