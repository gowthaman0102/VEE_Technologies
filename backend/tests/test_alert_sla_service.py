from datetime import datetime, timedelta, timezone

import pytest

from app.services.alert_sla_service import (
    calculate_alert_sla,
    is_alert_overdue,
)


BASE_TIME = datetime(
    2026,
    9,
    11,
    10,
    0,
    tzinfo=timezone.utc,
)


def test_review_alert_has_60_minute_sla():
    result = calculate_alert_sla(
        alert_type="review",
        created_at=BASE_TIME,
    )

    assert result.sla_minutes == 60
    assert result.due_at == BASE_TIME + timedelta(
        minutes=60,
    )


def test_urgent_alert_has_15_minute_sla():
    result = calculate_alert_sla(
        alert_type="urgent",
        created_at=BASE_TIME,
    )

    assert result.sla_minutes == 15
    assert result.due_at == BASE_TIME + timedelta(
        minutes=15,
    )


def test_alert_type_is_normalized():
    result = calculate_alert_sla(
        alert_type=" URGENT ",
        created_at=BASE_TIME,
    )

    assert result.alert_type == "urgent"


def test_unknown_alert_type_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unsupported alert type",
    ):
        calculate_alert_sla(
            alert_type="unknown",
            created_at=BASE_TIME,
        )


def test_pending_alert_before_deadline_is_not_overdue():
    due_at = BASE_TIME + timedelta(
        minutes=60,
    )

    assert is_alert_overdue(
        sla_due_at=due_at,
        now=BASE_TIME + timedelta(
            minutes=30,
        ),
    ) is False


def test_pending_alert_after_deadline_is_overdue():
    due_at = BASE_TIME + timedelta(
        minutes=60,
    )

    assert is_alert_overdue(
        sla_due_at=due_at,
        now=BASE_TIME + timedelta(
            minutes=61,
        ),
    ) is True


def test_on_time_delivery_is_not_overdue():
    due_at = BASE_TIME + timedelta(
        minutes=60,
    )

    assert is_alert_overdue(
        sla_due_at=due_at,
        delivered_at=BASE_TIME + timedelta(
            minutes=45,
        ),
        now=BASE_TIME + timedelta(
            minutes=90,
        ),
    ) is False


def test_late_delivery_is_overdue():
    due_at = BASE_TIME + timedelta(
        minutes=60,
    )

    assert is_alert_overdue(
        sla_due_at=due_at,
        delivered_at=BASE_TIME + timedelta(
            minutes=70,
        ),
    ) is True


def test_naive_created_at_is_rejected():
    naive_time = datetime(
        2026,
        9,
        11,
        10,
        0,
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        calculate_alert_sla(
            alert_type="review",
            created_at=naive_time,
        )
