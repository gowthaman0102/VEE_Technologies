from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.v1 import articles
from app.main import app
from app.models.article import Article


client = TestClient(app)


def make_article(
    article_id: int = 1,
) -> Article:
    article = Article(
        id=article_id,
        source_name="Test News",
        source_type="rss",
        external_id=f"test-{article_id}",
        title="PayU test article",
        url=(
            "https://example.com/"
            f"article-{article_id}"
        ),
        author="Test Author",
        description="Test description",
        raw_content=None,
        language="en",
        extraction_status="pending",
        published_at=datetime(
            2026,
            9,
            9,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        collected_at=datetime(
            2026,
            9,
            9,
            10,
            5,
            tzinfo=timezone.utc,
        ),
    )

    return article


def test_list_articles(
    monkeypatch,
):
    article = make_article()

    list_mock = AsyncMock(
        return_value=[article]
    )

    monkeypatch.setattr(
        articles,
        "list_articles",
        list_mock,
    )

    response = client.get(
        "/api/v1/articles?limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["title"] == (
        "PayU test article"
    )
    assert data[0]["source_name"] == (
        "Test News"
    )

    list_mock.assert_awaited_once()

    assert (
        list_mock.await_args.kwargs["limit"]
        == 10
    )


def test_get_article(
    monkeypatch,
):
    article = make_article(
        article_id=25
    )

    get_mock = AsyncMock(
        return_value=article
    )

    monkeypatch.setattr(
        articles,
        "get_article",
        get_mock,
    )

    response = client.get(
        "/api/v1/articles/25"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 25
    assert data["external_id"] == "test-25"

    get_mock.assert_awaited_once()


def test_get_missing_article(
    monkeypatch,
):
    get_mock = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        articles,
        "get_article",
        get_mock,
    )

    response = client.get(
        "/api/v1/articles/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Article not found"
    }


def test_article_limit_too_small():
    response = client.get(
        "/api/v1/articles?limit=0"
    )

    assert response.status_code == 422


def test_article_limit_too_large():
    response = client.get(
        "/api/v1/articles?limit=501"
    )

    assert response.status_code == 422
