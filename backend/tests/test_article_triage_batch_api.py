from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.article_triage import ArticleTriageResult


client = TestClient(app)


def make_triage_result(article_id: int):
    return SimpleNamespace(
        article_id=article_id,
        model="test-llm",
        triage=ArticleTriageResult(
            company_name="PayU",
            event_type="regulatory_action",
            summary="PayU received RBI approval.",
            why_it_matters="This supports regulated operations.",
            evidence=[
                "RBI granted final approval."
            ],
            potential_impact="PayU can expand operations.",
            urgency="high",
            confidence=0.9,
        ),
    )


def test_batch_triage_api_success(monkeypatch):
    batch_result = SimpleNamespace(
        company_id=1,
        requested_count=2,
        success_count=2,
        not_found_count=0,
        failed_count=0,
        items=[
            SimpleNamespace(
                article_id=8,
                status="success",
                result=make_triage_result(8),
                error=None,
            ),
            SimpleNamespace(
                article_id=5,
                status="success",
                result=make_triage_result(5),
                error=None,
            ),
        ],
    )

    monkeypatch.setattr(
        "app.api.v1.triage.triage_articles_batch",
        AsyncMock(return_value=batch_result),
    )

    response = client.post(
        "/api/v1/triage/batch",
        json={
            "company_id": 1,
            "article_ids": [8, 5],
            "rag_limit": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == 1
    assert data["requested_count"] == 2
    assert data["success_count"] == 2
    assert data["failed_count"] == 0
    assert len(data["items"]) == 2
    assert data["items"][0]["status"] == "success"


def test_batch_triage_api_mixed_results(monkeypatch):
    batch_result = SimpleNamespace(
        company_id=1,
        requested_count=3,
        success_count=1,
        not_found_count=1,
        failed_count=1,
        items=[
            SimpleNamespace(
                article_id=8,
                status="success",
                result=make_triage_result(8),
                error=None,
            ),
            SimpleNamespace(
                article_id=999,
                status="not_found",
                result=None,
                error=None,
            ),
            SimpleNamespace(
                article_id=5,
                status="failed",
                result=None,
                error="LLM returned invalid JSON.",
            ),
        ],
    )

    monkeypatch.setattr(
        "app.api.v1.triage.triage_articles_batch",
        AsyncMock(return_value=batch_result),
    )

    response = client.post(
        "/api/v1/triage/batch",
        json={
            "company_id": 1,
            "article_ids": [8, 999, 5],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success_count"] == 1
    assert data["not_found_count"] == 1
    assert data["failed_count"] == 1

    assert data["items"][1]["status"] == "not_found"
    assert data["items"][2]["status"] == "failed"
    assert (
        data["items"][2]["error"]
        == "LLM returned invalid JSON."
    )


def test_batch_triage_api_rejects_empty_ids():
    response = client.post(
        "/api/v1/triage/batch",
        json={
            "company_id": 1,
            "article_ids": [],
        },
    )

    assert response.status_code == 422


def test_batch_triage_api_rejects_invalid_company():
    response = client.post(
        "/api/v1/triage/batch",
        json={
            "company_id": 0,
            "article_ids": [8],
        },
    )

    assert response.status_code == 422


def test_batch_triage_api_rejects_invalid_rag_limit():
    response = client.post(
        "/api/v1/triage/batch",
        json={
            "company_id": 1,
            "article_ids": [8],
            "rag_limit": 0,
        },
    )

    assert response.status_code == 422
