from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

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
