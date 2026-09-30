"""Sliding-window rate limiter unit tests (M055) — pure, clock injected."""

from __future__ import annotations

from src.core.ratelimit import MAX_KEYS, SlidingWindowLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _limiter() -> tuple[SlidingWindowLimiter, FakeClock]:
    clock = FakeClock()
    return SlidingWindowLimiter(clock=clock), clock


def test_allows_up_to_the_limit_then_blocks() -> None:
    limiter, _ = _limiter()
    for _ in range(3):
        assert limiter.record("login:1.2.3.4", limit=3).allowed
    decision = limiter.record("login:1.2.3.4", limit=3)
    assert not decision.allowed
    assert decision.retry_after >= 1


def test_window_slides_and_old_hits_expire() -> None:
    limiter, clock = _limiter()
    for _ in range(3):
        limiter.record("k", limit=3)
    assert not limiter.record("k", limit=3).allowed
    clock.advance(60.0)  # every hit ages out
    assert limiter.record("k", limit=3).allowed


def test_blocked_attempts_do_not_extend_the_lockout() -> None:
    limiter, clock = _limiter()
    for _ in range(2):
        limiter.record("k", limit=2)
    # hammer the blocked state: none of these are recorded
    for _ in range(50):
        assert not limiter.record("k", limit=2).allowed
    clock.advance(60.0)
    assert limiter.record("k", limit=2).allowed  # window not extended by abuse


def test_keys_are_isolated() -> None:
    limiter, _ = _limiter()
    for _ in range(2):
        limiter.record("bucket:a", limit=2)
    assert not limiter.record("bucket:a", limit=2).allowed
    assert limiter.record("bucket:b", limit=2).allowed  # other key unaffected


def test_retry_after_counts_down_with_age() -> None:
    limiter, clock = _limiter()
    limiter.record("k", limit=1)
    clock.advance(59.0)
    decision = limiter.record("k", limit=1)
    assert not decision.allowed
    assert decision.retry_after == 2  # 1s of window left, rounded up


def test_capacity_evicts_the_oldest_key() -> None:
    clock = FakeClock()
    limiter = SlidingWindowLimiter(clock=clock, max_keys=2)
    limiter.record("one", limit=5)
    limiter.record("two", limit=5)
    limiter.record("three", limit=5)  # evicts "one"
    assert len(limiter._hits) == 2  # noqa: SLF001 - asserting the bound itself
    assert "one" not in limiter._hits  # noqa: SLF001
    # the evicted key starts fresh (its history is gone, by design)
    assert limiter.record("one", limit=1).allowed


def test_reset_forgets_everything() -> None:
    limiter, _ = _limiter()
    limiter.record("k", limit=1)
    assert not limiter.record("k", limit=1).allowed
    limiter.reset()
    assert limiter.record("k", limit=1).allowed


def test_max_keys_default_is_bounded() -> None:
    assert MAX_KEYS == 10_000
