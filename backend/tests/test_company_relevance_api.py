from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.v1 import companies
from app.main import app
from app.services.company_relevance_service import (
    ArticleRelevanceResult,
    CompanyRelevanceResult,
)


client = TestClient(app)


def test_company_semantic_relevance_api(
    monkeypatch,
):
    relevance_mock = AsyncMock(
        return_value=CompanyRelevanceResult(
            company_id=1,
            company_name="PayU",
            threshold=0.65,
            context_text="Company: PayU",
            results=[
                ArticleRelevanceResult(
                    article_id=10,
                    title="PayU faces RBI review",
                    source_name="source-a",
                    url="https://example.com/10",
                    published_at=None,
                    distance=0.10,
                    similarity=0.90,
                    is_relevant=True,
                ),
                ArticleRelevanceResult(
                    article_id=11,
                    title="Other news",
                    source_name="source-b",
                    url="https://example.com/11",
                    published_at=None,
                    distance=0.55,
                    similarity=0.45,
                    is_relevant=False,
                ),
            ],
        )
    )

    monkeypatch.setattr(
        companies,
        "score_company_article_relevance",
        relevance_mock,
    )

    response = client.post(
        "/api/v1/companies/1/semantic-relevance",
        json={
            "limit": 25,
            "threshold": 0.65,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == 1
    assert data["company_name"] == "PayU"
    assert data["threshold"] == 0.65
    assert data["count"] == 2
    assert data["relevant_count"] == 1

    assert data["results"][0]["article_id"] == 10
    assert data["results"][0]["similarity"] == 0.90
    assert data["results"][0]["is_relevant"] is True

    kwargs = relevance_mock.await_args.kwargs

    assert kwargs["company_id"] == 1
    assert kwargs["limit"] == 25
    assert kwargs["threshold"] == 0.65


def test_company_semantic_relevance_defaults(
    monkeypatch,
):
    relevance_mock = AsyncMock(
        return_value=CompanyRelevanceResult(
            company_id=1,
            company_name="PayU",
            threshold=0.65,
            context_text="Company: PayU",
            results=[],
        )
    )

    monkeypatch.setattr(
        companies,
        "score_company_article_relevance",
        relevance_mock,
    )

    response = client.post(
        "/api/v1/companies/1/semantic-relevance",
        json={},
    )

    assert response.status_code == 200

    kwargs = relevance_mock.await_args.kwargs

    assert kwargs["limit"] == 50
    assert kwargs["threshold"] is None


def test_company_semantic_relevance_missing_company(
    monkeypatch,
):
    relevance_mock = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        companies,
        "score_company_article_relevance",
        relevance_mock,
    )

    response = client.post(
        "/api/v1/companies/999/semantic-relevance",
        json={},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Company not found."
    }


def test_company_semantic_relevance_rejects_small_limit():
    response = client.post(
        "/api/v1/companies/1/semantic-relevance",
        json={
            "limit": 0
        },
    )

    assert response.status_code == 422


def test_company_semantic_relevance_rejects_large_limit():
    response = client.post(
        "/api/v1/companies/1/semantic-relevance",
        json={
            "limit": 101
        },
    )

    assert response.status_code == 422


def test_company_semantic_relevance_rejects_high_threshold():
    response = client.post(
        "/api/v1/companies/1/semantic-relevance",
        json={
            "threshold": 1.1
        },
    )

    assert response.status_code == 422


def test_company_semantic_relevance_rejects_low_threshold():
    response = client.post(
        "/api/v1/companies/1/semantic-relevance",
        json={
            "threshold": -1.1
        },
    )

    assert response.status_code == 422
