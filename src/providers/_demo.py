"""Shared helpers for the deterministic demo providers (M028).

Rule of three: ``point_seed``/``check_wgs84`` existed verbatim in
``weather_demo`` (M022) and ``satellite_demo`` (M025); the soil demo
would have been the third copy, so both extract here. Behavior is
unchanged — same sha256 scheme (4-decimal coordinate precision, ≈ 11 m)
and the same WGS84 ``ValueError`` message.
"""

from __future__ import annotations

import hashlib


def point_seed(lat: float, lon: float) -> int:
    """Stable 64-bit seed per point (4-decimal ≈ 11 m precision)."""
    digest = hashlib.sha256(f"{lat:.4f},{lon:.4f}".encode()).hexdigest()
    return int(digest[:16], 16)


def check_wgs84(lat: float, lon: float) -> None:
    """Caller-bug guard: out-of-bounds coordinates raise ``ValueError``
    (not a ``ProviderError`` — the upstream was never contacted)."""
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError(f"coordinates out of WGS84 bounds: lat={lat}, lon={lon}")
