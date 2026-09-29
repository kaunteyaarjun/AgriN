"""Disease provider tests (M036): registration through the normal
M021 path, payload determinism, documented candidate/confidence ranges
over a fixed sweep (including the no-findings path), contract
validation against ``DISEASE_CATALOG``, the caller guard, and catalog
sanity.

Pure unit - the demo provider has no I/O by design.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.engines.health import CROP_PROFILES
from src.providers import (
    DISEASE_CATALOG,
    DemoDiseaseProvider,
    DiseaseCandidate,
    DiseaseDetection,
    DiseaseProvider,
    ProviderNotRegistered,
    get_disease_provider,
    get_provider,
)
from src.providers.disease_demo import (
    CONFIDENCE_MAX,
    CONFIDENCE_MIN,
    DEMO_NAME,
    image_seed,
)

PHOTO_A = b"alpha photo payload \x89PNG fake bytes 0001"
PHOTO_B = b"beta photo payload \xff\xd8\xde fake bytes 0002"
SWEEP: list[bytes] = [f"disease-sweep-image-{i:03d}".encode() for i in range(60)]


def test_registered_through_normal_settings_path() -> None:
    provider = get_provider("disease")  # settings default: demo
    assert isinstance(provider, DemoDiseaseProvider)
    typed = get_disease_provider()
    assert isinstance(typed, DiseaseProvider)
    assert typed.family == "disease"
    assert typed.mode == "demo"
    assert typed.name == DEMO_NAME
    assert provider is typed  # registry caches the same instance


def test_live_mode_not_registered_yet() -> None:
    with pytest.raises(ProviderNotRegistered, match="disease.*live"):
        get_disease_provider(mode="live")


async def test_same_image_is_deterministic() -> None:
    provider = DemoDiseaseProvider()
    first = await provider.detect(PHOTO_A)
    second = await provider.detect(PHOTO_A)
    assert isinstance(first, DiseaseDetection)
    assert first.source == DEMO_NAME
    assert first.model_dump(exclude={"detected_at"}) == second.model_dump(exclude={"detected_at"})


async def test_different_images_differ() -> None:
    provider = DemoDiseaseProvider()
    a = await provider.detect(PHOTO_A)
    b = await provider.detect(PHOTO_B)
    assert a.model_dump(exclude={"detected_at", "source"}) != b.model_dump(
        exclude={"detected_at", "source"}
    )


def test_image_seed_is_stable_and_payload_sensitive() -> None:
    assert image_seed(PHOTO_A) == image_seed(PHOTO_A)
    assert image_seed(PHOTO_A) != image_seed(PHOTO_B)


async def test_sweep_obeys_documented_ranges() -> None:
    """Confidence 0.30-0.95, 0-2 candidates, catalog codes only, no
    duplicates, and both the empty and non-empty paths occur."""
    provider = DemoDiseaseProvider()
    empty_seen = False
    nonempty_seen = False
    for image in SWEEP:
        result = await provider.detect(image)
        assert result.source == DEMO_NAME
        detections = result.detections
        assert 0 <= len(detections) <= 2
        if not detections:
            empty_seen = True
            continue
        nonempty_seen = True
        codes = [candidate.code for candidate in detections]
        assert len(codes) == len(set(codes))  # no duplicate codes
        for candidate in detections:
            assert candidate.code in DISEASE_CATALOG
            assert CONFIDENCE_MIN <= candidate.confidence <= CONFIDENCE_MAX
    assert empty_seen, "sweep must exercise the no-findings path"
    assert nonempty_seen, "sweep must exercise the detection path"


def test_unknown_code_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown disease code"):
        DiseaseCandidate(code="martian_rot", confidence=0.5)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_confidence_bounds_enforced(confidence: float) -> None:
    with pytest.raises(ValidationError):
        DiseaseCandidate(code="rust", confidence=confidence)


def test_every_catalog_code_constructs() -> None:
    for code in DISEASE_CATALOG:
        candidate = DiseaseCandidate(code=code, confidence=0.5)
        assert candidate.code == code


async def test_empty_payload_is_caller_bug() -> None:
    provider = DemoDiseaseProvider()
    with pytest.raises(ValueError, match="empty image payload"):
        await provider.detect(b"")


def test_catalog_crops_are_known_profiles() -> None:
    known = set(CROP_PROFILES)
    for code, spec in DISEASE_CATALOG.items():
        assert spec.label.strip(), f"{code}: empty label"
        assert spec.crops, f"{code}: no crops"
        assert spec.crops <= known, f"{code}: crops outside CROP_PROFILES"
