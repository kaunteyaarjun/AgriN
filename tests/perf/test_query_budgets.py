"""Query-count regression budgets (M056): N+1 guards for the hot read paths.

M019 already pins ``get_farm_state`` to exactly 3 queries
(``tests/services/test_farm_state.py``); this module extends the guard
to ``analyze_farm`` (M043's service) and the farm read endpoints that
everything renders from (list, detail, state). Budgets are measured on
the dev Postgres and recorded in MILESTONES.md's M056 notes — an N+1
regression fails here instead of shipping.

DB-backed (SKIP when unreachable). Cleanup is scoped to the seeded user
(FK cascade clears farmer → farms → plots → plot_states and
farm_signal_caches), the same pattern as the API test modules.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator, Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, event, select, text
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import create_access_token
from src.main import create_app
from src.models import Farm, Farmer, Plot, User
from src.services.analysis import analyze_farm
from src.services.farm_state import put_signals, set_plot_state

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = "/api/v1/farms"

# Measured budgets (M056 notes carry the run numbers). Headroom of ±0:
# these paths are deterministic, and a new query is exactly the
# regression this file exists to catch.
ANALYZE_FARM_BUDGET = 3  # reuses get_farm_state's contract (M019)
FARMS_LIST_BUDGET = 4
FARM_DETAIL_BUDGET = 2
FARM_STATE_ENDPOINT_BUDGET = 5


class _StatementRecorder:
    """``before_cursor_execute`` listener recording every statement."""

    def __init__(self) -> None:
        self.statements: list[str] = []

    def __call__(
        self,
        conn: object,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        executemany: bool,
    ) -> None:
        self.statements.append(statement)


@contextmanager
def _record() -> Iterator[_StatementRecorder]:
    recorder = _StatementRecorder()
    engine = get_engine().sync_engine
    event.listen(engine, "before_cursor_execute", recorder)
    try:
        yield recorder
    finally:
        event.remove(engine, "before_cursor_execute", recorder)


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


async def _seed_read_world(session) -> tuple[uuid.UUID, uuid.UUID]:
    """farmer user + profile + farm + 2 plots (one state) + signals.

    Returns (user_id, farm_id); the caller cleans up by user id.
    """
    user = User(email=f"perf-{uuid.uuid4().hex[:12]}@example.com", password_hash="stored-hash")
    session.add(user)
    await session.commit()
    farmer = Farmer(user_id=user.id, full_name="Perf Owner")
    session.add(farmer)
    await session.commit()
    farm = Farm(farmer_id=farmer.id, name="Perf Farm")
    session.add(farm)
    await session.commit()
    session.add(Plot(farm_id=farm.id, name="Block A"))
    session.add(Plot(farm_id=farm.id, name="Block B"))
    await session.commit()
    plot_a = await session.scalar(
        select(Plot.id).where(Plot.farm_id == farm.id, Plot.name == "Block A")
    )
    assert plot_a is not None
    await set_plot_state(
        session,
        plot_a,
        crop="Maize",
        growth_stage="vegetative",
        planted_on=date(2026, 9, 18),
    )
    await put_signals(session, farm_id=farm.id, signals={"weather": {"temp_c": 26.0}})
    return user.id, farm.id


async def _cleanup(session, user_id: uuid.UUID) -> None:
    await session.rollback()
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
    await session.close()


async def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app())
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def test_analyze_farm_stays_within_query_budget(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user_id, farm_id = await _seed_read_world(session)
        with _record() as recorder:
            analysis = await analyze_farm(session, farm_id)
        assert analysis is not None
        assert len(recorder.statements) <= ANALYZE_FARM_BUDGET, recorder.statements
    finally:
        await _cleanup(session, user_id)


async def test_farms_list_query_budget(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user_id, farm_id = await _seed_read_world(session)
        headers = _headers(user_id)
        async with await _client() as client:
            with _record() as recorder:
                response = await client.get(BASE, headers=headers)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert len(recorder.statements) <= FARMS_LIST_BUDGET, recorder.statements
    finally:
        await _cleanup(session, user_id)


async def test_farm_detail_query_budget(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user_id, farm_id = await _seed_read_world(session)
        headers = _headers(user_id)
        async with await _client() as client:
            with _record() as recorder:
                response = await client.get(f"{BASE}/{farm_id}", headers=headers)
        assert response.status_code == 200
        assert len(recorder.statements) <= FARM_DETAIL_BUDGET, recorder.statements
    finally:
        await _cleanup(session, user_id)


async def test_farm_state_endpoint_query_budget(_db: None) -> None:
    session = get_sessionmaker()()
    try:
        user_id, farm_id = await _seed_read_world(session)
        headers = _headers(user_id)
        async with await _client() as client:
            with _record() as recorder:
                response = await client.get(f"{BASE}/{farm_id}/state", headers=headers)
        assert response.status_code == 200
        assert len(recorder.statements) <= FARM_STATE_ENDPOINT_BUDGET, recorder.statements
    finally:
        await _cleanup(session, user_id)
