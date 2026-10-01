from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import csv
import io
import pytest
from openpyxl import load_workbook

from app.services.report_service import (
    _report_summaries,
    _get_report_articles,
    build_intelligence_export_data,
    export_report_csv,
    render_article_list_csv,
    render_article_list_xlsx,
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
    assert risk["critical_risk_count"] == 0
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
        "critical_risk_count": 2,
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
    assert "critical_risk_count,2" in csv_text
    assert "source_count,1" in csv_text
    assert "alert_count,1" in csv_text


@pytest.mark.asyncio
async def test_intelligence_export_uses_complete_filtered_processed_articles():
    article = SimpleNamespace(
        id=44,
        title="Security review",
        source_name="Example News",
        url="https://example.com/security-review",
        published_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        collected_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
    )
    triage = SimpleNamespace(
        company_id=3,
        company_name="Example Co",
        event_type="cybersecurity",
        summary="Landmark cybersecurity incident",
        why_it_matters="Affects customer data",
    )
    risk = SimpleNamespace(
        risk_level="critical",
        risk_score=82.0,
        monitoring_topic="cybersecurity",
    )
    insight = SimpleNamespace(
        headline="Security review",
        executive_summary="Stored risk analysis",
        updated_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
    )
    row = (article, triage, risk, insight, None, None)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(all=lambda: [row])),
        get=AsyncMock(return_value=SimpleNamespace(name="Example Co")),
    )

    report = await build_intelligence_export_data(
        db,
        company_id=3,
        start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
        snapshot_at=datetime(2026, 9, 30, tzinfo=timezone.utc),
        scope_metadata={
            "search_filter": "landmark",
            "risk_filter": "Critical Risk",
            "topic_filter": "Fraud Security",
        },
    )

    assert [item["article_id"] for item in report["articles"]] == [44]
    assert report["articles"][0]["risk_level"] == "critical"
    assert report["articles"][0]["sentiment"] is None
    assert report["articles"][0]["business_impact"] is None

    rows = list(csv.reader(io.StringIO(render_article_list_csv(report).decode("utf-8"))))
    assert len(rows) == 2
    assert rows[1][0] == "44"
    assert rows[1][1] == "Security review"
    assert rows[0][0] == "Article ID"


@pytest.mark.asyncio
async def test_intelligence_export_keeps_all_670_matching_articles_in_csv_and_xlsx():
    triage = SimpleNamespace(
        company_id=3,
        company_name="Example Co",
        event_type="incident",
        summary="Stored article triage",
        why_it_matters="Relevant to the organization",
    )
    risk = SimpleNamespace(
        risk_level="medium",
        risk_score=54.0,
        monitoring_topic="security",
    )
    insight = SimpleNamespace(
        headline="Analyzed headline",
        executive_summary="Stored risk analysis",
        updated_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
    )
    articles = [
        (
            SimpleNamespace(
                id=article_id,
                title=f"Analyzed article {article_id}",
                source_name="Example News",
                url=f"https://example.com/{article_id}",
                published_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
                collected_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
            ),
            triage,
            risk,
            insight,
            None,
            None,
        )
        for article_id in range(1, 671)
    ]
    db = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(all=lambda: articles)),
        get=AsyncMock(return_value=SimpleNamespace(name="Example Co")),
    )

    report = await build_intelligence_export_data(
        db,
        company_id=3,
        start_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
        snapshot_at=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )

    assert len(report["articles"]) == 670
    statement = db.execute.await_args.args[0]
    assert "LIMIT" not in str(statement).upper()
    csv_rows = list(csv.reader(io.StringIO(render_article_list_csv(report).decode("utf-8"))))
    assert len(csv_rows) == 671
    workbook = load_workbook(io.BytesIO(render_article_list_xlsx(report)), read_only=True)
    assert workbook.active.max_row == 671


@pytest.mark.asyncio
async def test_search_report_preserves_distinct_matching_article_ids():
    timestamp = datetime(2026, 9, 24, tzinfo=timezone.utc)
    matching_articles = [
        SimpleNamespace(
            id=article_id,
            external_id="shared-external-id",
            canonical_url="https://example.com/shared",
            url="https://example.com/shared",
            published_at=timestamp,
            collected_at=timestamp,
        )
        for article_id in (1001, 1002)
    ]
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: matching_articles)
            )
        )
    )

    result = await _get_report_articles(
        db,
        company_id=3,
        start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
        snapshot_at=datetime(2026, 9, 30, tzinfo=timezone.utc),
        report_scope="search_results",
        article_ids=[1001, 1002],
    )

    assert [article.id for article in result] == [1001, 1002]


@pytest.mark.asyncio
async def test_standard_report_does_not_filter_publishers_by_collector_names():
    article = SimpleNamespace(
        id=2048,
        external_id="publisher-item",
        canonical_url="https://example.com/article",
        url="https://example.com/article",
        source_name="Pypi.org",
        published_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        collected_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
    )
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: [article])
            )
        )
    )

    result = await _get_report_articles(
        db,
        company_id=3,
        start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
        snapshot_at=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )

    assert [row.id for row in result] == [2048]
    assert "articles.source_name in" not in str(db.execute.await_args.args[0]).lower()
