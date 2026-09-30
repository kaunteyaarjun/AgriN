"""Cross-resource authorization audit — IDOR pass (M017).

One suite covering the whole `/api/v1` surface built in M012/M014/M016:

1. **Route inventory / default-deny** — every operation of the real app
   (from its OpenAPI schema) must 401 for anonymous callers, except the
   explicit public allow-list. Any new route that forgets its auth
   dependency fails here.
2. **Cross-tenant IDOR matrix** — a farmer touching another tenant's
   profile/farm/plot gets 404 whose body is *identical* to the response
   for a random nonexistent id (no existence oracle).
3. **Mass assignment** — `user_id`, `role`, `password_hash`, `farmer_id`
   and `farm_id` are immutable through PATCH; client-supplied extras are
   ignored and the DB row is unchanged.
4. **List scoping / no-profile farmers / malformed UUIDs / sanitized
   error bodies.**

Fixtures seed alpha/bravo (farmers with profiles), an extension officer,
an admin and ``loner`` (farmer account without a profile); farm A + plot
(alpha), farm B + plot (bravo). Cleanup is scoped to seeded user emails
(cascade removes profiles, farms and plots).
"""

from __future__ import annotations

import re
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from sqlalchemy import delete, select
from src.core.db import get_sessionmaker
from src.main import create_app
from src.models import Farm, Farmer, Plot, User, UserRole

from tests.conftest import _client, _headers, _seed_password_hash

SEED_ROLES = (
    ("alpha", UserRole.farmer),
    ("bravo", UserRole.farmer),
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
    ("loner", UserRole.farmer),
)

