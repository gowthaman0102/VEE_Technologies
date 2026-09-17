from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import report_service


START = datetime(
    2026,
    9,
    1,
    tzinfo=timezone.utc,
)

END = datetime(
    2026,
    9,
    2,
    tzinfo=timezone.utc,
)


def _zero_sentiment():
    return {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
    }


def _zero_risk():
    return {
        "average_risk_score": 0.0,
        "highest_risk_score": 0.0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
    }


def _zero_business():
    return {}


def _zero_events():
    return {
        "total_events": 0,
        "largest_events": [],
    }


def _patch_common_analytics(monkeypatch):
    monkeypatch.setattr(
        report_service,
        "get_sentiment_distribution",
        AsyncMock(
            return_value=_zero_sentiment()
        ),
    )

    monkeypatch.setattr(
        report_service,
        "get_risk_summary",
        AsyncMock(
            return_value=_zero_risk()
        ),
    )

    monkeypatch.setattr(
        report_service,
        "get_business_impact_distribution",
        AsyncMock(
            return_value=_zero_business()
        ),
    )

    monkeypatch.setattr(
        report_service,
        "get_event_summary",
        AsyncMock(
            return_value=_zero_events()
        ),
    )


@pytest.mark.asyncio
async def test_build_company_report_handles_zero_data_period(
    monkeypatch,
):
    db = AsyncMock()

    monkeypatch.setattr(
        report_service,
        "_get_company",
        AsyncMock(
            return_value=SimpleNamespace(
                id=2,
                name="VEE Technologies",
            )
        ),
    )

    monkeypatch.setattr(
        report_service,
        "_get_report_articles",
        AsyncMock(return_value=[]),
    )

    monkeypatch.setattr(
        report_service,
        "_fetch_by_article_ids",
        AsyncMock(return_value=[]),
    )

    monkeypatch.setattr(
        report_service,
        "_get_event_memberships",
        AsyncMock(
            return_value=({}, {})
        ),
    )

    monkeypatch.setattr(
        report_service,
        "_configured_competitor_names",
        AsyncMock(return_value=[]),
    )

    _patch_common_analytics(
        monkeypatch
    )

    report = await report_service.build_company_report(
        db,
        company_id=2,
        start_date=START,
        end_date=END,
    )

    assert report["company_id"] == 2
    assert report["company_name"] == (
        "VEE Technologies"
    )

    assert report["total_articles"] == 0
    assert report["total_events"] == 0
    assert report["articles"] == []
    assert report["sources"] == []
    assert report["competitors"] == []
    assert report["alerts"] == []
    assert report["highest_risk_stories"] == []

    assert report["sentiment_balance"] == {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
    }

    assert (
        "No qualifying media articles were found"
        in report["executive_summary"]
    )

    assert (
        "no media-driven sentiment"
        in report["executive_summary"]
    )


@pytest.mark.asyncio
async def test_report_summary_uses_only_configured_competitors(
    monkeypatch,
):
    db = AsyncMock()

    article = SimpleNamespace(
        id=1001,
        title="Market update",
        source_name="Test Source",
        url="https://example.com/article",
        published_at=datetime(
            2026,
            9,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        created_at=datetime(
            2026,
            9,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    competitor_mention = SimpleNamespace(
        article_id=1001,
        competitors=[
            "Configured Competitor",
            "Unconfigured Company",
        ],
    )

    monkeypatch.setattr(
        report_service,
        "_get_company",
        AsyncMock(
            return_value=SimpleNamespace(
                id=2,
                name="VEE Technologies",
            )
        ),
    )

    monkeypatch.setattr(
        report_service,
        "_get_report_articles",
        AsyncMock(
            return_value=[article]
        ),
    )

    fetch_mock = AsyncMock(
        side_effect=[
            [],                     # sentiment
            [],                     # business impact
            [competitor_mention],   # competitors
            [],                     # risk
            [],                     # risk insights
            [],                     # alerts
        ]
    )

    monkeypatch.setattr(
        report_service,
        "_fetch_by_article_ids",
        fetch_mock,
    )

    monkeypatch.setattr(
        report_service,
        "_get_event_memberships",
        AsyncMock(
            return_value=({}, {})
        ),
    )

    configured_mock = AsyncMock(
        return_value=[
            "Configured Competitor"
        ]
    )

    monkeypatch.setattr(
        report_service,
        "_configured_competitor_names",
        configured_mock,
    )

    _patch_common_analytics(
        monkeypatch
    )

    report = await report_service.build_company_report(
        db,
        company_id=2,
        start_date=START,
        end_date=END,
    )

    configured_mock.assert_awaited_once_with(
        db,
        2,
    )

    assert report["total_articles"] == 1
    assert len(report["competitors"]) == 1

    competitor_names = {
        item["name"]
        for item in report["competitors"]
    }

    assert competitor_names == {
        "Configured Competitor"
    }

    assert "Unconfigured Company" not in (
        competitor_names
    )
