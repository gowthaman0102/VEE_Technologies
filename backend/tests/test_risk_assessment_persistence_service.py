from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.risk_assessment import RiskAssessment
from app.services.monitoring_priority_service import (
    MonitoringPriorityResult,
)
from app.services.risk_assessment_service import (
    RiskAssessmentResult,
)
from app.services.risk_escalation_service import (
    EscalationDecision,
)
from app.services.risk_rule_service import (
    RiskCalculation,
)
from app.services.risk_assessment_persistence_service import (
    save_risk_assessment,
)


def make_assessment():
    return RiskAssessmentResult(
        triage_id=1,
        article_id=8,
        company_id=1,
        company_name="PayU",
        event_type="regulatory_action",
        urgency="high",
        confidence=0.9,
        monitoring_priority=MonitoringPriorityResult(
            company_id=1,
            event_type="regulatory_action",
            monitoring_topic="Regulatory Action",
            priority="high",
            source="configured",
        ),
        risk=RiskCalculation(
            event_type="regulatory_action",
            monitoring_topic="Regulatory Action",
            topic_priority="high",
            urgency="high",
            confidence=0.9,
            priority_score=80.0,
            urgency_score=75.0,
            confidence_score=90.0,
            risk_score=80.0,
            risk_level="high",
        ),
        escalation=EscalationDecision(
            risk_level="high",
            action="review",
            requires_human_review=True,
            requires_immediate_alert=False,
        ),
    )


@pytest.mark.asyncio
async def test_save_risk_assessment_creates_record():
    db = AsyncMock()
    db.add = MagicMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    async def refresh_side_effect(record):
        record.id = 1

    db.refresh.side_effect = refresh_side_effect

    result = await save_risk_assessment(
        db,
        assessment=make_assessment(),
    )

    assert result.article_id == 8
    assert result.company_id == 1
    assert result.triage_id == 1
    assert result.risk_score == 80.0
    assert result.risk_level == "high"
    assert result.escalation_action == "review"
    assert result.requires_human_review is True
    assert result.requires_immediate_alert is False

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_risk_assessment_updates_record():
    existing = RiskAssessment(
        id=1,
        triage_id=1,
        article_id=8,
        company_id=1,
        event_type="other",
        monitoring_topic=None,
        topic_priority="medium",
        priority_source="fallback",
        urgency="low",
        confidence=0.4,
        risk_score=30.0,
        risk_level="low",
        escalation_action="ignore",
        requires_human_review=False,
        requires_immediate_alert=False,
    )

    db = AsyncMock()
    db.add = MagicMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = existing
    db.execute.return_value = execute_result

    result = await save_risk_assessment(
        db,
        assessment=make_assessment(),
    )

    assert result is existing
    assert result.event_type == "regulatory_action"
    assert result.monitoring_topic == "Regulatory Action"
    assert result.topic_priority == "high"
    assert result.priority_source == "configured"
    assert result.urgency == "high"
    assert result.confidence == 0.9
    assert result.risk_score == 80.0
    assert result.risk_level == "high"
    assert result.escalation_action == "review"
    assert result.requires_human_review is True
    assert result.requires_immediate_alert is False

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
