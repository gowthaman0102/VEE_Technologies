from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_analytics_overview(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.analytics.validate_time_window",
        lambda start, end: (start, end),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_sentiment_distribution",
        AsyncMock(return_value={"positive": 4, "neutral": 2, "negative": 1}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_risk_summary",
        AsyncMock(return_value={"average_risk_score": 65.5, "highest_risk_score": 92.0, "high_risk_count": 2, "medium_risk_count": 3, "low_risk_count": 1}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_business_impact_distribution",
        AsyncMock(return_value={"reputation": 3, "financial": 1}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_competitor_summary",
        AsyncMock(return_value={"competitors": [{"name": "Acme", "mention_count": 4}]}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_event_summary",
        AsyncMock(return_value={"total_events": 2, "largest_events": [{"cluster_id": 1, "article_count": 3}]}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_article_count",
        AsyncMock(return_value=7),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_period_comparison",
        AsyncMock(return_value={"article_volume_change_percent": 0.0}),
    )

    start = datetime.now(timezone.utc) - timedelta(days=7)
    end = datetime.now(timezone.utc)

    response = client.get(
        "/api/v1/analytics/overview",
        params={"company_id": 1, "start": start.isoformat(), "end": end.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == 1
    assert data["sentiment"]["positive"] == 4
    assert data["risk"]["high_risk_count"] == 2
    assert data["competitors"][0]["name"] == "Acme"
    assert data["total_events"] == 2


def test_get_article_trend(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.analytics.validate_time_window",
        lambda start, end: (start, end),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_article_volume_over_time",
        AsyncMock(return_value=[{"bucket": "2026-09-10T00:00:00+00:00", "article_count": 5}]),
    )

    start = datetime.now(timezone.utc) - timedelta(days=7)
    end = datetime.now(timezone.utc)

    response = client.get(
        "/api/v1/analytics/articles/trend",
        params={"company_id": 1, "start": start.isoformat(), "end": end.isoformat(), "bucket": "day"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == 1
    assert data["bucket"] == "day"
    assert data["points"][0]["article_count"] == 5
