"""What-if simulation engine (M044): perturb the state, re-run the chain.

``simulate_what_if`` takes the farm's *stored* normalized state, applies
a closed catalogue of signal overrides (``WHAT_IF_KNOBS``), and runs
M043's ``run_analysis`` twice under one clock — untouched baseline and
hypothetical — returning both analyses plus a structured diff.

Pure, like the rest of the package: no DB, no network, no clock beyond
the injectable ``now``. Every *rule* still lives in M032/M033/M034/M039
— this module only changes inputs and reports what moved.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Final

from pydantic import BaseModel

from src.engines.decision import DecisionAction
from src.engines.disease import DiseaseAssessment
from src.engines.pipeline import FarmAnalysis, run_analysis
from src.services.farm_state import SignalCacheView
from src.services.normalize import (
    EARTH_TEMPERATURE_RANGE,
    NDVI_RANGE,
    PERCENT_RANGE,
    PH_RANGE,
    NormalizedFarmState,
    normalize_signals,
)

WHAT_IF_KNOBS: Final[dict[str, dict[str, tuple[float | None, float | None]]]] = {
    "weather": {
        "temperature_c": EARTH_TEMPERATURE_RANGE,
        "rainfall_mm_24h": (0.0, None),
    },
    "soil": {
        "soil_moisture_pct": PERCENT_RANGE,
        "ph": PH_RANGE,
        "nitrogen_kg_ha": (0.0, None),
    },
    "satellite": {"ndvi": NDVI_RANGE},
}
"""family -> knob field -> allowed range.

