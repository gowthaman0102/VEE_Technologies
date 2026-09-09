from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.v1 import processing
from app.main import app
from app.services.article_batch_processing_service import (
    BatchProcessingResult,
)
from app.services.article_processing_service import (
    ArticleProcessingResult,
)


client = TestClient(app)


def test_process_single_article(
    monkeypatch,
):
    process_mock = AsyncMock(
        return_value=ArticleProcessingResult(
            article_id=10,
            status="success",
            content_hash="a" * 64,
        )
    )

    monkeypatch.setattr(
        processing,
        "process_article_by_id",
        process_mock,
    )

    response = client.post(
        "/api/v1/processing/articles/10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["article_id"] == 10
    assert data["status"] == "success"
    assert data["content_hash"] == "a" * 64
    assert data["duplicate_of_id"] is None
    assert data["error"] is None

    process_mock.assert_awaited_once()


def test_process_missing_article(
    monkeypatch,
):
    process_mock = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        processing,
        "process_article_by_id",
        process_mock,
    )

    response = client.post(
        "/api/v1/processing/articles/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Article not found"
    }


def test_process_batch(
    monkeypatch,
):
    batch_mock = AsyncMock(
        return_value=BatchProcessingResult(
            selected=3,
            success=1,
            skipped=1,
            failed=1,
            results=[
                ArticleProcessingResult(
                    article_id=1,
                    status="success",
                ),
                ArticleProcessingResult(
                    article_id=2,
                    status="skipped",
                    duplicate_of_id=1,
                ),
                ArticleProcessingResult(
                    article_id=3,
                    status="failed",
                    error="fetch failed",
                ),
            ],
        )
    )

    monkeypatch.setattr(
        processing,
        "process_articles_batch",
        batch_mock,
    )

    response = client.post(
        "/api/v1/processing/batch",
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

    kwargs = batch_mock.await_args.kwargs

    assert kwargs["limit"] == 3
    assert kwargs["include_failed"] is True


def test_process_batch_limit_too_small():
    response = client.post(
        "/api/v1/processing/batch",
        json={
            "limit": 0
        },
    )

    assert response.status_code == 422


def test_process_batch_limit_too_large():
    response = client.post(
        "/api/v1/processing/batch",
        json={
            "limit": 101
        },
    )

    assert response.status_code == 422
