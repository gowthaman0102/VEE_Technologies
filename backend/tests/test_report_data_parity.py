from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.report_service import (
    _report_summaries,
    export_report_csv,
)


def test_report_summaries_use_article_snapshot_without_triage_dependency():
    rows = [
        {
            "sentiment": "negative",
            "risk_score": 80.0,
            "risk_level": "high",
            "business_impact_primary": "legal",
            "business_impact_categories": ["legal", "reputation"],
            "event_cluster_id": 7,
            "alerts": [{"alert_type": "review"}],
            "source_name": "OpenAI Official News",
        },
        {
            "sentiment": None,
            "risk_score": None,
            "risk_level": None,
            "business_impact_primary": None,
            "business_impact_categories": [],
            "event_cluster_id": None,
            "alerts": [],
            "source_name": "Google News - OpenAI",
        },
    ]

    sentiment, risk, impact, events = _report_summaries(rows)

    assert sentiment == {"positive": 0, "neutral": 0, "negative": 1}
    assert risk["high_risk_count"] == 1
    assert impact["category_distribution"] == {
        "legal": 1,
        "reputation": 1,
    }
    assert events["total_events"] == 1


def test_csv_contains_snapshot_risk_sources_and_alerts():
    data = {
        "company_id": 3,
        "company_name": "OpenAI",
        "start_date": datetime(2026, 7, 31, tzinfo=timezone.utc),
        "end_date": datetime(2026, 9, 18, tzinfo=timezone.utc),
        "total_articles": 2,
        "total_events": 1,
        "high_risk_count": 1,
        "medium_risk_count": 0,
        "low_risk_count": 0,
        "sentiment_balance": {"positive": 0, "neutral": 0, "negative": 1},
        "risk": {"average_risk_score": 80.0, "highest_risk_score": 80.0},
        "sources": [{"source_name": "OpenAI Official News", "article_count": 2}],
        "alerts": [{"article_id": 1}],
    }
    csv_text = export_report_csv(data).decode("utf-8")
    assert "average_risk_score,80.0" in csv_text
    assert "source_count,1" in csv_text
    assert "alert_count,1" in csv_text
