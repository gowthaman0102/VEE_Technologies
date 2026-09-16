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
