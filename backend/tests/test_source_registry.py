import pytest

from app.ingestion.collectors import (
    NewsAPICollector,
    RSSCollector,
)
from app.ingestion.sources import (
    NEWS_SOURCES,
    NewsSource,
    build_collector,
    get_enabled_sources,
    get_source,
)


def test_registry_contains_expected_sources():
    keys = {
        source.key
        for source in NEWS_SOURCES
    }

    assert keys == {
        "google_news_vee",
        "newsapi_vee",
    }


def test_get_source():
    source = get_source(
        "google_news_vee"
    )

    assert source is not None
    assert source.source_type == "rss"
    assert source.category == "company"


def test_get_enabled_sources():
    sources = get_enabled_sources()

    assert len(sources) == 2
    assert all(
        source.enabled
        for source in sources
    )


def test_build_rss_collector():
    source = NewsSource(
        key="rss_test",
        name="RSS Test",
        source_type="rss",
        url="https://example.com/feed.xml",
    )

    collector = build_collector(source)

    assert isinstance(
        collector,
        RSSCollector,
    )


def test_build_newsapi_collector():
    source = NewsSource(
        key="newsapi_test",
        name="NewsAPI Test",
        source_type="newsapi",
        query='"VEE Technologies"',
    )

    collector = build_collector(
        source,
        newsapi_api_key="test-key",
    )

    assert isinstance(
        collector,
        NewsAPICollector,
    )


def test_google_news_vee_source():
    source = get_source(
        "google_news_vee"
    )

    assert source is not None
    assert source.source_type == "rss"
    assert source.url is not None
    assert "news.google.com/rss/search" in source.url
    assert source.category == "company"


def test_newsapi_vee_source():
    source = get_source(
        "newsapi_vee"
    )

    assert source is not None
    assert source.source_type == "newsapi"
    assert source.query == "VEE Technologies"
    assert source.category == "company"


def test_rss_source_requires_url():
    source = NewsSource(
        key="bad_rss",
        name="Bad RSS",
        source_type="rss",
    )

    with pytest.raises(
        ValueError,
        match="requires a URL",
    ):
        build_collector(source)


def test_newsapi_source_requires_query():
    source = NewsSource(
        key="bad_newsapi",
        name="Bad NewsAPI",
        source_type="newsapi",
    )

    with pytest.raises(
        ValueError,
        match="requires a query",
    ):
        build_collector(
            source,
            newsapi_api_key="test-key",
        )


def test_newsapi_source_requires_api_key():
    source = NewsSource(
        key="newsapi_no_key",
        name="NewsAPI No Key",
        source_type="newsapi",
        query='"VEE Technologies"',
    )

    with pytest.raises(
        ValueError,
        match="API key is required",
    ):
        build_collector(source)

