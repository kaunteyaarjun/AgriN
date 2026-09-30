"""Demo seed runner (M054).

Usage:
    uv run python -m workers.seed_demo

Creates or refreshes the fixed demo world (users, farms, plots,
signals) in the configured database. Re-running is safe: fixed UUIDs
upsert in place. Prints the login credentials once.

Idempotent upsert, never a wipe — so run it AFTER the quality gate
(test_migrations' round-trip drops all rows; M012 lesson).
"""

from __future__ import annotations

import asyncio

from src.core.config import get_settings
from src.core.db import dispose_engine, get_sessionmaker
from src.services.demo_seed import demo_emails, resolve_demo_password, seed_demo


async def _run() -> int:
    settings = get_settings()
    password = resolve_demo_password(settings)  # refuses env=prod without a value
    session = get_sessionmaker()()
    try:
        summary = await seed_demo(session, password=password)
        print(
            "seeded: "
            f"users={summary.users} "
            f"farmers={summary.farmers} "
            f"farms={summary.farms} "
            f"plots={summary.plots} "
            f"plot_states={summary.plot_states} "
            f"signal_caches={summary.signal_caches}"
        )
        print("log in with:")
        for email in demo_emails():
            print(f"  {email} / {password}")
        return 0
    finally:
        await session.close()
        await dispose_engine()


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
