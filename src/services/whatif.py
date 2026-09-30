"""What-if simulation service (M045): load the twin, run the simulation.

**Authorization is deliberately NOT done here** (M019 standing rule):
the calling route authorizes the farm first (``_authorized_farm``,
M014 read matrix); ``simulate_farm_what_if`` assumes an authorized
caller.

Read-only: it reuses ``get_farm_state`` and never commits — a what-if
computes, it does not persist. Mirrors ``analyze_farm`` (M043) but
hands the loaded state to M044's engine instead of running the
pipeline itself (the engine runs it twice), and threads a single
``now`` into *both* the twin load and the engine so the baseline, the
hypothetical and the signal ages they were computed from describe the
same moment.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.engines.disease import DiseaseAssessment
from src.engines.whatif import WhatIfResult, simulate_what_if
from src.services.farm_state import get_farm_state
from src.services.normalize import NormalizedFarmState, normalize_signals


async def simulate_farm_what_if(
    session: AsyncSession,
    farm_id: uuid.UUID,
    overrides: Mapping[str, Mapping[str, Any]],
    *,
    now: datetime | None = None,
    disease: Sequence[DiseaseAssessment] = (),
) -> WhatIfResult:
    """Simulate ``overrides`` against this farm's *current stored state*.

    Raises ``NotFound`` for an unknown farm (from ``get_farm_state``)
    and ``ValueError`` for a caller-bad override set (M044's contract:
    empty, unknown family/knob, non-numeric, out-of-range, malformed
    family, windowless rainfall — the message names the offending
    knob). No authz — callers authorize first.
    """
    moment = now or datetime.now(UTC)
    view = await get_farm_state(session, farm_id, now=moment)
    state = NormalizedFarmState(
        view=view,
        signals=normalize_signals(
            view.signals.signals, now=moment, refreshed_at=view.signals.refreshed_at
        ),
    )
    return simulate_what_if(state, overrides, now=moment, disease=disease)
