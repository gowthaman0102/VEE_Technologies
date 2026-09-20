from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dashboard import (
    DashboardOverviewResponse,
)


client = TestClient(app)


def test_get_dashboard_overview(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.dashboard."
        "get_dashboard_overview",
        AsyncMock(
            return_value=DashboardOverviewResponse(
                total_articles=46,
                processed_articles=3,
                total_companies=1,
                high_risk_items=1,
                critical_risk_items=0,
            )
        ),
    )

    response = client.get(
        "/api/v1/dashboard/overview"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_articles"] == 46
    assert data["processed_articles"] == 3
    assert data["total_companies"] == 1
    assert data["high_risk_items"] == 1
    assert data["critical_risk_items"] == 0


def test_get_dashboard_intelligence(monkeypatch):
    service = AsyncMock(
        return_value={
            "count": 1,
            "items": [
                {
                    "article_id": 8,
                    "company_id": 1,
                    "company_name": "PayU",
                    "title": "PayU RBI approval",
                        "publisher_name": "PayU",
                    "source_name": "Google News",
                    "url": "https://example.com/article",
                    "published_at": None,
                        "collected_at": "2026-09-11T09:00:00+00:00",
                    "event_type": "regulatory_action",
                    "urgency": "high",
                    "confidence": 0.9,
                    "summary": "Summary",
                    "why_it_matters": "Why it matters",
                    "risk_score": 80.0,
                    "risk_level": "high",
                    "escalation_action": "review",
                    "monitoring_topic": "Regulatory Action",
                    "headline": "PayU receives RBI approval",
                    "executive_summary": "Executive summary",
                    "recommended_action": "Review impact.",
                    "attention_level": "high",
                    "updated_at": "2026-09-11T10:00:00+00:00",
                }
            ],
        }
    )

    monkeypatch.setattr(
        "app.api.v1.dashboard."
        "get_dashboard_intelligence",
        service,
    )

    response = client.get(
        "/api/v1/dashboard/intelligence",
        params={
            "limit": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1
    assert data["items"][0]["article_id"] == 8
    assert data["items"][0]["company_name"] == "PayU"
    assert data["items"][0]["risk_score"] == 80.0
    assert data["items"][0]["risk_level"] == "high"


def test_get_dashboard_articles(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.dashboard.get_dashboard_articles",
        AsyncMock(
            return_value={
                "count": 1,
                "items": [
                    {
                        "article_id": 8,
                        "title": "PayU RBI approval",
                        "publisher_name": "PayU",
                        "source_name": "Google News",
                        "url": "https://news.google.com/articles/example",
                        "published_at": None,
                        "collected_at": "2026-09-11T09:00:00+00:00",
                        "event_type": "regulatory_action",
                        "sentiment": None,
                        "risk_level": "high",
                        "risk_score": 80.0,
                        "business_impact": "regulatory",
                    }
                ],
            }
        ),
    )

    response = client.get(
        "/api/v1/dashboard/articles",
        params={"metric": "high-risk"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["source_name"] == "Google News"


def test_get_dashboard_risk_analytics(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.dashboard."
        "get_dashboard_risk_analytics",
        AsyncMock(
            return_value={
                "total_assessments": 1,
                "average_risk_score": 80.0,
                "highest_risk_score": 80.0,
                "human_review_count": 1,
                "immediate_alert_count": 0,
                "risk_levels": [
                    {
                        "label": "high",
                        "count": 1,
                    }
                ],
                "event_types": [
                    {
                        "label": "regulatory_action",
                        "count": 1,
                    }
                ],
            }
        ),
    )

    response = client.get(
        "/api/v1/dashboard/risk-analytics"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_assessments"] == 1
    assert data["average_risk_score"] == 80.0
    assert data["highest_risk_score"] == 80.0
    assert data["human_review_count"] == 1
    assert data["risk_levels"][0] == {
        "label": "high",
        "count": 1,
    }



def test_get_dashboard_companies(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.dashboard."
        "get_dashboard_companies",
        AsyncMock(
            return_value={
                "count": 1,
                "items": [
                    {
                        "id": 1,
                        "name": "PayU",
                        "website": "https://payu.in",
                        "industry": "Fintech / Payments",
                        "is_active": True,
                        "aliases": [
                            "PayU India",
                            "PayU Payments",
                        ],
                        "geographies": [
                            "APAC",
                            "India",
                        ],
                        "regulators": [
                            "RBI",
                        ],
                        "relationships": [],
                        "monitoring_topics": [
                            {
                                "topic": "Regulatory Action",
                                "priority": "high",
                                "is_active": True,
                            }
                        ],
                        "triage_count": 3,
                        "risk_assessment_count": 1,
                        "high_risk_count": 1,
                        "critical_risk_count": 0,
                        "alert_count": 1,
                    }
                ],
            }
        ),
    )

    response = client.get(
        "/api/v1/dashboard/companies"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1
    assert data["items"][0]["name"] == "PayU"
    assert data["items"][0]["triage_count"] == 3
    assert data["items"][0]["risk_assessment_count"] == 1
    assert data["items"][0]["high_risk_count"] == 1
    assert data["items"][0]["alert_count"] == 1
