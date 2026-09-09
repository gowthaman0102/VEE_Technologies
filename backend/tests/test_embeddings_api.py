from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.v1 import embeddings
from app.db.session import get_db
from app.main import app
from app.services.article_embedding_batch_service import (
    BatchEmbeddingResult,
)
from app.services.article_embedding_service import (
    ArticleEmbeddingResult,
)


client = TestClient(app)


def test_embed_single_article(
    monkeypatch,
):
    embed_mock = AsyncMock(
        return_value=ArticleEmbeddingResult(
            article_id=10,
            status="success",
            model="text-embedding-3-large",
            dimensions=1536,
        )
    )

    monkeypatch.setattr(
        embeddings,
        "embed_article_by_id",
        embed_mock,
    )

    response = client.post(
        "/api/v1/embeddings/articles/10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["article_id"] == 10
    assert data["status"] == "success"
    assert data["model"] == "text-embedding-3-large"
    assert data["dimensions"] == 1536
    assert data["error"] is None

    kwargs = embed_mock.await_args.kwargs

    assert kwargs["article_id"] == 10


def test_embed_missing_article(
    monkeypatch,
):
    embed_mock = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        embeddings,
        "embed_article_by_id",
        embed_mock,
    )

    response = client.post(
        "/api/v1/embeddings/articles/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Article not found"
    }


def test_embed_batch(
    monkeypatch,
):
    batch_mock = AsyncMock(
        return_value=BatchEmbeddingResult(
            selected=3,
            success=1,
            skipped=1,
            failed=1,
            results=[
                ArticleEmbeddingResult(
                    article_id=1,
                    status="success",
                    model="text-embedding-3-large",
                    dimensions=1536,
                ),
                ArticleEmbeddingResult(
                    article_id=2,
                    status="skipped",
                    error="Not eligible",
                ),
                ArticleEmbeddingResult(
                    article_id=3,
                    status="failed",
                    error="Provider failure",
                ),
            ],
        )
    )

    monkeypatch.setattr(
        embeddings,
        "process_embedding_batch",
        batch_mock,
    )

    response = client.post(
        "/api/v1/embeddings/batch",
        json={
            "limit": 3,
            "include_failed": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["selected"] == 3
    assert data["success"] == 1
    assert data["skipped"] == 1
    assert data["failed"] == 1
    assert len(data["results"]) == 3

    assert data["results"][0]["model"] == (
        "text-embedding-3-large"
    )

    kwargs = batch_mock.await_args.kwargs

    assert kwargs["limit"] == 3
    assert kwargs["include_failed"] is True


def test_embed_batch_limit_too_small():
    response = client.post(
        "/api/v1/embeddings/batch",
        json={
            "limit": 0
        },
    )

    assert response.status_code == 422


def test_embed_batch_limit_too_large():
    response = client.post(
        "/api/v1/embeddings/batch",
        json={
            "limit": 101
        },
    )

    assert response.status_code == 422


def test_embedding_status():
    db = AsyncMock()

    db.execute.return_value = SimpleNamespace(
        all=lambda: [
            ("pending", 30),
            ("success", 10),
            ("skipped", 4),
            ("failed", 2),
        ]
    )

    async def override_get_db():
        yield db

    app.dependency_overrides[
        get_db
    ] = override_get_db

    try:
        response = client.get(
            "/api/v1/embeddings/status"
        )
    finally:
        app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 200

    assert response.json() == {
        "pending": 30,
        "success": 10,
        "skipped": 4,
        "failed": 2,
        "total": 46,
    }

    db.execute.assert_awaited_once()