Only fields an engine actually scores (M032 health, and through it
M033/M034/M039): a knob that cannot move an answer must not exist.
"""

Bound = tuple[float | None, float | None]


class WhatIfChanges(BaseModel):
    """Headline diff, hypothetical minus baseline.

    ``None`` means "unchanged" for the categorical fields; both full
    analyses are on the result, so any richer diff stays derivable.
    """

    stance: str | None
    health_level: str | None
    risk_score_delta: int
    risk_band: str | None
    action_counts_delta: dict[str, int]
    actions_added: list[DecisionAction]
    actions_removed: list[DecisionAction]


class WhatIfResult(BaseModel):
    """One simulation: both runs, what moved, and what was changed."""

    baseline: FarmAnalysis
    hypothetical: FarmAnalysis
    changes: WhatIfChanges
    overrides_applied: dict[str, dict[str, float]]
    simulated_families: list[str]


def _range_label(bound: Bound) -> str:
    low, high = bound
    return f"[{'-inf' if low is None else low}, {'+inf' if high is None else high}]"


def _validated_value(family: str, field: str, value: Any, bound: Bound) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{family}.{field} must be a number, got {type(value).__name__}.")
    low, high = bound
    number = float(value)
    if (low is not None and number < low) or (high is not None and number > high):
        raise ValueError(
            f"{family}.{field}={number} is outside the allowed range {_range_label(bound)}."
        )
    return number


def _apply_overrides(
    state: NormalizedFarmState,
    overrides: Mapping[str, Mapping[str, Any]],
    moment: datetime,
) -> tuple[NormalizedFarmState, dict[str, dict[str, float]], list[str]]:
    """Validate the knobs, rewrite the raw document, re-normalize.

    An overridden family is re-stamped to ``moment`` (a hypothetical is
    a statement about *now*, and a stale timestamp would let M032
    discard the value just changed); a family the farm never ingested
    is materialized with ``observed_at = moment`` and **no source** —
    provenance is never invented.
    """
    doc: dict[str, Any] = {
        family: dict(raw) if isinstance(raw, Mapping) else raw
        for family, raw in state.view.signals.signals.items()
    }
    applied: dict[str, dict[str, float]] = {}
    touched: set[str] = set()

    for family, knobs in overrides.items():
        if family not in WHAT_IF_KNOBS:
            raise ValueError(f"unknown what-if family: {family!r}.")
        if family in doc and not isinstance(doc[family], Mapping):
            raise ValueError(f"{family} family is malformed; it cannot be simulated.")
        for field, value in knobs.items():
            if field not in WHAT_IF_KNOBS[family]:
                raise ValueError(f"unknown what-if knob: {family}.{field}.")
            number = _validated_value(family, field, value, WHAT_IF_KNOBS[family][field])
            family_doc: dict[str, Any] = dict(doc.get(family) or {})
            family_doc[field] = number
            family_doc["observed_at"] = moment.isoformat()
            doc[family] = family_doc
            applied.setdefault(family, {})[field] = number
            touched.add(family)

    refreshed_at = state.view.signals.refreshed_at
    if refreshed_at is not None and refreshed_at.tzinfo is None:
        refreshed_at = refreshed_at.replace(tzinfo=UTC)
    signals = normalize_signals(doc, now=moment, refreshed_at=refreshed_at)

    if "rainfall_mm_24h" in applied.get("weather", {}):
        weather = signals.weather
        if (
            weather is not None
            and weather.rainfall_mm is not None
            and (weather.rainfall_mm_per_day is None)
        ):
            raise ValueError(
                "weather.rainfall_mm_24h cannot be simulated: the measurement window is "
                f"unknown for source {weather.source!r}."
            )

    view = state.view.model_copy(
        update={
            "signals": SignalCacheView(
                signals=doc,
                refreshed_at=refreshed_at,
                age_seconds=None
                if refreshed_at is None
                else int((moment - refreshed_at).total_seconds()),
            )
        }
    )
    sorted_applied = {
        family: {field: applied[family][field] for field in sorted(applied[family])}
        for family in sorted(applied)
    }
    return NormalizedFarmState(view=view, signals=signals), sorted_applied, sorted(touched)


def _action_key(action: DecisionAction) -> tuple[str, str, str]:
    return (action.origin, action.code, str(action.plot_id))


def _diff_actions(
    before: Sequence[DecisionAction], after: Sequence[DecisionAction]
) -> tuple[list[DecisionAction], list[DecisionAction]]:
    """Multiset diff keyed by (origin, code, plot_id); order preserved."""
    surplus = Counter(_action_key(action) for action in before)
    added: list[DecisionAction] = []
    for action in after:
        key = _action_key(action)
        if surplus[key] > 0:
            surplus[key] -= 1
        else:
            added.append(action)

    surplus = Counter(_action_key(action) for action in after)
    removed: list[DecisionAction] = []
    for action in before:
        key = _action_key(action)
        if surplus[key] > 0:
            surplus[key] -= 1
        else:
            removed.append(action)
    return added, removed


def _changes(baseline: FarmAnalysis, hypothetical: FarmAnalysis) -> WhatIfChanges:
    """Compare the two decisions field by field (hypothetical minus baseline)."""
    before, after = baseline.decision, hypothetical.decision
    counts_before, counts_after = before.action_counts, after.action_counts
    added, removed = _diff_actions(before.actions, after.actions)
    return WhatIfChanges(
        stance=None if before.stance == after.stance else after.stance,
        health_level=None if before.health_level == after.health_level else after.health_level,
        risk_score_delta=after.risk_score - before.risk_score,
        risk_band=None if before.risk_band == after.risk_band else after.risk_band,
        action_counts_delta={
            key: counts_after.get(key, 0) - counts_before.get(key, 0)
            for key in sorted(set(counts_before) | set(counts_after))
        },
        actions_added=added,
        actions_removed=removed,
    )


def simulate_what_if(
    state: NormalizedFarmState,
    overrides: Mapping[str, Mapping[str, Any]],
    *,
    now: datetime | None = None,
    disease: Sequence[DiseaseAssessment] = (),
) -> WhatIfResult:
    """Re-run the pipeline on ``state`` with ``overrides`` applied.

    Raises ``ValueError`` (caller bug, not an engine rule) for an empty
    override set, an unknown family/knob, a non-numeric or out-of-range
    value, a malformed family, or a rainfall knob whose measurement
    window is unknown.
    """
    if not overrides:
        raise ValueError("no what-if overrides given.")
    moment = now or datetime.now(UTC)

    baseline = run_analysis(state, disease, now=moment)
    hypothetical_state, applied, simulated = _apply_overrides(state, overrides, moment)
    hypothetical = run_analysis(hypothetical_state, disease, now=moment)

    return WhatIfResult(
        baseline=baseline,
        hypothetical=hypothetical,
        changes=_changes(baseline, hypothetical),
        overrides_applied=applied,
        simulated_families=simulated,
    )
