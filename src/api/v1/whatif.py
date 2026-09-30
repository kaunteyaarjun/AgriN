"""What-if simulation API (M045): POST a hypothetical, get the diff.

House route order (as M043 wrote it): M014's read matrix first — a
simulation *reads* stored state and writes nothing, so read
authorization is the right gate — then the authz-free service, which
loads the twin and runs M044's engine under one clock.

The route maps the engine's ``ValueError`` onto 422
``ValidationFailed`` verbatim (the message already names the offending
knob, so no sanitization is needed); pydantic rejects structural
problems before the handler runs, hence the two accepted 422 flavors
(M020 precedent, unify in M055). Nothing here calls a provider, so
there is no 502 path — M043's ``UpstreamUnavailable`` stays the single
upstream-failure mapping for routes that do call out.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body
from pydantic import BaseModel

from src.api.deps import CurrentUserDep, SessionDep
from src.api.v1.farms import _authorized_farm
from src.core.errors import ValidationFailed
from src.engines.whatif import WhatIfResult
from src.services.whatif import simulate_farm_what_if

router = APIRouter(prefix="/farms", tags=["what-if"])


class WhatIfRequest(BaseModel):
    """Structure only — M044's WHAT_IF_KNOBS catalogue decides semantics."""

    overrides: dict[str, dict[str, Any]]


@router.post("/{farm_id}/what-if", response_model=WhatIfResult)
async def run_farm_what_if(
    farm_id: uuid.UUID,
    request: Annotated[WhatIfRequest, Body()],
    session: SessionDep,
    current: CurrentUserDep,
) -> WhatIfResult:
    """Re-run this farm's analysis under ``request.overrides`` (read matrix)."""
    await _authorized_farm(session, farm_id, current, for_write=False)
    try:
        return await simulate_farm_what_if(session, farm_id, request.overrides)
    except ValueError as exc:
        raise ValidationFailed(str(exc)) from exc
