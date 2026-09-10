from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.monitoring_priority_service import (
    MonitoringPriorityResult,
)
from app.services.risk_assessment_service import (
    StoredTriageNotFoundError,
    assess_article_risk,
)


def make_triage(
    *,
    event_type="regulatory_action",
    urgency="high",
    confidence=0.9,
):
    return SimpleNamespace(
        id=1,
        article_id=8,
        company_id=1,
        company_name="PayU",
        event_type=event_type,
        urgency=urgency,
        confidence=confidence,
    )


def make_priority(
    *,
    event_type="regulatory_action",
    topic="Regulatory Action",
    priority="high",
    source="configured",
):
    return MonitoringPriorityResult(
        company_id=1,
        event_type=event_type,
        monitoring_topic=topic,
        priority=priority,
        source=source,
    )


@pytest.mark.asyncio
async def test_assess_article_risk_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "get_article_triage",
        AsyncMock(
            return_value=make_triage()
        ),
    )

    persistence_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "save_risk_assessment",
        persistence_mock,
    )

    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "resolve_monitoring_priority",
        AsyncMock(
            return_value=make_priority()
        ),
    )

    result = await assess_article_risk(
        AsyncMock(),
        article_id=8,
        company_id=1,
    )

    assert result.triage_id == 1
    assert result.article_id == 8
    assert result.company_id == 1
    assert result.company_name == "PayU"

    assert result.event_type == (
        "regulatory_action"
    )

    assert result.monitoring_priority.priority == (
        "high"
    )

    assert result.monitoring_priority.source == (
        "configured"
    )

    assert result.risk.risk_score == 80.0
    assert result.risk.risk_level == "high"


@pytest.mark.asyncio
async def test_assess_article_risk_uses_fallback_priority(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "get_article_triage",
        AsyncMock(
            return_value=make_triage(
                event_type="financial_performance",
                urgency="medium",
                confidence=0.8,
            )
        ),
    )

    persistence_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "save_risk_assessment",
        persistence_mock,
    )

    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "resolve_monitoring_priority",
        AsyncMock(
            return_value=make_priority(
                event_type="financial_performance",
                topic=None,
                priority="medium",
                source="fallback",
            )
        ),
    )

    result = await assess_article_risk(
        AsyncMock(),
        article_id=8,
        company_id=1,
    )

    assert result.monitoring_priority.priority == (
        "medium"
    )

    assert result.monitoring_priority.source == (
        "fallback"
    )

    assert result.risk.risk_score == 56.0
    assert result.risk.risk_level == "medium"


@pytest.mark.asyncio
async def test_assess_article_risk_missing_triage(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "get_article_triage",
        AsyncMock(return_value=None),
    )

    priority_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.risk_assessment_service."
        "resolve_monitoring_priority",
        priority_mock,
    )

    with pytest.raises(
        StoredTriageNotFoundError,
        match="Stored triage result not found",
    ):
        await assess_article_risk(
            AsyncMock(),
            article_id=999,
            company_id=1,
        )

    priority_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_assess_article_risk_critical():
    triage = make_triage(
        event_type="service_outage",
        urgency="critical",
        confidence=1.0,
    )

    priority = make_priority(
        event_type="service_outage",
        topic="Service Outage",
        priority="high",
        source="configured",
    )

    from app.services.risk_rule_service import (
        calculate_risk,
    )

    result = calculate_risk(
        event_type=triage.event_type,
        topic_priority=priority.priority,
        urgency=triage.urgency,
        confidence=triage.confidence,
    )

    assert result.risk_score == 92.0
    assert result.risk_level == "critical"
