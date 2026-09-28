"""Soil ingestion runner (M029).

Usage:
    uv run python -m workers.soil_ingest                # all farms
    uv run python -m workers.soil_ingest --farm <uuid>  # one farm

Prints one status line per farm plus a summary. Exit code 0 even when
individual farms failed (the summary shows them); non-zero only when
the run itself dies (e.g. database unreachable).
"""

from __future__ import annotations

import argparse
import asyncio
import uuid

from src.core.db import dispose_engine, get_sessionmaker
from src.ingestion.soil import ingest_soil_for_all, ingest_soil_for_farm


async def _run(farm: uuid.UUID | None) -> int:
    session = get_sessionmaker()()
    try:
        if farm is None:
            summary = await ingest_soil_for_all(session)
            for result in summary.results:
                detail = f" ({result.detail})" if result.detail else ""
                print(f"{result.farm_id} {result.status}{detail}")
            print(
                "summary: "
                f"ingested={summary.ingested} "
                f"skipped_no_geo={summary.skipped_no_geo} "
                f"provider_error={summary.provider_error} "
                f"failed={summary.failed}"
            )
        else:
            result = await ingest_soil_for_farm(session, farm)
            detail = f" ({result.detail})" if result.detail else ""
            print(f"{result.farm_id} {result.status}{detail}")
        return 0
    finally:
        await session.close()
        await dispose_engine()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest soil readings for farms")
    parser.add_argument("--farm", type=uuid.UUID, default=None, help="single farm id")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.farm)))


if __name__ == "__main__":
    main()
