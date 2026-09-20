from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_keyword_search(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.discovery.keyword_search",
        AsyncMock(return_value=[]),
    )
    response = client.get("/api/v1/search/keyword?q=regulatory&company_id=1")
    assert response.status_code == 200
    assert response.json() == {
        "query": "regulatory",
        "count": 0,
        "results": [],
    }


def test_keyword_search_passes_filters(monkeypatch):
    search_mock = AsyncMock(return_value=[])

    monkeypatch.setattr(
        "app.api.v1.discovery.keyword_search",
        search_mock,
    )

    response = client.get(
        "/api/v1/search/keyword"
        "?q=regulatory"
        "&company_id=2"
        "&start=2026-09-01T00:00:00Z"
        "&end=2026-09-17T00:00:00Z"
        "&source_name=Reuters"
        "&sentiment=negative"
        "&risk_level=high"
        "&business_impact=regulatory"
        "&event_type=enforcement"
        "&event_cluster_id=7"
    )

    assert response.status_code == 200

    kwargs = search_mock.await_args.kwargs
    filters = kwargs["filters"]

    assert filters.source_name == "Reuters"
    assert filters.sentiment == "negative"
    assert filters.risk_level == "high"
    assert filters.business_impact == "regulatory"
    assert filters.event_type == "enforcement"
    assert filters.event_cluster_id == 7
    assert filters.start is not None
    assert filters.end is not None


def test_keyword_search_rejects_invalid_time_window(monkeypatch):
    search_mock = AsyncMock(return_value=[])

    monkeypatch.setattr(
        "app.api.v1.discovery.keyword_search",
        search_mock,
    )

    response = client.get(
        "/api/v1/search/keyword"
        "?q=regulatory"
        "&company_id=2"
        "&start=2026-09-17T00:00:00Z"
        "&end=2026-09-01T00:00:00Z"
    )

    assert response.status_code == 422
    search_mock.assert_not_awaited()

def test_keyword_search_returns_enriched_api_fields(
    monkeypatch,
):
    from app.services.discovery_service import KeywordSearchItem

    monkeypatch.setattr(
        "app.api.v1.discovery.keyword_search",
        AsyncMock(
            return_value=[
                KeywordSearchItem(
                    article_id=10,
                    title="RBI regulatory update",
                    publisher_name="Reuters",
                    source_name="Reuters",
                    url="https://example.com/10",
                    published_at=None,
                    collected_at=None,
                    event_type="regulatory_action",
                    sentiment="negative",
                    risk_level="high",
                    risk_score=82.5,
                    business_impact="regulatory",
                    event_cluster_id=7,
                )
            ]
        ),
    )

    response = client.get(
        "/api/v1/search/keyword"
        "?q=regulatory"
        "&company_id=2"
    )

    assert response.status_code == 200

    result = response.json()["results"][0]

    assert result["article_id"] == 10
    assert result["event_type"] == "regulatory_action"
    assert result["sentiment"] == "negative"
    assert result["risk_level"] == "high"
    assert result["risk_score"] == 82.5
    assert result["business_impact"] == "regulatory"
    assert result["event_cluster_id"] == 7
