from datetime import datetime, timedelta, timezone

import pytest

from app.services.analytics_service import (
    _publisher_domain_from_urls,
    get_source_summary,
    validate_time_window,
)


def test_validate_time_window_rejects_invalid_range():
    start = datetime.now(timezone.utc)
    end = start - timedelta(days=1)

    with pytest.raises(ValueError, match="start.*end|end.*start"):
        validate_time_window(start, end)


def test_validate_time_window_accepts_valid_range():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    end = now - timedelta(days=2)

    validated_start, validated_end = validate_time_window(start, end)

    assert validated_start == start
    assert validated_end == end


def test_publisher_domain_prefers_canonical_article_host():
    domain = _publisher_domain_from_urls(
        "https://news.google.com/rss/articles/123",
        "https://www.thenextweb.com/news/example-story",
    )

    assert domain == "thenextweb.com"


def test_publisher_domain_ignores_google_news_when_no_canonical_url():
    domain = _publisher_domain_from_urls(
        "https://news.google.com/rss/articles/123",
        None,
    )

    assert domain is None


@pytest.mark.asyncio
async def test_source_summary_deduplicates_articles_and_returns_risk_breakdown():
    class Result:
        def all(self):
            return [
                (
                    1,
                    "The Next Web",
                    "https://news.google.com/rss/articles/1",
                    "https://thenextweb.com/news/first-story",
                    "positive",
                    20,
                    "low",
                    10,
                ),
                (
                    1,
                    "The Next Web",
                    "https://news.google.com/rss/articles/1",
                    "https://thenextweb.com/news/first-story",
                    "positive",
                    20,
                    "low",
                    11,
                ),
                (
                    2,
                    "The Next Web",
                    "https://www.thenextweb.com/news/second-story",
                    None,
                    "neutral",
                    30,
                    "medium",
                    None,
                ),
            ]

    class Database:
        async def execute(self, _statement):
            return Result()

    now = datetime.now(timezone.utc)
    summary = await get_source_summary(
        Database(),
        company_id=1,
        start=now - timedelta(days=1),
        end=now,
    )

    assert summary["sources"][0]["publisher_domain"] == "thenextweb.com"
    assert summary["sources"][0]["article_count"] == 2
    assert summary["sources"][0]["risk_assessed_count"] == 2
    assert summary["sources"][0]["average_risk_score"] == 25
    assert summary["sources"][0]["critical_risk_count"] == 0
    assert summary["sources"][0]["high_risk_count"] == 0
    assert summary["sources"][0]["medium_risk_count"] == 1
    assert summary["sources"][0]["low_risk_count"] == 1
