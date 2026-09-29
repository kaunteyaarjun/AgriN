"""Disease family interface - follows the soil/weather pattern (M036).

Defines the typed contract every disease source must satisfy:
``DiseaseDetection`` / ``DiseaseCandidate`` (validated at the boundary),
the crop-linked ``DISEASE_CATALOG`` vocabulary, the abstract
``DiseaseProvider.detect`` and the typed ``get_disease_provider``
accessor. The demo implementation registers under ``("disease",
"demo")``; the live model (M038) registers under ``("disease",
"live")``. M037's assessment consumes the result and the catalog - this
module is the single source of truth for both.

Input is opaque image bytes (M035 stores what the provider receives);
the family never inspects or transforms pixels. An empty detections
list means "no findings" - the healthy wording belongs to M037.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from pydantic import BaseModel, Field, field_validator

from src.core.config import ProviderMode
from src.providers.base import BaseProvider
from src.providers.errors import ProviderError
from src.providers.registry import get_provider


@dataclass(frozen=True)
class DiseaseSpec:
    """One vocabulary entry: display label plus the crops it plausibly
    affects. M037 down-weights a candidate whose crops exclude the
    plot's crop; unknown crops get no such discount."""

    label: str
    crops: frozenset[str]


DISEASE_CATALOG: Final[dict[str, DiseaseSpec]] = {
    "gray_leaf_spot": DiseaseSpec("Gray leaf spot", frozenset({"maize"})),
    "leaf_blight": DiseaseSpec("Leaf blight", frozenset({"maize", "wheat"})),
    "rust": DiseaseSpec("Rust", frozenset({"wheat", "beans"})),
    "powdery_mildew": DiseaseSpec("Powdery mildew", frozenset({"wheat", "beans"})),
    "anthracnose": DiseaseSpec("Anthracnose", frozenset({"beans"})),
    "fusarium_wilt": DiseaseSpec("Fusarium wilt", frozenset({"maize", "beans"})),
}
"""Fixed demo vocabulary (6 codes). Codes are validated against this
mapping at model construction - one source of truth for provider,
assessment and frontend alike."""


class DiseaseCandidate(BaseModel):
    """One suspected finding. ``confidence`` is probability-shaped
    [0, 1]; the demo documents 0.30-0.95 (it never claims certainty)."""

    code: str = Field(min_length=1, max_length=40)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("code")
    @classmethod
    def _code_in_catalog(cls, value: str) -> str:
        if value not in DISEASE_CATALOG:
            raise ValueError(f"unknown disease code: {value!r}")
        return value


class DiseaseDetection(BaseModel):
    """Result of one detection run over one image."""

    source: str
    detected_at: datetime
    detections: list[DiseaseCandidate] = Field(default_factory=list)


class DiseaseProvider(BaseProvider):
    """Abstract disease source: run detection over one image."""

    family = "disease"

    @abstractmethod
    async def detect(self, image: bytes) -> DiseaseDetection:
        """Return a validated detection result. Raise
        ``ProviderUnavailable`` / ``ProviderResponseInvalid`` on failure
        (never raw upstream exceptions - mapping is the
        implementation's job)."""


def get_disease_provider(*, mode: ProviderMode | None = None) -> DiseaseProvider:
    """Typed accessor - same lookup as ``get_provider``, no casts for
    callers."""
    provider = get_provider("disease", mode=mode)
    if not isinstance(provider, DiseaseProvider):
        raise ProviderError(
            f"Registered disease provider {provider!r} does not implement DiseaseProvider."
        )
    return provider
