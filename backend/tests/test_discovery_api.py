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


def test_event_clusters(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.discovery.list_event_clusters",
        AsyncMock(return_value=[]),
    )
    response = client.get("/api/v1/event-clusters?company_id=1")
    assert response.status_code == 200
    assert response.json() == {"count": 0, "items": []}
