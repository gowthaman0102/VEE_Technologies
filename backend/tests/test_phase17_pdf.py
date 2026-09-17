from copy import deepcopy
from datetime import datetime, timezone

from app.services.report_service import (
    build_deterministic_executive_summary,
    export_report_pdf,
)


def _base_report() -> dict:
    report = {
        "company_id": 2,
        "company_name": "VEE Technologies",
        "start_date": datetime(
            2026, 9, 1,
            tzinfo=timezone.utc,
        ),
        "end_date": datetime(
            2026, 9, 17,
            tzinfo=timezone.utc,
        ),
        "total_articles": 0,
        "total_events": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
        "sentiment_balance": {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
        },
        "metrics": [],
        "overview": {
            "total_articles": 0,
            "total_events": 0,
            "total_alerts": 0,
        },
        "article_trend": [],
        "articles": [],
        "sentiment": {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "series": [],
        },
        "risk": {
            "average_risk_score": 0.0,
            "highest_risk_score": 0.0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "series": [],
        },
        "business_impact": {
            "primary_distribution": {},
            "category_distribution": {},
        },
        "events": {
            "total_events": 0,
            "largest_events": [],
        },
        "sources": [],
        "competitors": [],
        "alerts": [],
        "highest_risk_stories": [],
    }

    report["executive_summary"] = (
        build_deterministic_executive_summary(
            report
        )
    )

    return report


def test_phase17_pdf_empty_report_renders() -> None:
    report = _base_report()

    content = export_report_pdf(report)

    assert content.startswith(b"%PDF")
    assert len(content) > 3000


def test_phase17_pdf_does_not_mutate_input() -> None:
    report = _base_report()
    before = deepcopy(report)

    export_report_pdf(report)

    assert report == before


def test_phase17_pdf_nonempty_report_renders() -> None:
    report = _base_report()

    report.update(
        {
            "total_articles": 3,
            "total_events": 1,
            "high_risk_count": 1,
            "medium_risk_count": 1,
            "low_risk_count": 1,
            "sentiment_balance": {
                "positive": 1,
                "neutral": 1,
                "negative": 1,
            },
        }
    )

    report["sentiment"] = {
        "positive": 1,
        "neutral": 1,
        "negative": 1,
        "series": [
            {
                "period": "2026-09-15",
                "positive": 1,
                "neutral": 1,
                "negative": 1,
            }
        ],
    }

    report["risk"] = {
        "average_risk_score": 46.25,
        "highest_risk_score": 86.5,
        "high_risk_count": 1,
        "medium_risk_count": 1,
        "low_risk_count": 1,
        "series": [
            {
                "period": "2026-09-15",
                "average_risk_score": 46.25,
                "maximum_risk_score": 86.5,
                "low_count": 1,
                "medium_count": 1,
                "high_count": 1,
                "escalation_count": 1,
            }
        ],
    }

    report["business_impact"] = {
        "primary_distribution": {
            "operational": 2,
            "market": 1,
        },
        "category_distribution": {
            "operational": 2,
            "market": 2,
            "reputation": 1,
        },
    }

    report["events"] = {
        "total_events": 1,
        "largest_events": [
            {
                "cluster_id": 5,
                "title": "Tracked media event",
                "article_count": 3,
                "first_published_at": datetime(
                    2026, 9, 14,
                    tzinfo=timezone.utc,
                ),
                "last_published_at": datetime(
                    2026, 9, 15,
                    tzinfo=timezone.utc,
                ),
            }
        ],
    }

    report["sources"] = [
        {
            "source_name": "Business Daily",
            "article_count": 3,
        }
    ]

    report["alerts"] = [
        {
            "article_id": 100,
            "alert_type": "risk_threshold",
            "severity": "high",
            "title": "Elevated risk",
            "message": "Risk threshold exceeded.",
            "delivery_status": "delivered",
            "delivery_channel": "slack",
            "created_at": (
                "2026-09-15T09:00:00+00:00"
            ),
        }
    ]

    report["highest_risk_stories"] = [
        {
            "article_id": 100,
            "title": "Operational risk story",
            "source_name": "Business Daily",
            "published_at": (
                "2026-09-15T08:30:00+00:00"
            ),
            "sentiment": "negative",
            "business_impact_primary": "operational",
            "risk_score": 86.5,
            "risk_level": "high",
            "risk_headline": "Elevated operational risk",
            "risk_summary": (
                "Stored risk analysis identifies "
                "elevated operational impact."
            ),
            "event_cluster_title": "Tracked media event",
        }
    ]

    report["executive_summary"] = (
        build_deterministic_executive_summary(
            report
        )
    )

    content = export_report_pdf(report)

    assert content.startswith(b"%PDF")
    assert len(content) > 5000


def test_phase17_pdf_handles_long_text() -> None:
    report = _base_report()

    long_text = (
        "Long media intelligence narrative with "
        "special characters A&B <review> > context. "
        * 120
    )

    report["total_articles"] = 1
    report["high_risk_count"] = 1
    report["risk"]["high_risk_count"] = 1
    report["risk"]["highest_risk_score"] = 91.0

    report["highest_risk_stories"] = [
        {
            "article_id": 999,
            "title": long_text,
            "source_name": "Long Source & Partners",
            "published_at": (
                "2026-09-16T12:00:00+00:00"
            ),
            "sentiment": "negative",
            "business_impact_primary": "operational",
            "risk_score": 91.0,
            "risk_level": "high",
            "risk_headline": long_text,
            "risk_summary": long_text,
            "event_cluster_title": long_text,
        }
    ]

    report["alerts"] = [
        {
            "title": long_text,
            "severity": "high",
            "alert_type": "risk_threshold",
            "message": long_text,
        }
    ]

    report["executive_summary"] = long_text

    content = export_report_pdf(report)

    assert content.startswith(b"%PDF")
    assert len(content) > 5000
