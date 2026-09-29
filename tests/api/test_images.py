"""API tests for image upload (M035): the limits are the feature.

Covers the validation pipeline (size → sniff → pixels → verify), the
ownership matrix on both verbs, sniff-authoritative content types,
FK cascade on plot delete, and that files land only in the configured
``upload_dir`` (monkeypatched to ``tmp_path``).
"""

from __future__ import annotations

import asyncio
import functools
import io
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import httpx
import pytest
from alembic import command
from alembic.config import Config
from PIL import Image
from sqlalchemy import delete, select, text
from src.core.config import get_settings
from src.core.db import dispose_engine, get_engine, get_sessionmaker
from src.core.security import create_access_token, hash_password
from src.main import create_app
from src.models import Farm, Farmer, Plot, PlotImage, User, UserRole

REPO_ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "Sup3rSecret-Pass!"
SEED_ROLES = (
    ("alpha", UserRole.farmer),
    ("bravo", UserRole.farmer),
    ("officer", UserRole.extension_officer),
    ("admin", UserRole.admin),
)
MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 25_000_000


def base(farm_id: uuid.UUID, plot_id: uuid.UUID) -> str:
    return f"/api/v1/farms/{farm_id}/plots/{plot_id}/images"


def _image_bytes(fmt: str, *, size: tuple[int, int] = (4, 4), mode: str = "RGB") -> bytes:
    buffer = io.BytesIO()
    color: int | tuple[int, int, int] = (40, 160, 40) if mode in {"RGB", "RGBA"} else 1
    Image.new(mode, size, color).save(buffer, fmt)
    return buffer.getvalue()


def _png() -> bytes:
    return _image_bytes("PNG")


def _jpeg() -> bytes:
    return _image_bytes("JPEG")


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


@pytest.fixture
def _upload_dir(tmp_path: Path) -> Generator[Path, None, None]:
    settings = get_settings()
    original = settings.upload_dir
    settings.upload_dir = tmp_path
    try:
        yield tmp_path
    finally:
        settings.upload_dir = original


@functools.lru_cache(maxsize=1)
def _seed_password_hash() -> str:
    return hash_password(PASSWORD)


