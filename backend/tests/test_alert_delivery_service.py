from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.alert import Alert
from app.services.alert_delivery_service import (
    AlertNotFoundError,
    deliver_alert,
)
from app.services.slack_alert_service import (
    SlackDeliveryResult,
)


def make_alert() -> Alert:
    return Alert(
        id=2,
        article_id=8,
        company_id=1,
        risk_assessment_id=1,
        risk_insight_id=1,
        alert_type="review",
        severity="high",
        title="PayU alert",
        message="Review required.",
        delivery_status="pending",
        delivery_channel=None,
        retry_count=0,
        last_error=None,
        requires_immediate_delivery=False,
    )


@pytest.mark.asyncio
async def test_deliver_alert_marks_success():
    alert = make_alert()

    db = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = alert
    db.execute.return_value = execute_result

    with patch(
        "app.services.alert_delivery_service."
        "send_alert_to_slack",
        new=AsyncMock(
            return_value=SlackDeliveryResult(
                delivered=True,
                status_code=200,
                error=None,
            )
        ),
    ):
        record = await deliver_alert(
            db,
            alert_id=2,
        )

    assert record.delivery_status == "delivered"
    assert record.delivery_channel == "slack"
    assert record.retry_count == 0
    assert record.last_error is None
    assert record.delivered_at is not None

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_deliver_alert_records_failure():
    alert = make_alert()

    db = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = alert
    db.execute.return_value = execute_result

    with patch(
        "app.services.alert_delivery_service."
        "send_alert_to_slack",
        new=AsyncMock(
            return_value=SlackDeliveryResult(
                delivered=False,
                status_code=None,
                error="Slack webhook is not configured.",
            )
        ),
    ):
        record = await deliver_alert(
            db,
            alert_id=2,
        )

    assert record.delivery_status == "failed"
    assert record.delivery_channel == "slack"
    assert record.retry_count == 1
    assert (
        record.last_error
        == "Slack webhook is not configured."
    )
    assert record.delivered_at is None

    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_deliver_alert_requires_existing_alert():
    db = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    with pytest.raises(
        AlertNotFoundError,
        match="Alert 999 not found",
    ):
        await deliver_alert(
            db,
            alert_id=999,
        )

    db.commit.assert_not_awaited()
