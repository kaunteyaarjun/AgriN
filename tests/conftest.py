"""Shared test fixtures (M055, extended M056).

Two pieces of process-wide state would otherwise leak across test
cases: the in-process rate limiter (src/core/ratelimit, M055) and the
MODIS calendar cache (src/providers/satellite_live, M056) — every test
starts clean here (M055 note: add future process-wide state resets
alongside these).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator

import pytest
from src.core.ratelimit import limiter


@pytest.fixture(autouse=True)
async def _reset_rate_limiter() -> AsyncGenerator[None, None]:
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _reset_modis_calendar() -> Generator[None, None]:
    from src.providers.satellite_live import reset_calendar_cache

    reset_calendar_cache()
    yield
    reset_calendar_cache()
