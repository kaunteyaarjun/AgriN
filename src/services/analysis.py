"""Farm analysis service (M043): load the twin, run the pipeline.

**Authorization is deliberately NOT done here** (M019 standing rule):
the calling route authorizes the farm first (``_authorized_farm``,
M014); ``analyze_farm`` assumes an authorized caller and is tested as
such.

Read-only: it reuses ``get_farm_state`` (M019's constant 3 queries) and
never commits. The single ``now`` is threaded into both the twin view
and the pipeline, so staleness and ``decision.computed_at`` describe
the same moment.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.engines.disease import DiseaseAssessment
from src.engines.pipeline import FarmAnalysis, run_analysis
from src.services.farm_state import get_farm_state
from src.services.normalize import NormalizedFarmState, normalize_signals


async def analyze_farm(
    session: AsyncSession,
    farm_id: uuid.UUID,
    *,
    now: datetime | None = None,
    disease: Sequence[DiseaseAssessment] = (),
) -> FarmAnalysis:
    """Assemble this farm's *current stored state* into one analysis.

    Raises ``NotFound`` for an unknown farm (from ``get_farm_state``).
    No authz — callers authorize first.
    """
    moment = now or datetime.now(UTC)
    view = await get_farm_state(session, farm_id, now=moment)
    state = NormalizedFarmState(
        view=view,
        signals=normalize_signals(
            view.signals.signals, now=moment, refreshed_at=view.signals.refreshed_at
        ),
    )
    return run_analysis(state, disease, now=moment)
