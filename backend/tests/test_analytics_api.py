from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

client = TestClient(app)


def test_business_impact_articles_returns_company_scoped_total_and_page():
    article = SimpleNamespace(
        id=120,
        title="Security incident",
        source_name="Example News",
        url="https://example.com/security",
        published_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        collected_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
    )
    db = SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(id=7)),
        scalar=AsyncMock(return_value=153),
        execute=AsyncMock(
            return_value=SimpleNamespace(
                all=lambda: [(article, "incident", "negative", "high", 72.0, "cybersecurity")]
            )
        ),
    )
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        start = datetime.now(timezone.utc) - timedelta(days=270)
        end = datetime.now(timezone.utc)
        response = client.get(
            "/api/v1/analytics/business-impact/articles",
            params={
                "company_id": 7,
                "category": "cybersecurity",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "page": 2,
                "page_size": 1,
            },
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 153
    assert len(result["items"]) == 1
    assert result["items"][0]["article_id"] == 120
    assert result["items"][0]["business_impact"] == "cybersecurity"
    assert response.headers["Cache-Control"] == "no-store, no-cache, must-revalidate"


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


def test_get_analytics_overview_uses_active_company_when_not_provided(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.analytics.validate_time_window",
        lambda start, end: (start, end),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_active_company_profile",
        AsyncMock(return_value=type("Profile", (), {"company_id": 42, "company_name": "VEE Technologies"})()),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_sentiment_distribution",
        AsyncMock(return_value={"positive": 4, "neutral": 2, "negative": 1, "summary": {"positive": 4, "neutral": 2, "negative": 1}}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_risk_summary",
        AsyncMock(return_value={"average_risk_score": 65.5, "highest_risk_score": 92.0, "high_risk_count": 2, "medium_risk_count": 3, "low_risk_count": 1, "summary": {"average_risk_score": 65.5, "highest_risk_score": 92.0, "high_risk_count": 2, "medium_risk_count": 3, "low_risk_count": 1}}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_business_impact_distribution",
        AsyncMock(return_value={"items": {"reputation": 3, "financial": 1}, "summary": {"reputation": 3, "financial": 1}}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_competitor_summary",
        AsyncMock(return_value={"competitors": []}),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_event_summary",
        AsyncMock(return_value={"total_events": 2, "largest_events": []}),
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
        params={"start": start.isoformat(), "end": end.isoformat()},
    )

    assert response.status_code == 200
    assert response.json()["company_id"] == 42


def test_sentiment_trend_response_includes_summary_and_series(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.analytics.validate_time_window",
        lambda start, end: (start, end),
    )
    monkeypatch.setattr(
        "app.api.v1.analytics.get_sentiment_distribution",
        AsyncMock(return_value={
            "summary": {"positive": 6, "neutral": 2, "negative": 1},
            "positive": 6,
            "neutral": 2,
            "negative": 1,
            "series": [{"period": "2026-09-10T00:00:00+00:00", "positive": 3, "neutral": 1, "negative": 0}],
        }),
    )

    start = datetime.now(timezone.utc) - timedelta(days=7)
    end = datetime.now(timezone.utc)

    response = client.get(
        "/api/v1/analytics/sentiment/trend",
        params={"company_id": 1, "start": start.isoformat(), "end": end.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["positive"] == 6
    assert data["series"][0]["positive"] == 3
