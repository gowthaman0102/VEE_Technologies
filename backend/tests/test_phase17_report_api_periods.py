from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.v1 import reports
from app.api.v1.reports import _resolve_period
from app.schemas.reports import ReportRequest


def test_daily_api_period_uses_previous_completed_day() -> None:
    payload = ReportRequest(
        company_id=2,
        report_type="daily",
        end_date=datetime(
            2026,
            9,
            17,
            14,
            30,
            tzinfo=timezone.utc,
        ),
    )

    start, end = _resolve_period(payload)

    assert start == datetime(
        2026,
        9,
        16,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        17,
        tzinfo=timezone.utc,
    )


def test_weekly_api_period_uses_previous_completed_week() -> None:
    payload = ReportRequest(
        company_id=2,
        report_type="weekly",
        end_date=datetime(
            2026,
            9,
            17,
            14,
            30,
            tzinfo=timezone.utc,
        ),
    )

    start, end = _resolve_period(payload)

    assert start == datetime(
        2026,
        9,
        7,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        14,
        tzinfo=timezone.utc,
    )


def test_monthly_api_period_uses_previous_calendar_month() -> None:
    payload = ReportRequest(
        company_id=2,
        report_type="monthly",
        end_date=datetime(
            2026,
            9,
            17,
            14,
            30,
            tzinfo=timezone.utc,
        ),
    )

    start, end = _resolve_period(payload)

    assert start == datetime(
        2026,
        8,
        1,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )


def test_monthly_api_period_handles_year_boundary() -> None:
    payload = ReportRequest(
        company_id=2,
        report_type="monthly",
        end_date=datetime(
            2026,
            1,
            20,
            tzinfo=timezone.utc,
        ),
    )

    start, end = _resolve_period(payload)

    assert start == datetime(
        2025,
        12,
        1,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )


def test_custom_api_period_preserves_explicit_window() -> None:
    payload = ReportRequest(
        company_id=2,
        report_type="custom",
        start_date=datetime(
            2026,
            9,
            5,
            9,
            15,
            tzinfo=timezone.utc,
        ),
        end_date=datetime(
            2026,
            9,
            10,
            18,
            45,
            tzinfo=timezone.utc,
        ),
    )

    start, end = _resolve_period(payload)

    assert start == datetime(
        2026,
        9,
        5,
        9,
        15,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        10,
        18,
        45,
        tzinfo=timezone.utc,
    )


def test_custom_api_period_requires_start_date() -> None:
    payload = ReportRequest(
        company_id=2,
        report_type="custom",
        end_date=datetime(
            2026,
            9,
            17,
            tzinfo=timezone.utc,
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        _resolve_period(payload)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == (
        "start_date is required for custom reports."
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("search_mode", ["keyword", "semantic"])
async def test_search_report_resolves_all_results_and_preserves_context(
    monkeypatch,
    search_mode: str,
) -> None:
    batch_mock = AsyncMock(
        return_value=[SimpleNamespace(file_format="pdf", id=456)]
    )
    monkeypatch.setattr(reports, "generate_report_batch", batch_mock)

    filters = {
        "start": "2026-09-01T00:00:00+00:00",
        "end": "2026-09-30T00:00:00+00:00",
        "source_name": "Example News",
        "sentiment": "negative",
        "risk_level": "high",
    }
    
    # We now provide exact snapshot IDs
    article_ids = list(range(1, 51))
    
    payload = ReportRequest(
        company_id=12,
        report_type="custom",
        report_scope="search_results",
        article_ids=article_ids,
        search_query="security incident",
        search_mode=search_mode,
        search_filters=filters,
        minimum_similarity=0.73 if search_mode == "semantic" else None,
        start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )

    record = await reports.generate_report_record(
        SimpleNamespace(),
        payload,
        "pdf",
    )

    assert record.id == 456
    
    # Verify that the exact article IDs are passed to batch generation
    assert batch_mock.await_args.kwargs["article_ids"] == article_ids

    assert batch_mock.await_args.kwargs["search_query"] == "security incident"
    assert batch_mock.await_args.kwargs["search_mode"] == search_mode
    assert batch_mock.await_args.kwargs["search_filters"] == filters
    assert batch_mock.await_args.kwargs["minimum_similarity"] == payload.minimum_similarity
