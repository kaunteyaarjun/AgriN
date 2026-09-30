"""Deterministic demo seed (M054): one command, one fixed world.

Writes through the ORM and M019's write paths (``set_plot_state``,
``put_signals``) — no API routes, no authz: this is not a reachable
surface. Every entity's primary key derives from ``uuid5`` over a
fixed namespace, so re-running **upserts in place** instead of
duplicating (delete-and-recreate is deliberately avoided: it would
cascade away artifacts someone attached later, M035).

Timestamps are seed-relative while content is fixed: signal
``observed_at`` is ``now - 30 min`` and ``planted_on`` is
``today - N days``, because a fixed absolute date would be stale by
demo time. Determinism means the same world *shape*, not the same
clock reading.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.core.security import hash_password
from src.models import Farm, Farmer, Plot, User, UserRole
from src.services.farm_state import put_signals, set_plot_state

SEED_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "agrin.demo.seed")
"""Fixed namespace: identical ids on every machine and every run."""

DEV_DEMO_PASSWORD = "Demo-Passw0rd!"
"""Dev-only fallback; prod requires an explicit ``demo_password`` (M002)."""


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, key)


def resolve_demo_password(settings: Settings) -> str:
    """Settings value, else the dev default — prod refuses to guess."""
    if settings.demo_password is not None:
        return settings.demo_password.get_secret_value()
    if settings.env == "prod":
        raise ValueError("demo_password must be set explicitly when env=prod.")
    return DEV_DEMO_PASSWORD


class SeedSummary(BaseModel):
    """What one seed run created or refreshed."""

    users: int
    farmers: int
    farms: int
    plots: int
    plot_states: int
    signal_caches: int


# ---------- fixed world constants ----------

USERS: tuple[tuple[str, str, str, UserRole], ...] = (
    ("admin", "admin@agrin.demo", "AgriN Admin", UserRole.admin),
    ("officer", "officer@agrin.demo", "Extension Officer", UserRole.extension_officer),
    ("maria", "maria@agrin.demo", "Maria Demo", UserRole.farmer),
    ("joseph", "joseph@agrin.demo", "Joseph Demo", UserRole.farmer),
)
# (key, farmer_key, name, area_hectares, geojson polygon)
FARMS: tuple[tuple[str, str, str, str, dict[str, Any]], ...] = (
    (
        "east",
        "maria",
        "Demo Farm East",
        "20.00",
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [36.820, -1.280],
                    [36.824, -1.280],
                    [36.824, -1.276],
                    [36.820, -1.276],
                    [36.820, -1.280],
                ]
            ],
        },
    ),
    (
        "west",
        "joseph",
        "Demo Farm West",
        "16.00",
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [36.780, -1.310],
                    [36.784, -1.310],
                    [36.784, -1.306],
                    [36.780, -1.306],
                    [36.780, -1.310],
                ]
            ],
        },
    ),
)
# (plot_key, farm_key, name, crop, stage, days_since_planted)
PLOTS: tuple[tuple[str, str, str, str, str, int], ...] = (
    ("east-1", "east", "East Block A", "Maize", "vegetative", 20),
    ("east-2", "east", "East Block B", "Wheat", "flowering", 35),
    ("west-1", "west", "West Block A", "Maize", "vegetative", 20),
    ("west-2", "west", "West Block B", "Beans", "fruiting", 45),
)
_EAST_SIGNALS: dict[str, dict[str, Any]] = {
    "weather": {"temperature_c": 22.0, "humidity_pct": 55.0, "rainfall_mm_24h": 5.0},
    "satellite": {"ndvi": 0.62, "cloud_cover_pct": 10.0},
    "soil": {
        "soil_moisture_pct": 45.0,
        "ph": 6.5,
        "soil_temperature_c": 18.0,
        "nitrogen_kg_ha": 60.0,
    },
}
_WEST_SIGNALS: dict[str, dict[str, Any]] = {
    "weather": {"temperature_c": 27.0, "humidity_pct": 40.0, "rainfall_mm_24h": 0.0},
    "satellite": {"ndvi": 0.44, "cloud_cover_pct": 5.0},
    "soil": {
        "soil_moisture_pct": 22.0,
        "ph": 5.8,
        "soil_temperature_c": 21.0,
        "nitrogen_kg_ha": 25.0,
    },
}
_SIGNAL_SOURCES: dict[str, str] = {
    "weather": "demo-weather-v1",
    "satellite": "demo-satellite-v1",
    "soil": "demo-soil-v1",
}
_OBSERVED_LEAD = timedelta(minutes=30)


def _signals_for(farm_key: str, observed_at: datetime) -> dict[str, Any]:
    """Fixed values + fixed sources + a seed-relative timestamp."""
    template = _EAST_SIGNALS if farm_key == "east" else _WEST_SIGNALS
    observed = observed_at.isoformat()
    return {
        family: {
            **values,
            **({"wind_speed_kmh": 10.0, "condition": "clear"} if family == "weather" else {}),
            "observed_at": observed,
            "source": _SIGNAL_SOURCES[family],
        }
        for family, values in template.items()
    }


async def _upsert_user(
    session: AsyncSession, *, key: str, email: str, role: UserRole, password_hash: str
) -> User:
    user = await session.get(User, _id(f"user:{key}"))
    if user is None:
        user = User(id=_id(f"user:{key}"), email=email, password_hash=password_hash, role=role)
        session.add(user)
    else:
        user.password_hash = password_hash  # re-seed refreshes the secret
        user.role = role
        user.is_active = True
    return user


async def seed_demo(
    session: AsyncSession, *, password: str, now: datetime | None = None
) -> SeedSummary:
    """Create or refresh the fixed demo world. Commits (a writer, M019-style).

    Caller owns the session. Idempotent: fixed ids mean a second run
    updates rows in place; unique-email conflicts only appear if a
    pre-existing row already claimed a ``@agrin.demo`` address under a
    different id (documented, not handled — the seed owns those
    addresses).
    """
    moment = now or datetime.now(UTC)
    password_hash = hash_password(password)
    observed_at = moment - _OBSERVED_LEAD
    today = moment.date()

    users: dict[str, User] = {}
    for key, email, _name, role in USERS:
        users[key] = await _upsert_user(
            session, key=key, email=email, role=role, password_hash=password_hash
        )

    farmers: dict[str, Farmer] = {}
    for key, _email, name, _role in USERS[2:]:
        farmer_id = _id(f"farmer:{key}")
        farmer = await session.get(Farmer, farmer_id)
        if farmer is None:
            farmer = Farmer(id=farmer_id, user_id=users[key].id, full_name=name)
            session.add(farmer)
        else:
            farmer.full_name = name
        farmers[key] = farmer

    for farm_key, farmer_key, name, area, geo in FARMS:
        farm = await session.get(Farm, _id(f"farm:{farm_key}"))
        if farm is None:
            farm = Farm(
                id=_id(f"farm:{farm_key}"),
                farmer_id=farmers[farmer_key].id,
                name=name,
                area_hectares=Decimal(area),
                geo=func.ST_GeomFromGeoJSON(json.dumps(geo)),
            )
            session.add(farm)
        else:
            farm.name = name
            farm.area_hectares = Decimal(area)
            farm.geo = func.ST_GeomFromGeoJSON(json.dumps(geo))

    plot_ids: dict[str, uuid.UUID] = {}
    for plot_key, farm_key, name, *_rest in PLOTS:
        plot_id = _id(f"plot:{plot_key}")
        plot = await session.get(Plot, plot_id)
        if plot is None:
            plot = Plot(id=plot_id, farm_id=_id(f"farm:{farm_key}"), name=name)
            session.add(plot)
        else:
            plot.name = name
        plot_ids[plot_key] = plot_id
    await session.commit()  # flush users/farmers/farms/plots before the M019 writes

    for plot_key, _farm_key, _name, crop, stage, days in PLOTS:
        await set_plot_state(
            session,
            plot_ids[plot_key],
            crop=crop,
            growth_stage=stage,
            planted_on=today - timedelta(days=days),
        )

    for farm_key, *_rest in FARMS:
        await put_signals(
            session,
            _id(f"farm:{farm_key}"),
            signals=_signals_for(farm_key, observed_at),
            refreshed_at=observed_at,
        )

    farmer_count = await session.scalar(select(func.count()).select_from(Farmer))
    return SeedSummary(
        users=len(USERS),
        farmers=int(farmer_count or 0),
        farms=len(FARMS),
        plots=len(PLOTS),
        plot_states=len(PLOTS),
        signal_caches=len(FARMS),
    )


def demo_emails() -> list[str]:
    """The fixed login addresses (for the CLI banner and tests)."""
    return [email for _key, email, _name, _role in USERS]
