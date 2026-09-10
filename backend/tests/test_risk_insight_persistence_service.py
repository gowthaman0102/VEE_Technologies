from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.risk_assessment import RiskAssessment
from app.models.risk_insight import RiskInsight
from app.schemas.risk_insight import RiskInsightResult
from app.services.risk_insight_persistence_service import (
    StoredRiskAssessmentNotFoundError,
    save_risk_insight,
)


def make_result():
    return SimpleNamespace(
        article_id=8,
        company_id=1,
        model="qwen2.5:7b",
        insight=RiskInsightResult(
            headline="PayU regulatory development",
            executive_summary=(
                "PayU received RBI authorization and "
                "requires business review."
            ),
            recommended_action=(
                "Review the regulatory development."
            ),
            key_reasons=[
                "RBI authorization was received.",
                "The risk level is high.",
            ],
            attention_level="high",
        ),
    )


@pytest.mark.asyncio
async def test_save_risk_insight_creates_record():
    db = AsyncMock()
    db.add = MagicMock()

    risk_result = MagicMock()
    risk_result.scalar_one_or_none.return_value = (
        RiskAssessment(
            id=1,
            triage_id=1,
            article_id=8,
            company_id=1,
            event_type="regulatory_action",
            monitoring_topic="Regulatory Action",
            topic_priority="high",
            priority_source="configured",
            urgency="high",
            confidence=0.9,
            risk_score=80.0,
            risk_level="high",
            escalation_action="review",
            requires_human_review=True,
            requires_immediate_alert=False,
        )
    )

    insight_result = MagicMock()
    insight_result.scalar_one_or_none.return_value = None

    db.execute.side_effect = [
        risk_result,
        insight_result,
    ]

    async def refresh_side_effect(record):
        record.id = 1

    db.refresh.side_effect = refresh_side_effect

    record = await save_risk_insight(
        db,
        result=make_result(),
    )

    assert record.id == 1
    assert record.article_id == 8
    assert record.company_id == 1
    assert record.risk_assessment_id == 1
    assert record.attention_level == "high"
    assert record.llm_model == "qwen2.5:7b"

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_risk_insight_updates_record():
    db = AsyncMock()
    db.add = MagicMock()

    risk_result = MagicMock()
    risk_result.scalar_one_or_none.return_value = (
        SimpleNamespace(id=1)
    )

    existing = RiskInsight(
        id=1,
        risk_assessment_id=1,
        article_id=8,
        company_id=1,
        headline="Old headline",
        executive_summary="Old summary",
        recommended_action="Old action",
        key_reasons=["Old reason"],
        attention_level="medium",
        llm_model="old-model",
    )

    insight_result = MagicMock()
    insight_result.scalar_one_or_none.return_value = (
        existing
    )

    db.execute.side_effect = [
        risk_result,
        insight_result,
    ]

    record = await save_risk_insight(
        db,
        result=make_result(),
    )

    assert record is existing
    assert record.headline == (
        "PayU regulatory development"
    )
    assert record.attention_level == "high"
    assert record.llm_model == "qwen2.5:7b"
    assert len(record.key_reasons) == 2

    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_risk_insight_requires_risk_record():
    db = AsyncMock()

    risk_result = MagicMock()
    risk_result.scalar_one_or_none.return_value = None

    db.execute.return_value = risk_result

    with pytest.raises(
        StoredRiskAssessmentNotFoundError,
        match="Stored risk assessment not found",
    ):
        await save_risk_insight(
            db,
            result=make_result(),
        )

    db.commit.assert_not_awaited()
