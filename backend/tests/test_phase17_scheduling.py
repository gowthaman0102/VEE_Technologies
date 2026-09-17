from datetime import datetime, timezone

import pytest

from app.tasks.report_tasks import (
    _scheduled_report_period,
)


def test_daily_uses_previous_completed_calendar_day() -> None:
    now = datetime(
        2026,
        9,
        17,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start, end = _scheduled_report_period(
        "daily",
        now=now,
    )

    assert start == datetime(
        2026,
        9,
        16,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        17,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_weekly_uses_previous_completed_monday_sunday_week() -> None:
    now = datetime(
        2026,
        9,
        17,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start, end = _scheduled_report_period(
        "weekly",
        now=now,
    )

    assert start == datetime(
        2026,
        9,
        7,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        14,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_monthly_uses_previous_calendar_month() -> None:
    now = datetime(
        2026,
        9,
        17,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start, end = _scheduled_report_period(
        "monthly",
        now=now,
    )

    assert start == datetime(
        2026,
        8,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_monthly_handles_february_leap_year() -> None:
    now = datetime(
        2024,
        3,
        20,
        10,
        0,
        tzinfo=timezone.utc,
    )

    start, end = _scheduled_report_period(
        "monthly",
        now=now,
    )

    assert start == datetime(
        2024,
        2,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2024,
        3,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_monthly_handles_year_boundary() -> None:
    now = datetime(
        2026,
        1,
        15,
        9,
        0,
        tzinfo=timezone.utc,
    )

    start, end = _scheduled_report_period(
        "monthly",
        now=now,
    )

    assert start == datetime(
        2025,
        12,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        1,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_naive_now_is_interpreted_as_utc() -> None:
    now = datetime(
        2026,
        9,
        17,
        14,
        30,
    )

    start, end = _scheduled_report_period(
        "daily",
        now=now,
    )

    assert start.tzinfo == timezone.utc
    assert end.tzinfo == timezone.utc


def test_unsupported_schedule_type_fails() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported scheduled report type"
        ),
    ):
        _scheduled_report_period(
            "quarterly",
            now=datetime(
                2026,
                9,
                17,
                tzinfo=timezone.utc,
            ),
        )

def test_report_beat_schedules_use_crontab() -> None:
    from celery.schedules import crontab

    from app.core.celery_app import celery_app

    beat = celery_app.conf.beat_schedule

    daily = beat[
        "generate-daily-intelligence-reports"
    ]
    weekly = beat[
        "generate-weekly-intelligence-reports"
    ]
    monthly = beat[
        "generate-monthly-intelligence-reports"
    ]

    assert daily["task"] == "reports.generate_daily"
    assert weekly["task"] == "reports.generate_weekly"
    assert monthly["task"] == "reports.generate_monthly"

    assert isinstance(
        daily["schedule"],
        crontab,
    )
    assert isinstance(
        weekly["schedule"],
        crontab,
    )
    assert isinstance(
        monthly["schedule"],
        crontab,
    )


def test_report_beat_schedules_are_calendar_based() -> None:
    from app.core.celery_app import celery_app

    beat = celery_app.conf.beat_schedule

    daily = str(
        beat[
            "generate-daily-intelligence-reports"
        ]["schedule"]
    )
    weekly = str(
        beat[
            "generate-weekly-intelligence-reports"
        ]["schedule"]
    )
    monthly = str(
        beat[
            "generate-monthly-intelligence-reports"
        ]["schedule"]
    )

    assert "0" in daily
    assert "10" in daily

    assert "monday" in weekly.lower() or "1" in weekly
    assert "20" in weekly

    assert "1" in monthly
    assert "30" in monthly
