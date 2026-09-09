import pytest

from app.ingestion.collectors.newsapi import NewsAPICollector


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeAsyncClient:
    payload = {}

    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.get("timeout")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def get(self, url, params=None):
        self.url = url
        self.params = params
        return FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_newsapi_collector_maps_articles(monkeypatch):
    FakeAsyncClient.payload = {
        "status": "ok",
        "totalResults": 1,
        "articles": [
            {
                "source": {
                    "id": None,
                    "name": "Example News",
                },
                "author": "Test Author",
                "title": "PayU receives regulatory approval",
                "description": "A test description",
                "url": "https://example.com/payu-approval",
                "publishedAt": "2026-09-09T10:30:00Z",
                "content": "Test article content",
            }
        ],
    }

    monkeypatch.setattr(
        "app.ingestion.collectors.newsapi.httpx.AsyncClient",
        FakeAsyncClient,
    )

    collector = NewsAPICollector(
        api_key="test-key",
        query="PayU India",
    )

    articles = await collector.collect()

    assert len(articles) == 1

    article = articles[0]

    assert article.source_name == "Example News"
    assert article.source_type == "newsapi"
    assert article.external_id == "https://example.com/payu-approval"
    assert article.title == "PayU receives regulatory approval"
    assert article.url == "https://example.com/payu-approval"
    assert article.author == "Test Author"
    assert article.description == "A test description"
    assert article.raw_content == "Test article content"
    assert article.language == "en"

    assert article.published_at is not None
    assert article.published_at.year == 2026
    assert article.published_at.month == 9
    assert article.published_at.day == 9


@pytest.mark.asyncio
async def test_newsapi_collector_skips_invalid_articles(monkeypatch):
    FakeAsyncClient.payload = {
        "status": "ok",
        "totalResults": 3,
        "articles": [
            {
                "source": {"name": "Valid News"},
                "author": None,
                "title": "Valid PayU article",
                "description": None,
                "url": "https://example.com/valid",
                "publishedAt": "2026-09-09T10:30:00Z",
                "content": None,
            },
            {
                "source": {"name": "Missing Title"},
                "title": "",
                "url": "https://example.com/no-title",
            },
            {
                "source": {"name": "Missing URL"},
                "title": "Article without URL",
                "url": "",
            },
        ],
    }

    monkeypatch.setattr(
        "app.ingestion.collectors.newsapi.httpx.AsyncClient",
        FakeAsyncClient,
    )

    collector = NewsAPICollector(
        api_key="test-key",
        query="PayU India",
    )

    articles = await collector.collect()

    assert len(articles) == 1
    assert articles[0].title == "Valid PayU article"


@pytest.mark.asyncio
async def test_newsapi_collector_handles_api_error(monkeypatch):
    FakeAsyncClient.payload = {
        "status": "error",
        "code": "apiKeyInvalid",
        "message": "API key is invalid",
    }

    monkeypatch.setattr(
        "app.ingestion.collectors.newsapi.httpx.AsyncClient",
        FakeAsyncClient,
    )

    collector = NewsAPICollector(
        api_key="test-key",
        query="PayU India",
    )

    with pytest.raises(
        RuntimeError,
        match="API key is invalid",
    ):
        await collector.collect()


def test_newsapi_collector_validates_configuration():
    with pytest.raises(
        ValueError,
        match="NewsAPI API key is required",
    ):
        NewsAPICollector(
            api_key="",
            query="PayU India",
        )

    with pytest.raises(
        ValueError,
        match="NewsAPI query is required",
    ):
        NewsAPICollector(
            api_key="test-key",
            query="",
        )


def test_newsapi_page_size_is_limited():
    collector = NewsAPICollector(
        api_key="test-key",
        query="PayU India",
        page_size=500,
    )

    assert collector.page_size == 100

    collector = NewsAPICollector(
        api_key="test-key",
        query="PayU India",
        page_size=0,
    )

    assert collector.page_size == 1
