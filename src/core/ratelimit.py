"""In-process sliding-window rate limiter (M055).

Deliberately stdlib-only (locked decision: no new dependency): a deque
of monotonic timestamps per key, pruned on access. The critical
section performs no ``await``, so it is safe on a single event loop.

**Known limitation:** state lives in this process — with multiple
workers each worker enforces its own window, so the effective global
limit is ``limit x workers``. A shared store (Redis etc.) is the fix
and was explicitly refused for now; revisit if the API is ever run
multi-worker behind a public LB.
"""

from __future__ import annotations

import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request

from src.core.audit import audit
from src.core.config import get_settings
from src.core.errors import RateLimited

WINDOW_SECONDS = 60.0
MAX_KEYS = 10_000
"""Memory bound: oldest key is evicted when the table is full."""


@dataclass
class Decision:
    allowed: bool
    retry_after: int  # seconds until the oldest hit leaves the window (0 if allowed)


class SlidingWindowLimiter:
    """Timestamps-per-key sliding window with a bounded key table."""

    def __init__(
        self,
        *,
        window_seconds: float = WINDOW_SECONDS,
        max_keys: int = MAX_KEYS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._window = window_seconds
        self._max_keys = max_keys
        self._clock = clock
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()

    def record(self, key: str, limit: int) -> Decision:
        """Count one hit for ``key``; decide against ``limit``.

        A blocked attempt is NOT recorded (it would let an attacker
        extend their own lockout forever).
        """
        now = self._clock()
        bucket = self._hits.get(key)
        if bucket is None:
            if len(self._hits) >= self._max_keys:
                self._hits.popitem(last=False)  # FIFO eviction
            bucket = deque()
            self._hits[key] = bucket
        else:
            self._hits.move_to_end(key)
        while bucket and now - bucket[0] >= self._window:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(self._window - (now - bucket[0])) + 1)
            return Decision(allowed=False, retry_after=retry_after)
        bucket.append(now)
        return Decision(allowed=True, retry_after=0)

    def reset(self) -> None:
        """Forget every key (test hygiene: autouse fixture)."""
        self._hits.clear()


limiter = SlidingWindowLimiter()
"""Process-wide instance (tests reset it between cases)."""


def rate_limit(bucket: str) -> Callable[[Request], None]:
    """Dependency factory: enforce ``settings.auth_rate_limit_per_minute``
    for ``bucket`` keyed by client IP. Raises ``RateLimited`` (429)."""

    def _dep(request: Request) -> None:
        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"
        decision = limiter.record(f"{bucket}:{client_ip}", settings.auth_rate_limit_per_minute)
        if not decision.allowed:
            audit(
                "rate_limited.blocked",
                outcome="blocked",
                ip=client_ip,
                bucket=bucket,
                retry_after=decision.retry_after,
            )
            raise RateLimited(retry_after=decision.retry_after)

    return _dep
