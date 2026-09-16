from __future__ import annotations

from datetime import datetime

from app.services.analytics_service import (
    get_business_impact_distribution,
    get_event_summary,
    get_risk_summary,
    get_sentiment_distribution,
)


async def build_company_report(db, *, company_id: int, start_date: str, end_date: str) -> dict:
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    sentiment = await get_sentiment_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    risk = await get_risk_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    business = await get_business_impact_distribution(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )
    events = await get_event_summary(
        db,
        company_id=company_id,
        start=start,
        end=end,
    )

    total_articles = sum(business.values()) or 0
    total_events = events.get("total_events", 0)

    metrics = [
        {"label": "Average risk score", "value": risk["average_risk_score"]},
        {"label": "High risk count", "value": risk["high_risk_count"]},
        {"label": "Medium risk count", "value": risk["medium_risk_count"]},
        {"label": "Low risk count", "value": risk["low_risk_count"]},
        {"label": "Positive sentiment", "value": sentiment.get("positive", 0)},
        {"label": "Neutral sentiment", "value": sentiment.get("neutral", 0)},
        {"label": "Negative sentiment", "value": sentiment.get("negative", 0)},
    ]

    return {
        "company_id": company_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_articles": total_articles,
        "total_events": total_events,
        "high_risk_count": risk["high_risk_count"],
        "medium_risk_count": risk["medium_risk_count"],
        "low_risk_count": risk["low_risk_count"],
        "sentiment_balance": {
            "positive": sentiment.get("positive", 0),
            "neutral": sentiment.get("neutral", 0),
            "negative": sentiment.get("negative", 0),
        },
        "metrics": metrics,
    }


def export_report_csv(report_data: dict) -> str:
    rows = [
        ["metric", "value"],
        ["company_id", str(report_data["company_id"])],
        ["start_date", report_data["start_date"]],
        ["end_date", report_data["end_date"]],
        ["total_articles", str(report_data["total_articles"])],
        ["total_events", str(report_data["total_events"])],
        ["high_risk_count", str(report_data["high_risk_count"])],
        ["medium_risk_count", str(report_data["medium_risk_count"])],
        ["low_risk_count", str(report_data["low_risk_count"])],
        ["positive_sentiment", str(report_data["sentiment_balance"].get("positive", 0))],
        ["neutral_sentiment", str(report_data["sentiment_balance"].get("neutral", 0))],
        ["negative_sentiment", str(report_data["sentiment_balance"].get("negative", 0))],
    ]
    for metric in report_data.get("metrics", []):
        rows.append([metric["label"], str(metric["value"])])

    return "\n".join(",".join(str(cell) for cell in row) for row in rows)
