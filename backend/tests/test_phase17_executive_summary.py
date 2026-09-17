from app.services.report_service import (
    build_deterministic_executive_summary,
)


def test_empty_report_summary_does_not_invent_findings():
    report = {
        "company_name": "VEE Technologies",
        "total_articles": 0,
        "total_events": 0,
        "high_risk_count": 0,
        "sentiment_balance": {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
        },
        "alerts": [],
        "competitors": [],
    }

    summary = build_deterministic_executive_summary(
        report
    )

    assert "No qualifying media articles" in summary
    assert "no media-driven" in summary.lower()


def test_non_empty_report_summary_uses_stored_metrics():
    report = {
        "company_name": "VEE Technologies",
        "total_articles": 5,
        "total_events": 2,
        "high_risk_count": 1,
        "sentiment_balance": {
            "positive": 1,
            "neutral": 1,
            "negative": 3,
        },
        "alerts": [
            {"id": 1},
            {"id": 2},
        ],
        "competitors": [],
    }

    summary = build_deterministic_executive_summary(
        report
    )

    assert "5 qualifying media articles" in summary
    assert "predominantly negative" in summary
    assert "1 article was classified as high risk" in summary
    assert "2 tracked events" in summary
    assert "2 alerts were generated" in summary
    assert "No competitors are currently configured" in summary
