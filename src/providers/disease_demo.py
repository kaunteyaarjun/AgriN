"""Disease demo provider (M036): deterministic, network-free diagnoses.

Registered on the default registry under ``("disease", "demo")``, so the
default ``disease_provider = "demo"`` flag resolves to it through the
normal M021 path. Results derive from the sha256 of the image bytes
(``image_seed``) - the same photo always yields the same diagnosis,
which is what makes the demo and its tests stable.

Documented behavior (tested):
- 0-2 candidates; no duplicate codes within one result;
- ``seed % 5 == 0`` (20 % of inputs) yields no findings at all;
- confidence within 0.30-0.95 (1 decimal-step thousandths, rounded);
- codes only from ``DISEASE_CATALOG``.

A live model (M038) registers under ``("disease", "live")`` behind the
same ABC.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from src.providers.disease import (
    DISEASE_CATALOG,
    DiseaseCandidate,
    DiseaseDetection,
    DiseaseProvider,
)
from src.providers.registry import register

DEMO_NAME = "demo-disease-v1"

CONFIDENCE_MIN = 0.30
CONFIDENCE_MAX = 0.95


def image_seed(image: bytes) -> int:
    """Stable 64-bit seed per payload (full sha256, 16 hex chars)."""
    return int(hashlib.sha256(image).hexdigest()[:16], 16)


@register
class DemoDiseaseProvider(DiseaseProvider):
    """Synthetic detection over opaque image bytes. No I/O, no vision
    by design - it reports seeded candidates, not real morphology."""

    mode = "demo"
    name = DEMO_NAME

    async def detect(self, image: bytes) -> DiseaseDetection:
        if not image:
            raise ValueError("empty image payload")
        seed = image_seed(image)
        detections: list[DiseaseCandidate] = []
        if seed % 5 != 0:
            codes = list(DISEASE_CATALOG)
            count = 1 + ((seed >> 8) % 2)
            used: set[str] = set()
            for position in range(count):
                index = (seed >> (16 + 16 * position)) % len(codes)
                while codes[index] in used:
                    index = (index + 1) % len(codes)
                used.add(codes[index])
                confidence = round(CONFIDENCE_MIN + ((seed >> (32 + 8 * position)) % 651) / 1000, 3)
                detections.append(DiseaseCandidate(code=codes[index], confidence=confidence))
        return DiseaseDetection(
            source=self.name,
            detected_at=datetime.now(UTC),
            detections=detections,
        )
