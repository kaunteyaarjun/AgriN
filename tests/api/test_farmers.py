"""API tests for farmer CRUD (M012): full authorization matrix.

Needs the dev Postgres (skip-if-unreachable `_db` fixture requested by the
seeded `_users` fixture so its dispose teardown always runs — M008 lesson).
Access tokens are minted directly via `create_access_token` (login itself is
covered in test_auth.py) so the matrix runs without bcrypt cost.
"""

from __future__ import annotations

import asyncio
import functools
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import delete, text
from src.api.v1.farmers import FarmerCreate, FarmerPatch
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import create_access_token, hash_password
from src.main import create_app
from src.models import User, UserRole

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = "/api/v1/farmers"
PASSWORD = "Sup3rSecret-Pass!"
SEED_ROLES = (
    ("alpha", UserRole.farmer),
    ("bravo", UserRole.farmer),
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
)


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
    """One bcrypt hash per test process; reused for every seeded user."""
    return hash_password(PASSWORD)


@pytest.fixture
async def _users(_db: None) -> AsyncGenerator[dict[str, User], None]:
    """Seeded alpha/bravo farmers + officer + admin; always cleaned up."""
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    password_hash = _seed_password_hash()
    for name, role in SEED_ROLES:
        user = User(
            email=f"farmer-{name}-{uuid.uuid4().hex[:8]}@example.com",
            password_hash=password_hash,
            role=role,
        )
        session.add(user)
        users[name] = user
    await session.commit()
    try:
        yield users
    finally:
        await session.rollback()
        # Scoped delete only; FK cascade removes these users' farmer rows.
        # Never unscoped DELETE — M011's test teardown wiped dev accounts.
        await session.execute(delete(User).where(User.email.in_([u.email for u in users.values()])))
        await session.commit()
        await session.close()


async def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app())
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def _farmer_body(user_id: uuid.UUID | None = None, **extra: str) -> dict[str, object]:
    body: dict[str, object] = {"full_name": "Asha Mwangi"}
    if user_id is not None:
        body["user_id"] = str(user_id)
    body.update(extra)
    return body


def test_empty_patch_rejected() -> None:
    with pytest.raises(ValidationError):
        FarmerPatch.model_validate({})


def test_create_rejects_bad_fields() -> None:
    with pytest.raises(ValidationError):
        FarmerCreate.model_validate({"full_name": ""})
    with pytest.raises(ValidationError):
        FarmerCreate.model_validate({"full_name": "Asha", "phone": "not-a-phone!!"})
    with pytest.raises(ValidationError):
        FarmerCreate.model_validate({"full_name": "Asha", "village": "x" * 121})


async def test_anonymous_requests_get_401(_users: dict[str, User]) -> None:
    any_id = str(uuid.uuid4())
    async with await _client() as client:
        responses = [
            await client.get(BASE),
            await client.post(BASE, json=_farmer_body()),
            await client.get(f"{BASE}/{any_id}"),
            await client.patch(f"{BASE}/{any_id}", json={"full_name": "X"}),
            await client.delete(f"{BASE}/{any_id}"),
        ]
    assert [r.status_code for r in responses] == [401, 401, 401, 401, 401]
    assert all(r.json()["error_code"] == "not_authenticated" for r in responses)


async def test_farmer_self_create_then_read_own(_users: dict[str, User]) -> None:
    farmer = _users["alpha"]
    async with await _client() as client:
        created = await client.post(BASE, json=_farmer_body(), headers=_headers(farmer))
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["user_id"] == str(farmer.id)
        assert body["phone"] is None and body["village"] is None

        fetched = await client.get(f"{BASE}/{body['id']}", headers=_headers(farmer))
        assert fetched.status_code == 200
        assert fetched.json()["full_name"] == "Asha Mwangi"


async def test_farmer_create_for_someone_else_forbidden(_users: dict[str, User]) -> None:
    async with await _client() as client:
        response = await client.post(
            BASE,
            json=_farmer_body(user_id=_users["bravo"].id),
            headers=_headers(_users["alpha"]),
        )
    assert response.status_code == 403
    assert response.json()["error_code"] == "permission_denied"


async def test_duplicate_profile_conflicts(_users: dict[str, User]) -> None:
    async with await _client() as client:
        first = await client.post(BASE, json=_farmer_body(), headers=_headers(_users["alpha"]))
        assert first.status_code == 201
        second = await client.post(BASE, json=_farmer_body(), headers=_headers(_users["alpha"]))
    assert second.status_code == 409
    assert second.json()["error_code"] == "conflict"


async def test_admin_create_for_farmer_account(_users: dict[str, User]) -> None:
    async with await _client() as client:
        response = await client.post(
            BASE,
            json=_farmer_body(user_id=_users["alpha"].id, phone="+255712345678"),
            headers=_headers(_users["admin"]),
        )
    assert response.status_code == 201, response.text
    assert response.json()["phone"] == "+255712345678"


async def test_admin_create_missing_user_404(_users: dict[str, User]) -> None:
    async with await _client() as client:
        response = await client.post(
            BASE, json=_farmer_body(user_id=uuid.uuid4()), headers=_headers(_users["admin"])
        )
    assert response.status_code == 404
    assert response.json()["error_code"] == "not_found"


