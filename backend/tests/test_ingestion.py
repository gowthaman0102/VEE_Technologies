from unittest.mock import AsyncMock

import httpx
import pytest

from app.ingestion.collectors.base import BaseCollector
from app.ingestion.runner import run_collector
from app.ingestion.types import CollectedArticle


class FakeCollector(BaseCollector):
    async def collect(self) -> list[CollectedArticle]:
        return [
            CollectedArticle(
                source_name="Test RSS",
                source_type="rss",
                external_id="article-001",
                title="PayU receives RBI approval",
                url="https://example.com/article-001",
                language="en",
            ),
            CollectedArticle(
                source_name="Test RSS",
                source_type="rss",
                external_id="article-002",
                title="PayU launches new payment product",
                url="https://example.com/article-002",
                language="en",
            ),
        ]


@pytest.mark.asyncio
async def test_fake_collector_returns_articles():
    collector = FakeCollector()

    articles = await collector.collect()

    assert len(articles) == 2
    assert articles[0].external_id == "article-001"
    assert articles[0].source_type == "rss"
    assert articles[1].external_id == "article-002"


@pytest.mark.asyncio
async def test_run_collector_counts_inserted_and_skipped(
    monkeypatch,
):
    collector = FakeCollector()

    save_mock = AsyncMock(
        side_effect=[
            (object(), True),
            (object(), False),
        ]
    )

    monkeypatch.setattr(
        "app.ingestion.runner.save_collected_article",
        save_mock,
    )

    db = AsyncMock()

    result = await run_collector(
        db,
        collector,
    )

    assert result.collected == 2
    assert result.inserted == 1
    assert result.skipped == 1
    assert save_mock.await_count == 2


@pytest.mark.asyncio
async def test_run_collector_respects_limit(
    monkeypatch,
):
    collector = FakeCollector()

    save_mock = AsyncMock(
        return_value=(object(), True)
    )

    monkeypatch.setattr(
        "app.ingestion.runner.save_collected_article",
        save_mock,
    )

    db = AsyncMock()

    result = await run_collector(
        db,
        collector,
        limit=1,
    )

    assert result.collected == 1
    assert result.inserted == 1
    assert result.skipped == 0
    assert save_mock.await_count == 1


@pytest.mark.asyncio
async def test_rss_collector_parses_valid_entries(
    monkeypatch,
):
    from app.ingestion.collectors.rss import RSSCollector

    rss_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example RSS</title>
    <link>https://example.com</link>
    <description>Example feed</description>
    <item>
      <guid>rss-001</guid>
      <title> PayU regulatory update </title>
      <link>https://example.com/rss-001</link>
      <author>Reporter</author>
      <description>Summary</description>
      <pubDate>Mon, 31 Aug 2026 06:18:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

    request = httpx.Request(
        "GET",
        "https://example.com/feed.xml",
    )

    response = httpx.Response(
        status_code=200,
        content=rss_xml,
        request=request,
    )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        AsyncMock(
            return_value=response
        ),
    )

    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source_name="Example RSS",
        language="en",
    )

    articles = await collector.collect()

    assert len(articles) == 1
    assert articles[0].external_id == "rss-001"
    assert (
        articles[0].title
        == "PayU regulatory update"
    )
    assert (
        articles[0].url
        == "https://example.com/rss-001"
    )
    assert articles[0].published_at is not None


@pytest.mark.asyncio
async def test_rss_collector_skips_invalid_entries(
    monkeypatch,
):
    from app.ingestion.collectors.rss import RSSCollector

    rss_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example RSS</title>
    <link>https://example.com</link>
    <description>Example feed</description>

    <item>
      <title></title>
      <link>https://example.com/missing-title</link>
    </item>

    <item>
      <title>Missing URL</title>
      <link></link>
    </item>

    <item>
      <title>Valid article</title>
      <link>https://example.com/valid</link>
    </item>
  </channel>
</rss>
"""

    request = httpx.Request(
        "GET",
        "https://example.com/feed.xml",
    )

    response = httpx.Response(
        status_code=200,
        content=rss_xml,
        request=request,
    )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        AsyncMock(
            return_value=response
        ),
    )

    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source_name="Example RSS",
    )

    articles = await collector.collect()

    assert len(articles) == 1
    assert articles[0].title == "Valid article"
    assert (
        articles[0].url
        == "https://example.com/valid"
    )
