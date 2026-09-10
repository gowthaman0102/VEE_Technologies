from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.article_triage import ArticleTriageResult
from app.services.article_triage_service import ArticleNotFoundError, CompanyNotFoundError


client = TestClient(app)


def make_service_result():
    return SimpleNamespace(
        article_id=8,
        model="test-llm",
        triage=ArticleTriageResult(
            company_name="PayU",
            event_type="regulatory_action",
            summary="PayU received RBI approval.",
            why_it_matters=(
                "The approval supports regulated operations."
            ),
            evidence=[
                "RBI granted final approval."
            ],
            potential_impact=(
                "PayU can expand payment services."
            ),
            urgency="high",
            confidence=0.9,
        ),
    )


def make_stored_record():
    now = datetime(
        2026,
        9,
        10,
        14,
        30,
        tzinfo=timezone.utc,
    )

    return SimpleNamespace(
        id=1,
        article_id=8,
        company_id=1,
        company_name="PayU",
        event_type="regulatory_action",
        summary="PayU received RBI approval.",
        why_it_matters=(
            "The approval supports regulated operations."
        ),
        evidence=[
            "RBI granted final approval."
        ],
        potential_impact=(
            "PayU can expand payment services."
        ),
        urgency="high",
        confidence=0.9,
        llm_model="test-llm",
        created_at=now,
        updated_at=now,
    )


def test_triage_api_success(monkeypatch):
    service_mock = AsyncMock(
        return_value=make_service_result()
    )

    monkeypatch.setattr(
        "app.api.v1.triage.triage_article",
        service_mock,
    )

    response = client.post(
        "/api/v1/triage/articles/8",
        json={
            "company_id": 1
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["article_id"] == 8
    assert data["model"] == "test-llm"
    assert data["triage"]["company_name"] == "PayU"
    assert (
        data["triage"]["event_type"]
        == "regulatory_action"
    )
    assert data["triage"]["urgency"] == "high"
    assert data["triage"]["confidence"] == 0.9


def test_triage_api_not_found(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.triage.triage_article",
        AsyncMock(
            side_effect=ArticleNotFoundError(
                "Article 999 not found."
            )
        ),
    )

    response = client.post(
        "/api/v1/triage/articles/999",
        json={
            "company_id": 1
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Article 999 not found."
    )


def test_triage_api_validation_error(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.triage.triage_article",
        AsyncMock(
            side_effect=ValueError(
                "LLM returned invalid JSON."
            )
        ),
    )

    response = client.post(
        "/api/v1/triage/articles/8",
        json={
            "company_id": 1
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "LLM returned invalid JSON."
    )


def test_triage_api_rejects_invalid_company_id():
    response = client.post(
        "/api/v1/triage/articles/8",
        json={
            "company_id": 0
        },
    )

    assert response.status_code == 422


def test_get_stored_triage_success(monkeypatch):
    read_mock = AsyncMock(
        return_value=make_stored_record()
    )

    monkeypatch.setattr(
        "app.api.v1.triage.get_article_triage",
        read_mock,
    )

    response = client.get(
        "/api/v1/triage/articles/8",
        params={
            "company_id": 1
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["article_id"] == 8
    assert data["company_id"] == 1
    assert data["company_name"] == "PayU"
    assert data["event_type"] == "regulatory_action"
    assert data["urgency"] == "high"
    assert data["confidence"] == 0.9
    assert data["llm_model"] == "test-llm"


def test_get_stored_triage_not_found(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.triage.get_article_triage",
        AsyncMock(return_value=None),
    )

    response = client.get(
        "/api/v1/triage/articles/999",
        params={
            "company_id": 1
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Stored triage result not found."
    )


def test_get_stored_triage_requires_company_id():
    response = client.get(
        "/api/v1/triage/articles/8"
    )

    assert response.status_code == 422

def test_triage_api_company_not_found(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.triage.triage_article",
        AsyncMock(
            side_effect=CompanyNotFoundError(
                "Company 999 not found."
            )
        ),
    )

    response = client.post(
        "/api/v1/triage/articles/8",
        json={
            "company_id": 999
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Company 999 not found."
    )


def test_batch_triage_api_company_not_found(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.v1.triage.triage_articles_batch",
        AsyncMock(
            side_effect=CompanyNotFoundError(
                "Company 999 not found."
            )
        ),
    )

    response = client.post(
        "/api/v1/triage/batch",
        json={
            "company_id": 999,
            "article_ids": [8, 5],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Company 999 not found."
    )