@pytest.fixture
async def _ctx(_db: None) -> AsyncGenerator[dict[str, Any], None]:
    """users + farm A (alpha) with two plots + farm B (bravo) with one plot."""
    session = get_sessionmaker()()
    users: dict[str, User] = {}
    password_hash = _seed_password_hash()
    for name, role in SEED_ROLES:
        user = User(
            email=f"img-{name}-{uuid.uuid4().hex[:8]}@example.com",
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
    await session.flush()
    plot_a = Plot(farm_id=farm_a.id, name="Block A")
    plot_a2 = Plot(farm_id=farm_a.id, name="Block A2")
    plot_b = Plot(farm_id=farm_b.id, name="Block B")
    session.add_all([plot_a, plot_a2, plot_b])
    await session.commit()
    try:
        yield {
            "users": users,
            "farm_a": farm_a.id,
            "farm_b": farm_b.id,
            "plot_a": plot_a.id,
            "plot_a2": plot_a2.id,
            "plot_b": plot_b.id,
        }
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


def _files(data: bytes, *, filename: str = "leaf.png", content_type: str = "image/png") -> dict:
    return {"file": (filename, data, content_type)}


async def _rows_for(plot_id: uuid.UUID) -> list[PlotImage]:
    session = get_sessionmaker()()
    try:
        return list(
            (await session.execute(select(PlotImage).where(PlotImage.plot_id == plot_id)))
            .scalars()
            .all()
        )
    finally:
        await session.close()


async def test_upload_happy_path_sniffs_and_stores(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    data = _png()
    async with await _client() as client:
        response = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(data, filename="leaf.png", content_type="image/jpeg"),
            headers=_headers(users["alpha"]),
        )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["plot_id"] == str(_ctx["plot_a"])
    assert body["content_type"] == "image/png"  # sniff wins over declared jpeg
    assert body["size_bytes"] == len(data)
    assert body["original_name"] == "leaf.png"
    assert body["url"].endswith(f"/images/{body['id']}")

    stored = list(_upload_dir.iterdir())
    assert len(stored) == 1
    assert stored[0].suffix == ".png"
    assert stored[0].name != "leaf.png"  # server-generated name, not the client's
    assert stored[0].read_bytes() == data

    rows = await _rows_for(_ctx["plot_a"])
    assert len(rows) == 1
    assert rows[0].content_type == "image/png"
    assert rows[0].stored_name == stored[0].name
    assert rows[0].uploaded_by == users["alpha"].id


async def test_get_round_trip_serves_bytes_inline(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    data = _jpeg()
    async with await _client() as client:
        uploaded = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(data, filename="x.jpg", content_type="image/jpeg"),
            headers=_headers(users["alpha"]),
        )
        fetched = await client.get(
            f"{base(_ctx['farm_a'], _ctx['plot_a'])}/{uploaded.json()['id']}",
            headers=_headers(users["alpha"]),
        )
    assert fetched.status_code == 200
    assert fetched.content == data
    assert fetched.headers["content-type"] == "image/jpeg"
    assert fetched.headers["x-content-type-options"] == "nosniff"


async def test_list_returns_plot_images_with_url(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    async with await _client() as client:
        await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(_png()),
            headers=_headers(users["alpha"]),
        )
        listed = await client.get(
            base(_ctx["farm_a"], _ctx["plot_a"]), headers=_headers(users["alpha"])
        )
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["items"][0]["url"].startswith("/api/v1/farms/")
    assert body["items"][0]["content_type"] == "image/png"


async def test_authz_matrix_on_both_verbs(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    farm_a, plot_a = _ctx["farm_a"], _ctx["plot_a"]
    async with await _client() as client:
        anon = [
            await client.post(base(farm_a, plot_a), files=_files(_png())),
            await client.get(base(farm_a, plot_a)),
        ]
        officer_upload = await client.post(
            base(farm_a, plot_a), files=_files(_png()), headers=_headers(users["officer"])
        )
        officer_list = await client.get(base(farm_a, plot_a), headers=_headers(users["officer"]))
        owner_upload = await client.post(
            base(farm_a, plot_a), files=_files(_png()), headers=_headers(users["alpha"])
        )
        image_id = owner_upload.json()["id"]
        non_owner = [
            await client.post(
                base(farm_a, plot_a), files=_files(_png()), headers=_headers(users["bravo"])
            ),
            await client.get(
                base(farm_a, plot_a),
                headers=_headers(users["bravo"]),
            ),
        ]
        unknown_plot = await client.post(
            base(farm_a, uuid.uuid4()), files=_files(_png()), headers=_headers(users["alpha"])
        )
        cross_plot = await client.get(
            f"{base(farm_a, _ctx['plot_a2'])}/{image_id}", headers=_headers(users["alpha"])
        )
    assert [r.status_code for r in anon] == [401, 401]
    assert officer_upload.status_code == 403
    assert officer_list.status_code == 200
    assert owner_upload.status_code == 201
    assert [r.status_code for r in non_owner] == [404, 404]
    assert unknown_plot.status_code == 404
    assert cross_plot.status_code == 404


async def test_payload_over_limit_is_413(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    async with await _client() as client:
        response = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(b"A" * (MAX_BYTES + 1)),
            headers=_headers(users["alpha"]),
        )
    assert response.status_code == 413
    assert response.json()["error_code"] == "payload_too_large"
    assert list(_upload_dir.iterdir()) == []
    assert await _rows_for(_ctx["plot_a"]) == []


async def test_pixel_dimensions_over_limit_are_413(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    size = 5001  # 5001 * 5001 = 25,010,001 > 25,000,000, still a tiny file
    data = _image_bytes("PNG", size=(size, size), mode="1")
    assert len(data) < 1024 * 1024
    async with await _client() as client:
        response = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(data),
            headers=_headers(users["alpha"]),
        )
    assert response.status_code == 413
    assert response.json()["error_code"] == "image_too_large"
    assert list(_upload_dir.iterdir()) == []


async def test_non_image_payloads_are_415(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    async with await _client() as client:
        text_response = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(b"just some text", filename="leaf.png"),
            headers=_headers(users["alpha"]),
        )
        gif_response = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(_image_bytes("GIF", mode="P"), filename="anim.gif"),
            headers=_headers(users["alpha"]),
        )
    assert [text_response.status_code, gif_response.status_code] == [415, 415]
    assert text_response.json()["error_code"] == "unsupported_media_type"
    assert gif_response.json()["error_code"] == "unsupported_media_type"


async def test_truncated_image_is_422(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    truncated = _jpeg()[: len(_jpeg()) // 2]
    async with await _client() as client:
        response = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(truncated, filename="cut.jpg"),
            headers=_headers(users["alpha"]),
        )
    assert response.status_code == 422, response.text
    assert response.json()["error_code"] == "invalid_image"
    assert list(_upload_dir.iterdir()) == []


async def test_deleting_a_plot_cascades_image_rows(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    async with await _client() as client:
        uploaded = await client.post(
            base(_ctx["farm_a"], _ctx["plot_a"]),
            files=_files(_png()),
            headers=_headers(users["alpha"]),
        )
        assert uploaded.status_code == 201
        deleted = await client.delete(
            f"/api/v1/farms/{_ctx['farm_a']}/plots/{_ctx['plot_a']}",
            headers=_headers(users["admin"]),
        )
    assert deleted.status_code == 204
    assert await _rows_for(_ctx["plot_a"]) == []


async def test_invalid_image_ids_are_404(_ctx: dict[str, Any], _upload_dir: Path) -> None:
    users = _ctx["users"]
    async with await _client() as client:
        missing = await client.get(
            f"{base(_ctx['farm_a'], _ctx['plot_a'])}/{uuid.uuid4()}",
            headers=_headers(users["alpha"]),
        )
    assert missing.status_code == 404
    assert missing.json()["error_code"] == "not_found"
