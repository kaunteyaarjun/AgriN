"""Disease assessment engine (M037): context-aware blend.

Peer of ``health``/``risk``/``recommend``: pure rules over data it is
handed (M031 state, M032 health, M036 detection) — no I/O, no clock
beyond the injectable ``now``.

The blend may only **discount** raw model confidence, never inflate
it: the model saw the pixels, farm context can disagree with it but
must not raise a weak score — a boosting blend would let farm state
launder a 0.45 guess into ``detected``. Two multipliers apply in
sequence: crop affinity (M036 catalog) and a healthy-canopy note
(own M032 level). Every discount leaves an evidence string the way
``HealthFactor.detail`` does, so M041 phrases them verbatim.

Verdict from the best candidate: none → ``not_detected``, effective
≥ 0.70 → ``detected``, ≥ 0.50 → ``suspected``, else ``uncertain``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final

from pydantic import BaseModel

from src.engines.health import FarmHealth, crop_label_for
from src.providers.disease import DISEASE_CATALOG, DiseaseCandidate, DiseaseDetection
from src.services.normalize import NormalizedFarmState

DISEASE_VERDICTS: Final[tuple[str, ...]] = (
    "not_detected",
    "uncertain",
    "suspected",
    "detected",
)
DETECTED_MIN: Final[float] = 0.70
"""Effective confidence where model and context jointly warrant acting."""
SUSPECTED_MIN: Final[float] = 0.50
"""Effective confidence worth reporting to a human, not acting alone."""
CROP_MISMATCH_FACTOR: Final[float] = 0.6
HEALTHY_CANOPY_FACTOR: Final[float] = 0.9


class DiseaseCandidateAssessment(BaseModel):
    """One candidate after the blend, with its evidence trail."""

    code: str
    label: str
    raw_confidence: float
    effective_confidence: float
    reasons: list[str]


class DiseaseAssessment(BaseModel):
    """Plot-level verdict for one image's detection run."""

    farm_id: uuid.UUID
    plot_id: uuid.UUID
    plot_name: str
    crop: str | None
    health_level: str
    image_id: uuid.UUID | None
    source: str
    verdict: str
    candidates: list[DiseaseCandidateAssessment]
    detected_at: datetime
    computed_at: datetime


def _blend(
    candidate: DiseaseCandidate,
    crop_key: str,
    crop_name: str,
    health_level: str,
) -> DiseaseCandidateAssessment:
    spec = DISEASE_CATALOG[candidate.code]
    factor = 1.0
    reasons = [f"model confidence {candidate.confidence:.2f}"]
    if not crop_key:
        reasons.append(f"crop not registered - {spec.label} affinity unchecked")
    elif crop_key in spec.crops:
        reasons.append(f"crop match: {crop_name}")
    else:
        factor *= CROP_MISMATCH_FACTOR
        typical = ", ".join(sorted(spec.crops))
        reasons.append(
            f"crop mismatch: {spec.label} typically affects {typical}, "
            f"plot grows {crop_name} (x{CROP_MISMATCH_FACTOR})"
        )
    if health_level == "healthy":
        factor *= HEALTHY_CANOPY_FACTOR
        reasons.append(f"plot canopy reads healthy (x{HEALTHY_CANOPY_FACTOR})")
    effective = round(min(1.0, candidate.confidence * factor), 3)
    reasons.append(f"effective confidence {effective:.3f}")
    return DiseaseCandidateAssessment(
        code=candidate.code,
        label=spec.label,
        raw_confidence=candidate.confidence,
        effective_confidence=effective,
        reasons=reasons,
    )


def _verdict(candidates: list[DiseaseCandidateAssessment]) -> str:
    if not candidates:
        return "not_detected"
    best = candidates[0].effective_confidence
    if best >= DETECTED_MIN:
        return "detected"
    if best >= SUSPECTED_MIN:
        return "suspected"
    return "uncertain"


def assess_disease(
    state: NormalizedFarmState,
    health: FarmHealth,
    detection: DiseaseDetection,
    plot_id: uuid.UUID,
    *,
    image_id: uuid.UUID | None = None,
    now: datetime | None = None,
) -> DiseaseAssessment:
    """Assess one plot's detection against crop affinity and its own
    M032 health level. Raises ``ValueError`` on caller bugs: health for
    another farm, or a plot missing from state or health."""
    moment = now or datetime.now(UTC)
    if health.farm_id != state.view.farm_id:
        raise ValueError(
            f"health is for farm {health.farm_id}, state is for farm {state.view.farm_id}"
        )
    plot = next((item for item in state.view.plots if item.plot_id == plot_id), None)
    if plot is None:
        raise ValueError(f"plot {plot_id} is not part of farm {state.view.farm_id}")
    plot_health = next((item for item in health.plots if item.plot_id == plot_id), None)
    if plot_health is None:
        raise ValueError(f"plot {plot_id} is missing from health for farm {health.farm_id}")

    crop_key = (plot.crop or "").strip().lower()
    crop_name = crop_label_for(plot.crop)
    candidates = sorted(
        (
            _blend(candidate, crop_key, crop_name, plot_health.level)
            for candidate in detection.detections
        ),
        key=lambda item: (-item.effective_confidence, item.code),
    )
    return DiseaseAssessment(
        farm_id=state.view.farm_id,
        plot_id=plot.plot_id,
        plot_name=plot.name,
        crop=plot.crop,
        health_level=plot_health.level,
        image_id=image_id,
        source=detection.source,
        verdict=_verdict(candidates),
        candidates=candidates,
        detected_at=detection.detected_at,
        computed_at=moment,
    )


__all__ = [
    "CROP_MISMATCH_FACTOR",
    "DETECTED_MIN",
    "DISEASE_VERDICTS",
    "HEALTHY_CANOPY_FACTOR",
    "SUSPECTED_MIN",
    "DiseaseAssessment",
    "DiseaseCandidateAssessment",
    "assess_disease",
]
