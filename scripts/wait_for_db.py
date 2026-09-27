"""Wait until the configured Postgres database accepts connections.

Used by tests/CI so they don't race the ``docker compose`` db container.

Usage:
    uv run python -m scripts.wait_for_db [--timeout 30]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from sqlalchemy import text
from src.core.config import get_settings
from src.core.db import dispose_engine, get_engine, redact_database_url


async def _ping() -> None:
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def wait_for_db(timeout: float, interval: float) -> int:
    settings = get_settings()
    if not settings.database_url:
        print("database_url is not configured (set DATABASE_URL).", file=sys.stderr)
        return 2

    target = redact_database_url(settings.database_url)
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            await _ping()
            print(f"Database ready after {attempt} attempt(s): {target}")
            return 0
        except Exception as exc:  # noqa: BLE001 - report and retry
            if time.monotonic() >= deadline:
                print(
                    f"Database not ready after {timeout:.0f}s ({target}): {exc}",
                    file=sys.stderr,
                )
                return 1
            await asyncio.sleep(interval)


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Wait for the dev Postgres to be ready.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    try:
        return await wait_for_db(args.timeout, args.interval)
    finally:
        await dispose_engine()


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
