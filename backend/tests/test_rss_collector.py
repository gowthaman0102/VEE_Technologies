from unittest.mock import AsyncMock

import httpx
import pytest

from app.ingestion.collectors.rss import RSSCollector


RSS_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <description>Test RSS feed</description>
    <item>
      <guid>rss-001</guid>
      <title>PayU regulatory update</title>
      <link>https://example.com/rss-001</link>
      <description>Test summary</description>
      <pubDate>
        Mon, 31 Aug 2026 06:18:00 GMT
      </pubDate>
    </item>
  </channel>
</rss>
"""


def make_response(
    status_code: int = 200,
    content: bytes = RSS_XML,
) -> httpx.Response:
    request = httpx.Request(
        "GET",
        "https://example.com/feed.xml",
    )

    return httpx.Response(
        status_code=status_code,
        content=content,
        request=request,
    )


@pytest.mark.asyncio
async def test_rss_collector_fetches_and_parses(
    monkeypatch,
):
    response = make_response()

    get_mock = AsyncMock(
        return_value=response
    )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        get_mock,
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
    assert articles[0].source_type == "rss"
    assert articles[0].language == "en"

    get_mock.assert_awaited_once_with(
        "https://example.com/feed.xml"
    )


@pytest.mark.asyncio
async def test_rss_collector_raises_for_http_error(
    monkeypatch,
):
    response = make_response(
        status_code=503
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

    with pytest.raises(
        httpx.HTTPStatusError
    ):
        await collector.collect()


@pytest.mark.asyncio
async def test_rss_collector_propagates_timeout(
    monkeypatch,
):
    request = httpx.Request(
        "GET",
        "https://example.com/feed.xml",
    )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "get",
        AsyncMock(
            side_effect=httpx.ReadTimeout(
                "Feed request timed out",
                request=request,
            )
        ),
    )

    collector = RSSCollector(
        feed_url="https://example.com/feed.xml",
        source_name="Example RSS",
        timeout=5.0,
    )

    with pytest.raises(httpx.ReadTimeout):
        await collector.collect()


@pytest.mark.asyncio
async def test_rss_collector_empty_feed(
    monkeypatch,
):
    response = make_response(
        content=(
            b"<?xml version='1.0'?>"
            b"<rss version='2.0'>"
            b"<channel>"
            b"<title>Empty</title>"
            b"<link>https://example.com</link>"
            b"<description>Empty</description>"
            b"</channel>"
            b"</rss>"
        )
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

    assert articles == []


def test_rss_collector_validates_configuration():
    with pytest.raises(
        ValueError,
        match="feed URL",
    ):
        RSSCollector(
            feed_url="",
            source_name="Example RSS",
        )

    with pytest.raises(
        ValueError,
        match="source name",
    ):
        RSSCollector(
            feed_url="https://example.com/feed.xml",
            source_name="",
        )

    with pytest.raises(
        ValueError,
        match="timeout",
    ):
        RSSCollector(
            feed_url="https://example.com/feed.xml",
            source_name="Example RSS",
            timeout=0,
        )
