"""Advisory API (M043): one GET that answers "what should I do?".

House route order: M014's authorization helper first (``_authorized_farm``,
read matrix — admin/officer/owner read, non-owner → 404, anon → 401),
then the analysis service (which does no authz, M019/M043 contract),
then M041's advisory generation over the decision it produced.

Provider failures — upstream unavailable *or* M041's output policy
rejecting the answer — are mapped here onto one sanitized 502, so the
client never sees provider internals or the model's raw failure. The
route recomputes on every call: nothing about an advisory is persisted
or cached (rate limiting is M055's).
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from src.ai.advisory import Advisory, generate_advisory
from src.api.deps import CurrentUserDep, SessionDep
from src.api.v1.farms import _authorized_farm
from src.core.errors import UpstreamUnavailable
from src.engines.decision import FarmDecision
from src.providers.errors import ProviderError
from src.services.analysis import analyze_farm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farms", tags=["advisory"])


class AdvisoryResponse(BaseModel):
    """The prose and the structure behind it, from one analysis run."""

    advisory: Advisory
    decision: FarmDecision


@router.get("/{farm_id}/advisory", response_model=AdvisoryResponse)
async def read_farm_advisory(
    farm_id: uuid.UUID, session: SessionDep, current: CurrentUserDep
) -> AdvisoryResponse:
    """Current-state advisory for one farm (read matrix; recomputed)."""
    await _authorized_farm(session, farm_id, current, for_write=False)
    analysis = await analyze_farm(session, farm_id)
    try:
        advisory = await generate_advisory(analysis.decision)
    except ProviderError as exc:
        logger.warning(
            "advisory_provider_failed",
            extra={"farm_id": str(farm_id), "reason": type(exc).__name__},
        )
        raise UpstreamUnavailable() from exc
    return AdvisoryResponse(advisory=advisory, decision=analysis.decision)
