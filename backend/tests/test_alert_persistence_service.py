from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.alert import Alert
from app.services.alert_persistence_service import (
    StoredRiskAssessmentNotFoundError,
    save_alert,
)


SLA_DUE = datetime(
    2026,
    9,
    11,
    12,
    0,
    tzinfo=timezone.utc,
)


@pytest.mark.asyncio
async def test_save_alert_creates_record():
    db = AsyncMock()
    db.add = MagicMock()

    risk_result = MagicMock()
    risk_result.scalar_one_or_none.return_value = (
        SimpleNamespace(id=1)
    )

    insight_result = MagicMock()
    insight_result.scalar_one_or_none.return_value = (
        SimpleNamespace(id=2)
    )

    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = None

    db.execute.side_effect = [
        risk_result,
        insight_result,
        existing_result,
    ]

    async def refresh_side_effect(record):
        record.id = 10

    db.refresh.side_effect = refresh_side_effect

    record = await save_alert(
        db,
        article_id=8,
        company_id=1,
        alert_type="review",
        severity="high",
        title="PayU alert",
        message="Review required.",
        requires_immediate_delivery=False,
        sla_due_at=SLA_DUE,
    )

    assert record.id == 10
    assert record.article_id == 8
    assert record.company_id == 1
    assert record.risk_assessment_id == 1
    assert record.risk_insight_id == 2
    assert record.alert_type == "review"
    assert record.severity == "high"
    assert record.delivery_status == "pending"
    assert record.retry_count == 0
    assert record.sla_due_at == SLA_DUE

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_alert_updates_without_resetting_delivery():
    delivered_at = datetime(
        2026,
        9,
        11,
        11,
        30,
        tzinfo=timezone.utc,
    )

    existing = Alert(
        id=10,
        article_id=8,
        company_id=1,
        risk_assessment_id=1,
        risk_insight_id=2,
        alert_type="review",
        severity="high",
        title="Old title",
        message="Old message",
        delivery_status="delivered",
        delivery_channel="slack",
        retry_count=2,
        last_error=None,
        requires_immediate_delivery=False,
        sla_due_at=SLA_DUE,
        delivered_at=delivered_at,
    )

    db = AsyncMock()
    db.add = MagicMock()

    risk_result = MagicMock()
    risk_result.scalar_one_or_none.return_value = (
        SimpleNamespace(id=1)
    )

    insight_result = MagicMock()
    insight_result.scalar_one_or_none.return_value = (
        SimpleNamespace(id=2)
    )

    existing_result = MagicMock()
    existing_result.scalar_one_or_none.return_value = (
        existing
    )

    db.execute.side_effect = [
        risk_result,
        insight_result,
        existing_result,
    ]

    new_due = datetime(
        2026,
        9,
        11,
        14,
        0,
        tzinfo=timezone.utc,
    )

    record = await save_alert(
        db,
        article_id=8,
        company_id=1,
        alert_type="review",
        severity="high",
        title="Updated title",
        message="Updated message",
        requires_immediate_delivery=False,
        sla_due_at=new_due,
    )

    assert record is existing
    assert record.title == "Updated title"
    assert record.message == "Updated message"

    assert record.delivery_status == "delivered"
    assert record.delivery_channel == "slack"
    assert record.retry_count == 2
    assert record.delivered_at == delivered_at
    assert record.sla_due_at == SLA_DUE

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_alert_requires_risk_assessment():
    db = AsyncMock()

    risk_result = MagicMock()
    risk_result.scalar_one_or_none.return_value = None

    db.execute.return_value = risk_result

    with pytest.raises(
        StoredRiskAssessmentNotFoundError,
        match="Stored risk assessment not found",
    ):
        await save_alert(
            db,
            article_id=8,
            company_id=1,
            alert_type="review",
            severity="high",
            title="PayU alert",
            message="Review required.",
            requires_immediate_delivery=False,
            sla_due_at=SLA_DUE,
        )

    db.commit.assert_not_awaited()
