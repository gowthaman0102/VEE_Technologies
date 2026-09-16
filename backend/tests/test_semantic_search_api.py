from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.v1 import semantic_search
from app.main import app
from app.services.semantic_search_service import (
    SemanticSearchResult,
)


client = TestClient(app)


def test_semantic_search_api(
    monkeypatch,
):
    search_mock = AsyncMock(
        return_value=[
            SemanticSearchResult(
                article_id=10,
                title="PayU faces RBI review",
                source_name="test-source",
                url="https://example.com/10",
                published_at=datetime(
                    2026,
                    9,
                    9,
                    tzinfo=timezone.utc,
                ),
                distance=0.10,
                similarity=0.90,
            ),
            SemanticSearchResult(
                article_id=11,
                title="India digital payments grow",
                source_name="test-source",
                url="https://example.com/11",
                published_at=None,
                distance=0.20,
                similarity=0.80,
            ),
        ]
    )

    monkeypatch.setattr(
        semantic_search,
        "semantic_search",
        search_mock,
    )

    response = client.post(
        "/api/v1/semantic-search?company_id=1",
        json={
            "query": "  PayU RBI regulation  ",
            "limit": 5,
            "minimum_similarity": 0.7,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "PayU RBI regulation"
    assert data["count"] == 2
    assert len(data["results"]) == 2

    assert data["results"][0]["article_id"] == 10
    assert data["results"][0]["similarity"] == 0.90

    args = search_mock.await_args.args
    kwargs = search_mock.await_args.kwargs

    assert args[1] == "  PayU RBI regulation  "
    assert kwargs["limit"] == 5
    assert kwargs["minimum_similarity"] == 0.7


def test_semantic_search_api_default_values(
    monkeypatch,
):
    search_mock = AsyncMock(
        return_value=[]
    )

    monkeypatch.setattr(
        semantic_search,
        "semantic_search",
        search_mock,
    )

    response = client.post(
        "/api/v1/semantic-search?company_id=1",
        json={
            "query": "PayU"
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0

    kwargs = search_mock.await_args.kwargs

    assert kwargs["limit"] == 10
    assert kwargs["minimum_similarity"] is None


def test_semantic_search_api_rejects_empty_query():
    response = client.post(
        "/api/v1/semantic-search?company_id=1",
        json={
            "query": ""
        },
    )

    assert response.status_code == 422


def test_semantic_search_api_rejects_limit_too_small():
    response = client.post(
        "/api/v1/semantic-search?company_id=1",
        json={
            "query": "PayU",
            "limit": 0,
        },
    )

    assert response.status_code == 422


def test_semantic_search_api_rejects_limit_too_large():
    response = client.post(
        "/api/v1/semantic-search?company_id=1",
        json={
            "query": "PayU",
            "limit": 101,
        },
    )

    assert response.status_code == 422


def test_semantic_search_api_rejects_similarity_above_one():
    response = client.post(
        "/api/v1/semantic-search?company_id=1",
        json={
            "query": "PayU",
            "minimum_similarity": 1.1,
        },
    )

    assert response.status_code == 422


def test_semantic_search_api_rejects_similarity_below_minus_one():
    response = client.post(
        "/api/v1/semantic-search?company_id=1",
        json={
            "query": "PayU",
            "minimum_similarity": -1.1,
        },
    )

    assert response.status_code == 422
