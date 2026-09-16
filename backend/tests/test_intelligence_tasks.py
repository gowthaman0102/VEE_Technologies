from types import SimpleNamespace

import pytest

from app.tasks import intelligence_tasks


class FakeSession:
    async def __aenter__(self):
        return object()

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
    ):
        return False


@pytest.mark.asyncio
async def test_intelligence_pipeline_order(
    monkeypatch,
):
    calls = []

    async def fake_sentiment(
        db,
        *,
        article_id,
        company_id,
    ):
        calls.append("sentiment")

        return SimpleNamespace(
            sentiment=SimpleNamespace(
                label="positive",
                score=0.91,
                reason="Positive development.",
                model="fake-sentiment-model",
            )
        )

    async def fake_business_impact(
        db,
        *,
        article_id,
        company_id,
    ):
        calls.append("business_impact")

        return SimpleNamespace(
            impact=SimpleNamespace(
                primary_category="operational",
                categories=[
                    "operational",
                    "customer",
                ],
                impact_summary=(
                    "Expansion increases "
                    "operational capacity."
                ),
                model="fake-impact-model",
            )
        )

    async def fake_competitors(
        db,
        *,
        article_id,
        company_id,
    ):
        calls.append("competitors")

        return SimpleNamespace(
            competitors=[
                "Competitor One",
            ]
        )

    async def fake_triage(
        db,
        article_id,
        company_id,
        *,
        provider=None,
        rag_limit=3,
    ):
        calls.append("triage")

        return SimpleNamespace(
            triage=SimpleNamespace(
                event_type="market_competition",
                urgency="low",
                confidence=0.88,
            )
        )

    async def fake_risk(
        db,
        *,
        article_id,
        company_id,
    ):
        calls.append("risk")

        return SimpleNamespace(
            article_id=article_id,
            company_id=company_id,
            model="fake-risk-model",
            assessment=SimpleNamespace(
                risk=SimpleNamespace(
                    risk_score=25.0,
                    risk_level="low",
                ),
                escalation=SimpleNamespace(
                    action="monitor",
                ),
            ),
            insight=SimpleNamespace(
                attention_level="low",
                headline="Test headline",
            ),
        )

    async def fake_alert(
        db,
        *,
        article_id,
        company_id,
    ):
        calls.append("alert")

        return SimpleNamespace(
            should_create_alert=False,
            alert=None,
        )

    monkeypatch.setattr(
        intelligence_tasks,
        "CeleryAsyncSessionLocal",
        FakeSession,
    )

    monkeypatch.setattr(
        intelligence_tasks,
        "analyze_article_sentiment",
        fake_sentiment,
    )

    monkeypatch.setattr(
        intelligence_tasks,
        "analyze_article_business_impact",
        fake_business_impact,
    )

    monkeypatch.setattr(
        intelligence_tasks,
        "analyze_article_competitors",
        fake_competitors,
    )

    monkeypatch.setattr(
        intelligence_tasks,
        "triage_article",
        fake_triage,
    )

    monkeypatch.setattr(
        intelligence_tasks,
        "generate_risk_insight",
        fake_risk,
    )

    monkeypatch.setattr(
        intelligence_tasks,
        "create_alert_for_intelligence",
        fake_alert,
    )

    result = await (
        intelligence_tasks
        ._process_article_intelligence(
            article_id=701,
            company_id=2,
        )
    )

    assert calls == [
        "sentiment",
        "business_impact",
        "competitors",
        "triage",
        "risk",
        "alert",
    ]

    assert result["article_id"] == 701
    assert result["company_id"] == 2

    assert result["sentiment_label"] == "positive"
    assert result["sentiment_score"] == 0.91

    assert (
        result["business_impact_primary"]
        == "operational"
    )

    assert result["competitors"] == [
        "Competitor One",
    ]

    assert result["competitor_count"] == 1

    assert (
        result["triage_event_type"]
        == "market_competition"
    )

    assert result["triage_urgency"] == "low"
    assert result["triage_confidence"] == 0.88

    assert result["risk_score"] == 25.0
    assert result["risk_level"] == "low"

    assert result["alert_created"] is False
