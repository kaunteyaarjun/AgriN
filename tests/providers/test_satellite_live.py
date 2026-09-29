"""Satellite live provider tests (M027): the two-request protocol, QA
filtering of the MODIS window, failure taxonomy, client lifecycle and
settings-driven resolution.

Pure unit — every response comes from ``httpx.MockTransport`` (dispatching
on ``/dates`` vs ``/subset``); no test in this file touches the network
(the real call happens only in the manual live check recorded in the
milestone notes).

Dates are built relative to *today* so the suite never rots: the provider
picks the newest composite whose ``calendar_date <= today``.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from src.providers import (
    DemoSatelliteProvider,
    LiveSatelliteProvider,
    ProviderResponseInvalid,
    ProviderUnavailable,
    SatelliteProvider,
    get_provider,
    get_satellite_provider,
)
from src.providers.satellite_live import (
    NDVI_BAND,
    PRODUCT,
    RELIABILITY_BAND,
    SOURCE_NAME,
    TIMEOUT_S,
)

NAIROBI = (-1.2921, 36.8219)

TODAY = datetime.now(UTC).date()
PAST_DAY = TODAY - timedelta(days=40)
LATEST_DAY = TODAY - timedelta(days=8)
FUTURE_DAY = TODAY + timedelta(days=16)


def _modis_id(day: date) -> str:
    return f"A{day.year}{day.timetuple().tm_yday:03d}"


def _dates_payload(*days: date) -> dict[str, object]:
    return {"dates": [{"modis_date": _modis_id(d), "calendar_date": d.isoformat()} for d in days]}


def _subset_payload(
    ndvi: object | None,
    qa: object | None,
    *,
    modis_date: str | None = None,
    bands: tuple[str, ...] = (NDVI_BAND, RELIABILITY_BAND),
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for band in bands:
        data = ndvi if band == NDVI_BAND else qa
        entries.append(
            {"band": band, "modis_date": modis_date or _modis_id(LATEST_DAY), "data": data}
        )
    return {"subset": entries, "ncols": 3, "nrows": 3}


Handler = Callable[[httpx.Request], httpx.Response]


def provider_for(
    handler: Handler,
    *,
    base_url: str = "https://modis.ornl.gov/rst/api/v1",
) -> LiveSatelliteProvider:
    """Provider wired to an offline MockTransport."""
    return LiveSatelliteProvider(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        base_url=base_url,
    )


def api_handler(
    *,
    dates: object = None,
    subset: object = None,
    subset_status: int = 200,
    subset_text: str | None = None,
    dates_status: int = 200,
    dates_body: bytes | None = None,
    captured: list[httpx.Request] | None = None,
) -> Handler:
    dates_payload = _dates_payload(PAST_DAY, LATEST_DAY) if dates is None else dates
    subset_payload = _subset_payload([5000, 6000, 4000], [0, 1, 3]) if subset is None else subset

    def handler(request: httpx.Request) -> httpx.Response:
        if captured is not None:
            captured.append(request)
        path = request.url.path
        if path.endswith("/dates"):
            if dates_body is not None:
                return httpx.Response(
                    dates_status, content=dates_body, headers={"content-type": "application/json"}
                )
            return httpx.Response(dates_status, json=dates_payload)
        if path.endswith("/subset"):
            if subset_text is not None:
                return httpx.Response(subset_status, text=subset_text)
            return httpx.Response(subset_status, json=subset_payload)
        return httpx.Response(404, text="unexpected path")

    return handler


# ---------- registration / settings resolution ----------


async def test_live_registered_and_default_still_demo() -> None:
    from src.providers.registry import default_registry

    try:
        provider = get_provider("satellite", mode="live")
        assert isinstance(provider, LiveSatelliteProvider)
        assert isinstance(provider, SatelliteProvider)
        assert provider.family == "satellite"
        assert provider.mode == "live"
        assert provider.name == SOURCE_NAME
        assert get_satellite_provider(mode="live") is provider  # registry caches one instance

        default = get_provider("satellite")  # settings default: demo
        assert isinstance(default, DemoSatelliteProvider)
        assert get_satellite_provider().mode == "demo"
    finally:
        await default_registry.aclose_all()  # release the registry-built client


# ---------- two-request protocol ----------


async def test_protocol_is_dates_then_single_date_subset() -> None:
    captured: list[httpx.Request] = []
    reading = await provider_for(api_handler(captured=captured)).fetch(*NAIROBI)

    assert len(captured) == 2
    first, second = captured
    assert first.url.path.endswith(f"/{PRODUCT}/dates")
    assert second.url.path.endswith(f"/{PRODUCT}/subset")

    assert float(first.url.params["latitude"]) == NAIROBI[0]
    assert float(first.url.params["longitude"]) == NAIROBI[1]

    params = second.url.params
    assert params["startDate"] == params["endDate"] == _modis_id(LATEST_DAY)
    assert params["kmAboveBelow"] == "1"
    assert params["kmLeftRight"] == "1"
    assert float(params["latitude"]) == NAIROBI[0]
    assert float(params["longitude"]) == NAIROBI[1]
    assert "api_key" not in params and "appid" not in params  # keyless upstream

    assert reading.captured_at == datetime.combine(LATEST_DAY, datetime.min.time(), tzinfo=UTC)


async def test_future_composites_are_ignored() -> None:
    captured: list[httpx.Request] = []
    dates = _dates_payload(PAST_DAY, LATEST_DAY, FUTURE_DAY)
    await provider_for(api_handler(dates=dates, captured=captured)).fetch(*NAIROBI)

    subset_params = captured[1].url.params
    assert subset_params["startDate"] == _modis_id(LATEST_DAY)
    assert _modis_id(FUTURE_DAY) not in (subset_params["startDate"], subset_params["endDate"])


async def test_takes_the_newest_past_composite() -> None:
    captured: list[httpx.Request] = []
    dates = _dates_payload(PAST_DAY, LATEST_DAY)
    await provider_for(api_handler(dates=dates, captured=captured)).fetch(*NAIROBI)

    assert captured[1].url.params["startDate"] == _modis_id(LATEST_DAY)


# ---------- field mapping + QA filtering ----------


async def test_full_payload_maps_to_reading() -> None:
    # 5000 (good) + 6000 (marginal) are usable; 4000 is flagged cloudy → excluded
    subset = _subset_payload([5000, 6000, 4000], [0, 1, 3])
    reading = await provider_for(api_handler(subset=subset)).fetch(*NAIROBI)

    assert reading.ndvi == 0.55  # mean(0.5, 0.6)
    assert reading.cloud_cover_pct == 33.3  # 1 of 3 pixels cloudy
    assert reading.source == SOURCE_NAME
    assert reading.captured_at is not None
    assert reading.captured_at.tzinfo is not None
    now = datetime.now(UTC)
    assert reading.fetched_at.tzinfo is not None
    assert abs((now - reading.fetched_at).total_seconds()) < 60


async def test_scale_factor_and_rounding() -> None:
    subset = _subset_payload([3751, 3749], [0, 0])
    reading = await provider_for(api_handler(subset=subset)).fetch(*NAIROBI)
    assert reading.ndvi == 0.375  # mean(0.3751, 0.3749) -> 4 dp


@pytest.mark.parametrize(
    ("ndvi", "qa", "expected"),
    [
        # fill (-3000) and out-of-range (12000) raw values dropped
        ([5000, -3000, 12000], [0, 0, 0], 0.5),
        # snow / cloudy / failed pixels are not data → nothing usable
        ([5000, 4000, 6000], [2, 3, 4], None),
        # marginal (1) is usable, fill flag (-1) is not
        ([10000, -2000], [1, -1], 1.0),
        ([5000, 5000], [0, 2], 0.5),
    ],
)
async def test_qa_filtering_excludes_unusable_pixels(
    ndvi: object, qa: object, expected: float | None
) -> None:
    subset = _subset_payload(ndvi, qa)
    reading = await provider_for(api_handler(subset=subset)).fetch(*NAIROBI)
    assert reading.ndvi == expected


async def test_non_numeric_ndvi_is_ignored() -> None:
    subset = _subset_payload(["5000", 6000, None, True], [0, 0, 0, 0])
    reading = await provider_for(api_handler(subset=subset)).fetch(*NAIROBI)
    assert reading.ndvi == 0.6  # only the numeric 6000 survives


async def test_no_usable_pixel_yields_none_ndvi_but_still_cloud_cover() -> None:
    subset = _subset_payload([4000, 4000, 4000], [3, 3, 4])
    reading = await provider_for(api_handler(subset=subset)).fetch(*NAIROBI)
    assert reading.ndvi is None
    assert reading.cloud_cover_pct == 66.7  # 2 of 3 cloudy, 1 dp
    assert reading.captured_at is not None  # still a valid reading


async def test_cloud_cover_is_a_share_of_the_window() -> None:
    subset = _subset_payload([5000] * 81, [3] * 54 + [0] * 27)
    reading = await provider_for(api_handler(subset=subset)).fetch(*NAIROBI)
    assert reading.cloud_cover_pct == 66.7


# ---------- failure taxonomy (M021 contract) ----------


@pytest.mark.parametrize("status", [429, 500, 502, 503])
async def test_server_and_rate_limit_errors_are_unavailable(status: int) -> None:
    handler = api_handler(dates_status=status, dates_body=b"upstream boom")
    with pytest.raises(ProviderUnavailable, match=f"HTTP {status}"):
        await provider_for(handler).fetch(*NAIROBI)


async def test_subset_5xx_is_unavailable() -> None:
    handler = api_handler(subset_status=503)
    with pytest.raises(ProviderUnavailable, match="HTTP 503"):
        await provider_for(handler).fetch(*NAIROBI)


async def test_upstream_400_is_response_invalid_with_trimmed_detail() -> None:
    """The upstream answers 400 in plain text when a period has no data."""
    handler = api_handler(
        subset_status=400,
        subset_text="No data available for time period A2026225 to A2026225 for MOD13Q1 "
        "-1.2921 36.8219 combination.",
    )
    with pytest.raises(ProviderResponseInvalid, match="HTTP 400") as exc:
        await provider_for(handler).fetch(*NAIROBI)
    message = str(exc.value)
    assert "No data available" in message  # actionable upstream text is kept
    assert len(message) < 300  # but trimmed — never a raw payload dump


async def test_timeout_and_transport_errors_are_unavailable() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    with pytest.raises(ProviderUnavailable, match="timeout"):
        await provider_for(timeout).fetch(*NAIROBI)

    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(ProviderUnavailable, match="unreachable"):
        await provider_for(refused).fetch(*NAIROBI)


async def test_unparseable_body_is_response_invalid() -> None:
    handler = api_handler(dates_body=b"<html>nope</html>")
    with pytest.raises(ProviderResponseInvalid, match="unparseable"):
        await provider_for(handler).fetch(*NAIROBI)


async def test_non_object_dates_body_is_response_invalid() -> None:
    handler = api_handler(dates_body=b'["not", "an", "object"]')
    with pytest.raises(ProviderResponseInvalid):
        await provider_for(handler).fetch(*NAIROBI)


@pytest.mark.parametrize(
    "dates",
    [
        {"dates": []},
        {"dates": "nope"},
        {"payload": []},
        {"dates": [{"modis_date": "A2026225"}]},  # no calendar_date → nothing usable
        {"dates": [{"calendar_date": "2026-08-13"}]},  # no modis_date → nothing usable
        {"dates": [{"modis_date": "A2026225", "calendar_date": "13/08/2026"}]},  # unparseable
        {"dates": [{"modis_date": "A2026225", "calendar_date": FUTURE_DAY.isoformat()}]},
    ],
)
async def test_calendar_problems_are_response_invalid(dates: object) -> None:
    handler = api_handler(dates=dates)
    with pytest.raises(ProviderResponseInvalid):
        await provider_for(handler).fetch(*NAIROBI)


@pytest.mark.parametrize(
    "subset",
    [
        {"subset": []},  # ocean / no coverage
        {"subset": "nope"},
        {"subset": [{"band": "250m_16_days_EVI", "data": [1]}]},  # NDVI band missing
        _subset_payload(None, None, bands=(NDVI_BAND,)),  # quality band missing
        _subset_payload("not-a-list", [0, 1]),
        _subset_payload([], []),
        _subset_payload([1, 2, 3], [0, 1]),  # length mismatch
        {"subset": [{"band": NDVI_BAND, "data": [5000]}]},  # quality data missing
    ],
)
async def test_subset_shape_problems_are_response_invalid(subset: object) -> None:
    handler = api_handler(subset=subset)
    with pytest.raises(ProviderResponseInvalid):
        await provider_for(handler).fetch(*NAIROBI)


async def test_no_raw_exception_escapes_the_contract() -> None:
    with pytest.raises(ProviderUnavailable):
        await provider_for(api_handler(dates_status=503)).fetch(*NAIROBI)
    with pytest.raises(ProviderResponseInvalid):
        await provider_for(api_handler(subset={"subset": []})).fetch(*NAIROBI)
    with pytest.raises(ProviderUnavailable):

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=request)

        await provider_for(handler).fetch(*NAIROBI)


# ---------- client lifecycle ----------


async def test_aclose_closes_owned_client() -> None:
    provider = LiveSatelliteProvider()
    client = provider._client
    assert client.timeout.read == TIMEOUT_S
    assert not client.is_closed

    await provider.aclose()

    assert client.is_closed
    await provider.aclose()  # idempotent


async def test_aclose_closes_injected_client_too() -> None:
    provider = provider_for(api_handler())
    await provider.fetch(*NAIROBI)
    await provider.aclose()
    assert provider._client.is_closed