async def test_admin_create_for_non_farmer_account_conflicts(_users: dict[str, User]) -> None:
    async with await _client() as client:
        response = await client.post(
            BASE, json=_farmer_body(user_id=_users["admin"].id), headers=_headers(_users["admin"])
        )
    assert response.status_code == 409


async def test_officer_cannot_create(_users: dict[str, User]) -> None:
    async with await _client() as client:
        response = await client.post(
            BASE, json=_farmer_body(user_id=_users["alpha"].id), headers=_headers(_users["officer"])
        )
    assert response.status_code == 403


async def test_list_forbidden_for_farmer_allowed_for_officer_and_admin(
    _users: dict[str, User],
) -> None:
    async with await _client() as client:
        admin_created = await client.post(
            BASE, json=_farmer_body(user_id=_users["alpha"].id), headers=_headers(_users["admin"])
        )
        assert admin_created.status_code == 201
        farmer_list = await client.get(BASE, headers=_headers(_users["alpha"]))
        officer_list = await client.get(BASE, headers=_headers(_users["officer"]))
        admin_list = await client.get(BASE, headers=_headers(_users["admin"]))
    assert farmer_list.status_code == 403
    for ok in (officer_list, admin_list):
        assert ok.status_code == 200
        envelope = ok.json()
        assert envelope["total"] == 1 and len(envelope["items"]) == 1
        assert envelope["limit"] == 50 and envelope["offset"] == 0


async def test_list_pagination_bounds_enforced(_users: dict[str, User]) -> None:
    async with await _client() as client:
        too_big = await client.get(f"{BASE}?limit=101", headers=_headers(_users["admin"]))
        negative = await client.get(f"{BASE}?limit=0", headers=_headers(_users["admin"]))
    assert too_big.status_code == 422
    assert negative.status_code == 422


async def test_get_visibility_matrix(_users: dict[str, User]) -> None:
    async with await _client() as client:
        created = await client.post(
            BASE, json=_farmer_body(user_id=_users["alpha"].id), headers=_headers(_users["admin"])
        )
        farmer_id = created.json()["id"]
        own = await client.get(f"{BASE}/{farmer_id}", headers=_headers(_users["alpha"]))
        other = await client.get(f"{BASE}/{farmer_id}", headers=_headers(_users["bravo"]))
        officer = await client.get(f"{BASE}/{farmer_id}", headers=_headers(_users["officer"]))
        admin = await client.get(f"{BASE}/{farmer_id}", headers=_headers(_users["admin"]))
        missing = await client.get(f"{BASE}/{uuid.uuid4()}", headers=_headers(_users["admin"]))
    assert own.status_code == 200
    assert other.status_code == 404  # non-owner farmer: no existence oracle
    assert officer.status_code == 200
    assert admin.status_code == 200
    assert missing.status_code == 404


async def test_patch_owner_officer_other_matrix(_users: dict[str, User]) -> None:
    async with await _client() as client:
        created = await client.post(
            BASE, json=_farmer_body(user_id=_users["alpha"].id), headers=_headers(_users["admin"])
        )
        farmer_id = created.json()["id"]

        owner_patch = await client.patch(
            f"{BASE}/{farmer_id}",
            json={"full_name": "Asha Juma"},
            headers=_headers(_users["alpha"]),
        )
        officer_patch = await client.patch(
            f"{BASE}/{farmer_id}", json={"full_name": "Nope"}, headers=_headers(_users["officer"])
        )
        other_patch = await client.patch(
            f"{BASE}/{farmer_id}", json={"full_name": "Nope"}, headers=_headers(_users["bravo"])
        )
        empty_patch = await client.patch(
            f"{BASE}/{farmer_id}", json={}, headers=_headers(_users["admin"])
        )
        admin_patch = await client.patch(
            f"{BASE}/{farmer_id}", json={"village": "Mwanga"}, headers=_headers(_users["admin"])
        )
        final = await client.get(f"{BASE}/{farmer_id}", headers=_headers(_users["admin"]))
    assert owner_patch.status_code == 200
    assert owner_patch.json()["full_name"] == "Asha Juma"
    assert officer_patch.status_code == 403
    assert other_patch.status_code == 404
    assert empty_patch.status_code == 422
    assert admin_patch.status_code == 200
    assert final.json()["village"] == "Mwanga"
    assert final.json()["full_name"] == "Asha Juma"  # partial: untouched field kept


async def test_delete_admin_only_matrix(_users: dict[str, User]) -> None:
    async with await _client() as client:
        created = await client.post(
            BASE, json=_farmer_body(user_id=_users["alpha"].id), headers=_headers(_users["admin"])
        )
        farmer_id = created.json()["id"]

        owner_delete = await client.delete(f"{BASE}/{farmer_id}", headers=_headers(_users["alpha"]))
        officer_delete = await client.delete(
            f"{BASE}/{farmer_id}", headers=_headers(_users["officer"])
        )
        other_delete = await client.delete(f"{BASE}/{farmer_id}", headers=_headers(_users["bravo"]))
        admin_delete = await client.delete(f"{BASE}/{farmer_id}", headers=_headers(_users["admin"]))
        after = await client.get(f"{BASE}/{farmer_id}", headers=_headers(_users["admin"]))
    assert owner_delete.status_code == 403
    assert officer_delete.status_code == 403
    assert other_delete.status_code == 404
    assert admin_delete.status_code == 204
    assert after.status_code == 404
