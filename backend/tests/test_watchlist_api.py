from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_watchlist(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.watchlist.list_watchlist_items",
        AsyncMock(
            return_value={
                "count": 2,
                "items": [
                    {
                        "id": 1,
                        "company_id": 5,
                        "item_type": "keyword",
                        "item_name": "PayU",
                        "value": "PayU",
                        "is_active": True,
                    },
                    {
                        "id": 2,
                        "company_id": 5,
                        "item_type": "regulator",
                        "item_name": "RBI",
                        "value": "Reserve Bank of India",
                        "is_active": True,
                    },
                ],
            }
        ),
    )

    response = client.get("/api/v1/watchlist?company_id=5")

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert response.json()["items"][0]["item_name"] == "PayU"


def test_create_watchlist_item(monkeypatch):
    created = {
        "id": 10,
        "company_id": 5,
        "item_type": "keyword",
        "item_name": "RBI",
        "value": "RBI",
        "is_active": True,
    }

    monkeypatch.setattr(
        "app.api.v1.watchlist.create_watchlist_item",
        AsyncMock(return_value=created),
    )

    response = client.post(
        "/api/v1/watchlist",
        json={
            "company_id": 5,
            "item_type": "keyword",
            "item_name": "RBI",
            "value": "RBI",
        },
    )

    assert response.status_code == 201
    assert response.json()["item_name"] == "RBI"


def test_delete_watchlist_item(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.watchlist.delete_watchlist_item",
        AsyncMock(return_value=True),
    )

    response = client.delete("/api/v1/watchlist/10")

    assert response.status_code == 200
    assert response.json()["deleted"] is True

def test_get_watchlist_matches(monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace

    match_mock = AsyncMock(
        return_value=[
            SimpleNamespace(
                watchlist_item_id=4,
                item_type="risk_category",
                item_name="High Risk",
                value="high",
                article_id=20,
                title="Regulatory scrutiny increases",
                source_name="Reuters",
                url="https://example.com/20",
                published_at=datetime(
                    2026,
                    9,
                    10,
                    tzinfo=timezone.utc,
                ),
                event_type="regulatory_action",
                monitoring_topic="payments regulation",
                risk_level="high",
                risk_score=87.5,
                business_impact="regulatory",
            )
        ]
    )

    monkeypatch.setattr(
        "app.api.v1.watchlist.match_watchlist_items",
        match_mock,
    )

    response = client.get(
        (
            "/api/v1/watchlist/matches"
            "?company_id=2"
            "&limit=50"
        )
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1
    assert len(data["matches"]) == 1

    match = data["matches"][0]

    assert match["watchlist_item_id"] == 4
    assert match["article_id"] == 20
    assert match["risk_level"] == "high"
    assert match["risk_score"] == 87.5
    assert match["business_impact"] == "regulatory"

    kwargs = match_mock.await_args.kwargs

    assert kwargs["company_id"] == 2
    assert kwargs["limit"] == 50


def test_get_watchlist_matches_passes_time_window(
    monkeypatch,
):
    match_mock = AsyncMock(return_value=[])

    monkeypatch.setattr(
        "app.api.v1.watchlist.match_watchlist_items",
        match_mock,
    )

    response = client.get(
        (
            "/api/v1/watchlist/matches"
            "?company_id=2"
            "&start=2026-09-01T00:00:00Z"
            "&end=2026-09-17T00:00:00Z"
        )
    )

    assert response.status_code == 200

    kwargs = match_mock.await_args.kwargs

    assert kwargs["start"] is not None
    assert kwargs["end"] is not None


def test_get_watchlist_matches_rejects_invalid_time_window(
    monkeypatch,
):
    match_mock = AsyncMock(return_value=[])

    monkeypatch.setattr(
        "app.api.v1.watchlist.match_watchlist_items",
        match_mock,
    )

    response = client.get(
        (
            "/api/v1/watchlist/matches"
            "?company_id=2"
            "&start=2026-09-17T00:00:00Z"
            "&end=2026-09-01T00:00:00Z"
        )
    )

    assert response.status_code == 422
    match_mock.assert_not_awaited()
