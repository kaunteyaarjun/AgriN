"""Shared test fixtures (M055).

The in-process rate limiter (src/core/ratelimit) keeps state for the
process lifetime, which would leak across test cases — every test
starts from a clean window here (M055 note: add future process-wide
state resets alongside this one).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from src.core.ratelimit import limiter


@pytest.fixture(autouse=True)
async def _reset_rate_limiter() -> AsyncGenerator[None, None]:
    limiter.reset()
    yield
    limiter.reset()