# The *complete* set of operations anonymous callers may reach (M010
# allow-list; docs endpoints are a documented public decision, M006).
PUBLIC_OPERATIONS = {
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/ready"),
    ("GET", "/api/v1/ping"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/logout"),  # possession-based (M055), like refresh
    ("GET", "/docs"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
    ("GET", "/docs/oauth2-redirect"),
}
API_ONLY_PUBLIC = PUBLIC_OPERATIONS - {
    ("GET", "/docs"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
    ("GET", "/docs/oauth2-redirect"),
}

MUTATING_METHODS = {"POST", "PATCH", "PUT"}


def farms_url(farm_id: uuid.UUID | str | None = None) -> str:
    base = "/api/v1/farms"
    return base if farm_id is None else f"{base}/{farm_id}"


def plots_url(farm_id: uuid.UUID | str) -> str:
    return f"{farms_url(farm_id)}/plots"


def farmers_url(farmer_id: uuid.UUID | str | None = None) -> str:
    base = "/api/v1/farmers"
    return base if farmer_id is None else f"{base}/{farmer_id}"


@pytest.fixture
async def _ctx(_db: None) -> AsyncGenerator[dict[str, Any], None]:
    """Users, profiles, farms and plots for the cross-tenant matrix."""
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    password_hash = _seed_password_hash()
    for name, role in SEED_ROLES:
        user = User(
            email=f"idor-{name}-{uuid.uuid4().hex[:8]}@example.com",
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
    farm_b = Farm(farmer_id=profiles["bravo"], name="Farm B")
    session.add_all([farm_a, farm_b])
    await session.commit()
    plot_a = Plot(farm_id=farm_a.id, name="Plot A1")
    plot_b = Plot(farm_id=farm_b.id, name="Plot B1")
    session.add_all([plot_a, plot_b])
    await session.commit()
    try:
        yield {
            "users": users,
            "profiles": profiles,
            "farm_a": farm_a.id,
            "farm_b": farm_b.id,
            "plot_a": plot_a.id,
            "plot_b": plot_b.id,
        }
    finally:
        await session.rollback()
        await session.execute(delete(User).where(User.email.in_([u.email for u in users.values()])))
        await session.commit()
        await session.close()


def _inventory() -> list[tuple[str, str]]:
    """(method, path) for every documented operation of the real app."""
    spec = create_app().openapi()
    ops: list[tuple[str, str]] = []
    for path, operations in spec["paths"].items():
        for method in operations:
            if method.upper() in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
                ops.append((method.upper(), path))
    return sorted(ops)


def _bind(path: str) -> str:
    """Replace every {param} with a valid dummy UUID (so a 401, not a 422,
    is what the inventory test measures). Any new path parameter is
    covered automatically — only UUID-shaped params exist today."""
    return re.sub(r"\{(\w+)\}", lambda _match: str(uuid.uuid4()), path)


# ---------------------------------------------------------------------------
# 1. Route inventory / default-deny
# ---------------------------------------------------------------------------


async def test_every_non_public_operation_requires_auth(_ctx: dict[str, Any]) -> None:
    """Default-deny regression guard: a new route without an auth
    dependency fails this test."""
    checked = 0
    async with await _client() as client:
        for method, path in _inventory():
            if (method, path) in API_ONLY_PUBLIC:
                continue
            response = await client.request(
                method, _bind(path), json={} if method in MUTATING_METHODS else None
            )
            assert response.status_code == 401, (
                f"{method} {path} anonymous -> {response.status_code} "
                f"(expected 401): {response.text[:200]}"
            )
            assert response.json()["error_code"] == "not_authenticated"
            checked += 1
    assert checked >= 15, f"inventory suspiciously small ({checked} operations)"


async def test_public_allowlist_is_reachable_anonymously(_ctx: dict[str, Any]) -> None:
    """The allow-listed operations must NOT demand auth — proves the
    allow-list in the previous test is exact, not over-broad."""
    async with await _client() as client:
        for method, path in sorted(API_ONLY_PUBLIC):
            response = await client.request(
                method, path, json={} if method in MUTATING_METHODS else None
            )
            assert response.status_code != 401, f"public {method} {path} unexpectedly demands auth"
    for path in ("/docs", "/redoc", "/openapi.json"):
        async with await _client() as client:
            response = await client.get(path)
        assert response.status_code == 200, f"{path} should stay public (documented decision)"


# ---------------------------------------------------------------------------
# 2. Cross-tenant IDOR matrix (404 + oracle equivalence)
# ---------------------------------------------------------------------------


async def test_cross_tenant_profile_is_404_and_oracle_free(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    bravo_profile = _ctx["profiles"]["bravo"]
    missing = farmers_url(uuid.uuid4())
    async with await _client() as client:
        alpha = _headers(users["alpha"])
        for method, path, body in (
            ("GET", farmers_url(bravo_profile), None),
            ("GET", missing, None),
            ("PATCH", farmers_url(bravo_profile), {"full_name": "Hijack"}),
            ("PATCH", missing, {"full_name": "Hijack"}),
            ("DELETE", farmers_url(bravo_profile), None),
            ("DELETE", missing, None),
        ):
            owned = await client.request(method, path, json=body, headers=alpha)
            absent = await client.request(method, missing, json=body, headers=alpha)
            assert owned.status_code == 404, f"{method} {path} -> {owned.status_code}"
            assert absent.status_code == 404
            assert owned.json() == absent.json(), "404 body differs: existence oracle"
    # bravo's row must be untouched by the rejected PATCH/DELETE attempts
    session = get_sessionmaker()()
    try:
        profile = await session.get(Farmer, bravo_profile)
        assert profile is not None and profile.full_name == "Profile Bravo"
    finally:
        await session.close()


async def test_cross_tenant_farm_is_404_and_oracle_free(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_b = _ctx["farm_b"]
    missing_farm = farms_url(uuid.uuid4())
    async with await _client() as client:
        alpha = _headers(users["alpha"])
        cases: list[tuple[str, str, dict[str, Any] | None, str]] = [
            # method, foreign path, body, path of an id that never existed
            ("GET", farms_url(farm_b), None, missing_farm),
            ("PATCH", farms_url(farm_b), {"name": "Hijack"}, missing_farm),
            ("DELETE", farms_url(farm_b), None, missing_farm),
            # plot verbs under a foreign farm URL inherit the parent check
            ("POST", plots_url(farm_b), {"name": "X"}, plots_url(uuid.uuid4())),
            ("GET", plots_url(farm_b), None, plots_url(uuid.uuid4())),
        ]
        for method, path, body, absent_path in cases:
            foreign = await client.request(method, path, json=body, headers=alpha)
            absent = await client.request(method, absent_path, json=body, headers=alpha)
            assert foreign.status_code == 404, f"{method} {path} -> {foreign.status_code}"
            assert absent.status_code == 404, f"{method} {absent_path} -> {absent.status_code}"
            assert foreign.json() == absent.json(), "404 body differs: existence oracle"
    session = get_sessionmaker()()
    try:
        farm = await session.get(Farm, farm_b)
        assert farm is not None and farm.name == "Farm B"
    finally:
        await session.close()


async def test_cross_tenant_plot_is_404_and_oracle_free(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_a = _ctx["farm_a"]
    farm_b = _ctx["farm_b"]
    plot_a = _ctx["plot_a"]
    random_plot = uuid.uuid4()
    async with await _client() as client:
        bravo = _headers(users["bravo"])
        # (a) bravo reaching alpha's plot through alpha's farm URL: the
        # parent-farm check fires first and must look like a missing farm.
        for method, path, body in (
            ("GET", f"{plots_url(farm_a)}/{plot_a}", None),
            ("PATCH", f"{plots_url(farm_a)}/{plot_a}", {"name": "H"}),
            ("DELETE", f"{plots_url(farm_a)}/{plot_a}", None),
        ):
            response = await client.request(method, path, json=body, headers=bravo)
            absent = await client.request(
                method, f"{plots_url(uuid.uuid4())}/{random_plot}", json=body, headers=bravo
            )
            assert response.status_code == absent.status_code == 404, (
                f"{method} {path} -> {response.status_code}"
            )
            assert response.json() == absent.json(), "404 body differs: existence oracle"
        # (b) alpha's plot id smuggled through bravo's OWN farm URL: scoped
        # lookup must behave exactly like a plot id that never existed.
        stolen = await client.get(f"{plots_url(farm_b)}/{plot_a}", headers=bravo)
        absent = await client.get(f"{plots_url(farm_b)}/{random_plot}", headers=bravo)
        assert stolen.status_code == absent.status_code == 404
        assert stolen.json() == absent.json()
        # the plot itself must still be intact
        owner = await client.get(f"{plots_url(farm_a)}/{plot_a}", headers=_headers(users["alpha"]))
        assert owner.status_code == 200
        assert owner.json()["name"] == "Plot A1"
    session = get_sessionmaker()()
    try:
        plot = await session.get(Plot, plot_a)
        assert plot is not None and plot.farm_id == farm_a
        assert plot.name == "Plot A1"
    finally:
        await session.close()


async def test_non_owner_farmer_write_verbs_are_404_not_403(_ctx: dict[str, Any]) -> None:
    """403 on a cross-tenant write would confirm the resource exists."""
    users: dict[str, User] = _ctx["users"]
    farm_a = _ctx["farm_a"]
    plot_a = _ctx["plot_a"]
    async with await _client() as client:
        stranger = _headers(users["bravo"])
        responses = [
            await client.patch(farms_url(farm_a), json={"name": "H"}, headers=stranger),
            await client.patch(
                f"{plots_url(farm_a)}/{plot_a}", json={"name": "H"}, headers=stranger
            ),
            await client.delete(farms_url(farm_a), headers=stranger),
        ]
    assert [r.status_code for r in responses] == [404, 404, 404]

    # The farm-create mismatch guard (a farmer naming someone else's
    # profile) must not become an existence oracle either: a profile id
    # that never existed yields the exact same 403.
    async with await _client() as client:
        stranger = _headers(users["bravo"])
        real = await client.post(
            farms_url(),
            json={"name": "X", "farmer_id": str(_ctx["profiles"]["alpha"])},
            headers=stranger,
        )
        fake = await client.post(
            farms_url(),
            json={"name": "X", "farmer_id": str(uuid.uuid4())},
            headers=stranger,
        )
    assert real.status_code == fake.status_code == 403
    assert real.json() == fake.json()


# ---------------------------------------------------------------------------
# 3. Mass assignment / immutable fields
# ---------------------------------------------------------------------------


async def test_mass_assignment_cannot_reassign_ownership_or_role(
    _ctx: dict[str, Any],
) -> None:
    users: dict[str, User] = _ctx["users"]
    profiles: dict[str, uuid.UUID] = _ctx["profiles"]
    farm_a = _ctx["farm_a"]
    plot_a = _ctx["plot_a"]
    session = get_sessionmaker()()
    try:
        async with await _client() as client:
            # (a) profile: user_id / role / password_hash extras ignored
            moved = await client.patch(
                farmers_url(profiles["alpha"]),
                json={
                    "full_name": "Renamed",
                    "user_id": str(users["bravo"].id),
                    "role": "admin",
                    "password_hash": "pwned",
                    "email": "attacker@example.com",
                },
                headers=_headers(users["alpha"]),
            )
            assert moved.status_code == 200, moved.text
            assert moved.json()["user_id"] == str(users["alpha"].id)
            assert "role" not in moved.json()
            assert "password_hash" not in moved.json()

            # (b) farm: farmer_id immutable even for admin
            rehomed = await client.patch(
                farms_url(farm_a),
                json={"name": "Farm A2", "farmer_id": str(profiles["bravo"])},
                headers=_headers(users["admin"]),
            )
            assert rehomed.status_code == 200, rehomed.text
            assert rehomed.json()["farmer_id"] == str(profiles["alpha"])

            # (c) plot: farm_id immutable (URL owns the parent)
            moved_plot = await client.patch(
                f"{plots_url(farm_a)}/{plot_a}",
                json={"name": "Plot A1b", "farm_id": str(_ctx["farm_b"])},
                headers=_headers(users["alpha"]),
            )
            assert moved_plot.status_code == 200, moved_plot.text
            assert moved_plot.json()["farm_id"] == str(farm_a)

        # DB-level confirmation (response models could lie)
        farmer = await session.get(Farmer, profiles["alpha"])
        assert farmer is not None and farmer.user_id == users["alpha"].id
        user = await session.get(User, users["alpha"].id)
        assert user is not None
        assert user.role is UserRole.farmer
        assert user.email == users["alpha"].email
        assert user.password_hash == _seed_password_hash()
        farm = await session.get(Farm, farm_a)
        assert farm is not None and farm.farmer_id == profiles["alpha"]
        plot = await session.get(Plot, plot_a)
        assert plot is not None and plot.farm_id == farm_a
    finally:
        await session.close()


async def test_list_scoping_ignores_foreign_farmer_filter(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    profiles: dict[str, uuid.UUID] = _ctx["profiles"]
    async with await _client() as client:
        # a farmer may not use ?farmer_id to browse someone else's farms
        smuggled = await client.get(
            f"{farms_url()}?farmer_id={profiles['bravo']}", headers=_headers(users["alpha"])
        )
        own = await client.get(farms_url(), headers=_headers(users["alpha"]))
        assert smuggled.status_code == own.status_code == 200
        assert {i["farmer_id"] for i in smuggled.json()["items"]} == {str(profiles["alpha"])}
        assert smuggled.json()["total"] == 1

        # officers/admins keep their legitimate filter (contract from M014)
        filtered = await client.get(
            f"{farms_url()}?farmer_id={profiles['bravo']}",
            headers=_headers(users["officer"]),
        )
        assert filtered.status_code == 200
        assert {i["farmer_id"] for i in filtered.json()["items"]} == {str(profiles["bravo"])}

        # the profile list itself is staff-only
        denied = await client.get(farmers_url(), headers=_headers(users["alpha"]))
        assert denied.status_code == 403
        allowed = await client.get(farmers_url(), headers=_headers(users["officer"]))
        assert allowed.status_code == 200


async def test_farmer_without_profile_scoping(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    async with await _client() as client:
        loner = _headers(users["loner"])
        empty = await client.get(farms_url(), headers=loner)
        assert empty.status_code == 200
        assert empty.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}
        blocked = await client.post(farms_url(), json={"name": "Nope"}, headers=loner)
        assert blocked.status_code == 409
        assert blocked.json()["error_code"] == "conflict"
        # self-provisioning still works (and is scoped to the caller)
        created = await client.post(
            farmers_url(), json={"full_name": "Loner Profile"}, headers=loner
        )
        assert created.status_code == 201, created.text
        assert created.json()["user_id"] == str(users["loner"].id)


# ---------------------------------------------------------------------------
# 4. Input handling, officer ordering, sanitized errors
# ---------------------------------------------------------------------------


async def test_malformed_uuid_is_422_never_500(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    farm_a = _ctx["farm_a"]
    async with await _client() as client:
        responses = [
            await client.get(farms_url("not-a-uuid"), headers=_headers(users["alpha"])),
            await client.get(f"{farms_url()}?farmer_id=nope", headers=_headers(users["admin"])),
            await client.get(f"{plots_url(farm_a)}/nope", headers=_headers(users["alpha"])),
            await client.get(farmers_url("nope"), headers=_headers(users["admin"])),
        ]
        anonymous_path = await client.get(farms_url("not-a-uuid"))
    assert [r.status_code for r in responses] == [422, 422, 422, 422]
    assert all(r.status_code != 500 for r in responses)
    # auth runs before path validation: an anonymous malformed id is 401
    assert anonymous_path.status_code == 401


async def test_officer_write_ordering_documents_no_new_oracle(
    _ctx: dict[str, Any],
) -> None:
    """Officers may read everything, so 404-missing vs 403-existing carries
    no information they do not already have; assert the stable contract."""
    users: dict[str, User] = _ctx["users"]
    farm_a = _ctx["farm_a"]
    async with await _client() as client:
        officer = _headers(users["officer"])
        missing = await client.patch(farms_url(uuid.uuid4()), json={"name": "X"}, headers=officer)
        existing = await client.patch(farms_url(farm_a), json={"name": "X"}, headers=officer)
        readable = await client.get(farms_url(farm_a), headers=officer)
    assert missing.status_code == 404
    assert existing.status_code == 403
    assert readable.status_code == 200


async def test_error_bodies_carry_no_internals(_ctx: dict[str, Any]) -> None:
    users: dict[str, User] = _ctx["users"]
    async with await _client() as client:
        responses = [
            await client.get(farms_url(uuid.uuid4()), headers=_headers(users["alpha"])),
            await client.patch(
                farms_url(uuid.uuid4()), json={"name": "X"}, headers=_headers(users["officer"])
            ),
            await client.get(farmers_url(), headers=_headers(users["alpha"])),  # 403 staff list
            await client.post(farms_url(), json={}, headers=None),
        ]
    for response in responses:
        assert response.status_code >= 400
        payload = response.json()
        assert set(payload) <= {"error_code", "message"}, payload
        blob = response.text.lower()
        for forbidden in ("traceback", "select ", "insert ", "password", "secret", ".py"):
            assert forbidden not in blob, f"leaked {forbidden!r}: {response.text}"


async def test_role_escalation_via_token_or_body_is_impossible(
    _ctx: dict[str, Any],
) -> None:
    """A farmer cannot reach staff endpoints by asking nicely."""
    users: dict[str, User] = _ctx["users"]
    async with await _client() as client:
        farmer = _headers(users["alpha"])
        attempts = [
            await client.get(farmers_url(), headers=farmer),
            await client.patch(
                farmers_url(_ctx["profiles"]["alpha"]),
                json={"role": "admin"},
                headers=farmer,
            ),
        ]
    assert attempts[0].status_code == 403
    assert attempts[1].status_code == 200  # extra ignored, see mass-assignment test
    session = get_sessionmaker()()
    try:
        user = await session.get(User, users["alpha"].id)
        assert user is not None and user.role is UserRole.farmer
    finally:
        await session.close()
