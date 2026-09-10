from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.schemas.risk_insight import RiskInsightResult
from app.services.monitoring_priority_service import (
    MonitoringPriorityResult,
)
from app.services.risk_assessment_service import (
    RiskAssessmentResult,
)
from app.services.risk_escalation_service import (
    EscalationDecision,
)
from app.services.risk_insight_service import (
    generate_risk_insight,
)
from app.services.risk_rule_service import (
    RiskCalculation,
)


def make_triage():
    return SimpleNamespace(
        summary="PayU received RBI authorization.",
        why_it_matters=(
            "The authorization affects regulatory "
            "standing and operations in India."
        ),
        potential_impact=(
            "The development may influence business "
            "operations and stakeholder confidence."
        ),
        evidence=[
            "PayU has received final authorization "
            "from RBI."
        ],
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
async def test_generate_risk_insight_success(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "get_article_triage",
        AsyncMock(
            return_value=make_triage()
        ),
    )

    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "assess_article_risk",
        AsyncMock(
            return_value=make_assessment()
        ),
    )

    persistence_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "save_risk_insight",
        persistence_mock,
    )

    provider = AsyncMock()

    provider.generate.return_value = SimpleNamespace(
        text=(
            '''
            {
                "headline": "PayU faces high regulatory attention",
                "executive_summary": "PayU received RBI authorization and the event requires business review.",
                "recommended_action": "Review the regulatory development and monitor follow-up implications.",
                "key_reasons": [
                    "The event is regulatory in nature.",
                    "The deterministic risk level is high."
                ],
                "attention_level": "high"
            }
            '''
        ),
        model="qwen2.5:7b",
    )

    result = await generate_risk_insight(
        AsyncMock(),
        article_id=8,
        company_id=1,
        provider=provider,
    )

    assert result.article_id == 8
    assert result.company_id == 1
    assert result.model == "qwen2.5:7b"

    assert isinstance(
        result.insight,
        RiskInsightResult,
    )

    assert result.insight.attention_level == "high"
    assert result.assessment.risk.risk_score == 80.0

    provider.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_risk_insight_rejects_invalid_json(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "get_article_triage",
        AsyncMock(
            return_value=make_triage()
        ),
    )

    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "assess_article_risk",
        AsyncMock(
            return_value=make_assessment()
        ),
    )

    provider = AsyncMock()

    provider.generate.return_value = SimpleNamespace(
        text="not json",
        model="qwen2.5:7b",
    )

    with pytest.raises(
        ValueError,
        match="Insight agent returned invalid JSON",
    ):
        await generate_risk_insight(
            AsyncMock(),
            article_id=8,
            company_id=1,
            provider=provider,
        )


@pytest.mark.asyncio
async def test_generate_risk_insight_rejects_level_override(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "get_article_triage",
        AsyncMock(
            return_value=make_triage()
        ),
    )

    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "assess_article_risk",
        AsyncMock(
            return_value=make_assessment()
        ),
    )

    provider = AsyncMock()

    provider.generate.return_value = SimpleNamespace(
        text=(
            '''
            {
                "headline": "PayU regulatory update",
                "executive_summary": "The development requires attention.",
                "recommended_action": "Review the event.",
                "key_reasons": [
                    "Regulatory development detected."
                ],
                "attention_level": "critical"
            }
            '''
        ),
        model="qwen2.5:7b",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Insight attention level does not match "
            "the deterministic risk level"
        ),
    ):
        await generate_risk_insight(
            AsyncMock(),
            article_id=8,
            company_id=1,
            provider=provider,
        )


@pytest.mark.asyncio
async def test_generate_risk_insight_missing_triage(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "get_article_triage",
        AsyncMock(
            return_value=None
        ),
    )

    assessment_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.risk_insight_service."
        "assess_article_risk",
        assessment_mock,
    )

    with pytest.raises(
        ValueError,
        match="Stored triage result not found",
    ):
        await generate_risk_insight(
            AsyncMock(),
            article_id=999,
            company_id=1,
            provider=AsyncMock(),
        )

    assessment_mock.assert_not_awaited()
