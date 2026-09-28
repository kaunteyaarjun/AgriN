"""Shared ingestion result types (extracted M029, rule of three).

``IngestStatus`` / ``IngestResult`` / ``IngestSummary`` were defined
verbatim in `weather.py` (M023) and `satellite.py` (M026); soil (M029)
would have been the third copy, so all three families now import from
here. Shapes are unchanged — one status literal per farm attempt, a
result per farm, and a summary that counts results by status.
"""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel

IngestStatus = Literal["ingested", "skipped_no_geo", "provider_error", "failed"]


class IngestResult(BaseModel):
    """Outcome of one farm's ingestion attempt."""

    farm_id: uuid.UUID
    status: IngestStatus
    observation_id: uuid.UUID | None = None
    detail: str | None = None


class IngestSummary(BaseModel):
    """Aggregate outcome of a batch run."""

    ingested: int = 0
    skipped_no_geo: int = 0
    provider_error: int = 0
    failed: int = 0
    results: list[IngestResult] = []

    def record(self, result: IngestResult) -> None:
        self.results.append(result)
        setattr(self, result.status, getattr(self, result.status) + 1)
