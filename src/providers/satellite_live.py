"""Satellite live provider (M027): NASA MODIS NDVI via ORNL DAAC.

Second network-backed provider — the first one that needs a
**two-request protocol**, which is exactly why this milestone exists:

1. ``GET /MOD13Q1/dates`` → the composite calendar (``{modis_date,
   calendar_date}`` entries; the list is the *global* MODIS calendar,
   so it cannot by itself prove data exists for a point) — cached
   process-wide for ``CALENDAR_TTL_S`` since M056: one call per batch,
   not per farm;
2. ``GET /MOD13Q1/subset`` for the newest ``calendar_date <= today``
   and a 9x9 pixel window around the point (``kmAboveBelow=1``,
   ``kmLeftRight=1``, 231.66 m cell).

Keyless (no account, no API key) — chosen deliberately over the
Sentinel-2 / Copernicus / Earth Engine routes, which all need
credentials this platform does not have (see M027's spec).

Mapping (spec: M027):

- ``ndvi`` = mean of the **QA-valid** window pixels
  (``pixel_reliability`` 0 good / 1 marginal, raw value within
  ``[-2000, 10000]``) x ``0.0001`` (MOD13Q1 scale factor), 4 dp.
  Snow/ice (2), cloudy (3), failed (4) and fill (-1) are excluded
  because the product's own QA says they are not data — QA handling,
  not a masking *policy* (M031 owns policy). No usable pixel →
  ``ndvi=None``.
- ``cloud_cover_pct`` = ``100 * count(pixel_reliability == 3) / 81``,
  1 dp — a documented approximation (MOD13Q1 ships no cloud-cover
  band); raw for M031.
- ``captured_at`` = the composite day at 00:00 UTC; ``fetched_at`` =
  now (UTC).

Failure taxonomy (M021): timeouts/transport/5xx/429 →
``ProviderUnavailable``; any other non-2xx (the upstream answers 400
in plain text when a period has no data), an empty ``subset`` (ocean /
no coverage) or a malformed body → ``ProviderResponseInvalid``. No raw
exception escapes.

Client ownership mirrors M024: one pooled ``httpx.AsyncClient``
(20 s timeout — measured ``dates`` ~2.5-4.5 s, single-date ``subset``
~3 s) unless injected; ``aclose()`` closes it.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, time
from statistics import fmean
from time import monotonic
from typing import Any

import httpx

from src.providers.errors import ProviderResponseInvalid, ProviderUnavailable
from src.providers.registry import register
from src.providers.satellite import SatelliteProvider, SatelliteReading

logger = logging.getLogger("agrin.providers.satellite_live")

BASE_URL = "https://modis.ornl.gov/rst/api/v1"
PRODUCT = "MOD13Q1"
SOURCE_NAME = "ornl-daac-modis-mod13q1"

TIMEOUT_S = 20.0
CALENDAR_TTL_S = 12 * 3600.0
"""Freshness window for the cached ``/dates`` calendar (M056): a new
composite lands every 16 days, so half a day of staleness is free —
while ``day > today`` filtering keeps the chosen composite honest."""
NDVI_BAND = "250m_16_days_NDVI"
RELIABILITY_BAND = "250m_16_days_pixel_reliability"
KM_ABOVE_BELOW = 1
KM_LEFT_RIGHT = 1
NDVI_SCALE = 0.0001
RAW_MIN, RAW_MAX = -2000, 10000  # MOD13Q1 VI valid range (scaled)
QA_USABLE = frozenset({0, 1})  # 0 good, 1 marginal
QA_CLOUDY = 3
UPSTREAM_MESSAGE_MAX = 200

_calendar: tuple[float, list[dict[str, Any]]] | None = None
"""(fetched-at monotonic, raw ``dates`` entries) — process-wide (M056)."""

_calendar_lock = asyncio.Lock()
"""Collapses concurrent first fetches into one upstream ``/dates`` call."""


def reset_calendar_cache() -> None:
    """Drop the cached calendar and recreate the lock (M056).

    Tests call this per case via ``tests/conftest.py``; recreating the
    lock also keeps per-test event loops from inheriting a loop-bound
    primitive.
    """
    global _calendar, _calendar_lock
    _calendar = None
    _calendar_lock = asyncio.Lock()


@register
class LiveSatelliteProvider(SatelliteProvider):
    """MODIS/Terra 16-day NDVI for any WGS84 point (ORNL DAAC subset service)."""

    mode = "live"
    name = SOURCE_NAME

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        base_url: str = BASE_URL,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client if client is not None else httpx.AsyncClient(timeout=TIMEOUT_S)

    async def fetch(self, lat: float, lon: float) -> SatelliteReading:
        composite = await self._latest_composite(lat, lon)
        subset = await self._fetch_subset(lat, lon, composite["modis_date"])
        pairs = _qa_pairs(subset)
        return SatelliteReading(
            fetched_at=datetime.now(UTC),
            source=self.name,
            ndvi=_mean_ndvi(pairs),
            cloud_cover_pct=_cloud_cover_pct(pairs),
            captured_at=datetime.combine(composite["calendar_date"], time.min, tzinfo=UTC),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # ---------- upstream protocol ----------

    async def _latest_composite(self, lat: float, lon: float) -> dict[str, Any]:
        """Newest composite on or before today (the calendar is global)."""
        dates = await self._calendar_dates(lat, lon)

        today = datetime.now(UTC).date()
        best: dict[str, Any] | None = None
        for entry in dates:
            if not isinstance(entry, dict):
                continue
            modis_date = entry.get("modis_date")
            calendar_date = entry.get("calendar_date")
            if not isinstance(modis_date, str) or not isinstance(calendar_date, str):
                continue
            try:
                day = date.fromisoformat(calendar_date)
            except ValueError as exc:
                raise ProviderResponseInvalid(
                    "modis returned an unparseable calendar_date"
                ) from exc
            if day > today:
                continue
            if best is None or day > best["calendar_date"]:
                best = {"modis_date": modis_date, "calendar_date": day}
        if best is None:
            raise ProviderResponseInvalid("modis has no composite dated on or before today")
        return best

    async def _calendar_dates(self, lat: float, lon: float) -> list[dict[str, Any]]:
        """The global ``/dates`` calendar, fetched at most once per TTL.

        M056: ``/dates`` ignores the point (M027 measured the same
        calendar for a mid-ocean location), so one process-wide entry
        serves every farm — an N-farm batch costs one ``dates`` + N
        ``subset`` calls instead of 2N. A double-checked lock collapses
        a batch's concurrent first fetches into one upstream call;
        failures and invalid bodies are never cached (they raise before
        the store is written).
        """
        global _calendar
        if _calendar is not None and monotonic() - _calendar[0] < CALENDAR_TTL_S:
            return _calendar[1]
        async with _calendar_lock:
            if _calendar is not None and monotonic() - _calendar[0] < CALENDAR_TTL_S:
                return _calendar[1]  # another fetcher won the lock
            payload = await self._get_json("dates", {"latitude": lat, "longitude": lon})
            dates = payload.get("dates")
            if not isinstance(dates, list) or not dates:
                raise ProviderResponseInvalid("modis response missing a usable 'dates' list")
            _calendar = (monotonic(), dates)
            return dates

    async def _fetch_subset(self, lat: float, lon: float, modis_date: str) -> list[dict[str, Any]]:
        payload = await self._get_json(
            "subset",
            {
                "latitude": lat,
                "longitude": lon,
                "startDate": modis_date,
                "endDate": modis_date,
                "kmAboveBelow": KM_ABOVE_BELOW,
                "kmLeftRight": KM_LEFT_RIGHT,
            },
        )
        subset = payload.get("subset")
        if not isinstance(subset, list) or not subset:
            raise ProviderResponseInvalid("modis returned no subset data for this location")
        return subset

    async def _get_json(self, path: str, params: Mapping[str, str | float]) -> dict[str, Any]:
        url = f"{self._base_url}/{PRODUCT}/{path}"
        try:
            response = await self._client.get(url, params=dict(params))
        except httpx.TimeoutException as exc:
            logger.warning("modis timeout on %s: %s", path, exc)
            raise ProviderUnavailable(f"modis timeout on {path}: {exc}") from exc
        except httpx.TransportError as exc:
            logger.warning("modis transport error on %s: %s", path, exc)
            raise ProviderUnavailable(f"modis unreachable on {path}: {exc}") from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise ProviderUnavailable(f"modis HTTP {response.status_code} on {path}")
        if response.status_code != 200:
            detail = _safe_detail(response)
            raise ProviderResponseInvalid(f"modis HTTP {response.status_code} on {path}{detail}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseInvalid(f"modis returned an unparseable body on {path}") from exc
        if not isinstance(payload, dict):
            raise ProviderResponseInvalid(f"modis returned a non-object body on {path}")
        return payload


def _safe_detail(response: httpx.Response) -> str:
    """Plain-text upstream error, trimmed — never a raw payload dump."""
    text = response.text.strip().replace("\n", " ")
    if not text:
        return ""
    return f": {text[:UPSTREAM_MESSAGE_MAX]}"


def _band_data(subset: Sequence[object], band: str) -> list[Any]:
    entries = [entry for entry in subset if isinstance(entry, dict) and entry.get("band") == band]
    if not entries:
        raise ProviderResponseInvalid(f"modis response missing the {band} band")
    data = entries[-1].get("data")
    if not isinstance(data, list):
        raise ProviderResponseInvalid(f"modis band {band} has no data list")
    return data


def _qa_pairs(subset: Sequence[object]) -> list[tuple[Any, Any]]:
    """(NDVI raw value, pixel reliability) pairs for the single subset date."""
    ndvi_data = _band_data(subset, NDVI_BAND)
    qa_data = _band_data(subset, RELIABILITY_BAND)
    if not ndvi_data or len(ndvi_data) != len(qa_data):
        raise ProviderResponseInvalid("modis NDVI/quality bands are missing or inconsistent")
    return list(zip(ndvi_data, qa_data, strict=True))


def _is_raw_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _mean_ndvi(pairs: Sequence[tuple[Any, Any]]) -> float | None:
    """QA-valid mean x scale factor; ``None`` when no pixel is usable."""
    usable = [
        float(raw)
        for raw, quality in pairs
        if quality in QA_USABLE and _is_raw_number(raw) and RAW_MIN <= raw <= RAW_MAX
    ]
    if not usable:
        return None
    return round(fmean(usable) * NDVI_SCALE, 4)


def _cloud_cover_pct(pairs: Sequence[tuple[Any, Any]]) -> float:
    """Share of the window QA-flagged as cloudy (documented approximation)."""
    cloudy = sum(1 for _, quality in pairs if quality == QA_CLOUDY)
    return round(100 * cloudy / len(pairs), 1)
