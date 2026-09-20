from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_article_categories(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.article_settings.list_article_categories",
        AsyncMock(
            return_value={
                "count": 2,
                "items": [
                    {
                        "id": 1,
                        "company_id": 5,
                        "name": "Cybersecurity",
                        "priority": "medium",
                        "is_active": True,
                    },
                    {
                        "id": 2,
                        "company_id": 5,
                        "name": "AI Governance",
                        "priority": "medium",
                        "is_active": False,
                    },
                ],
            }
        ),
    )

    response = client.get("/api/v1/article-settings/categories?company_id=5")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["items"][0]["name"] == "Cybersecurity"


def test_create_article_category(monkeypatch):
    created = {
        "id": 10,
        "company_id": 5,
        "name": "Cybersecurity",
        "priority": "medium",
        "is_active": True,
    }

    monkeypatch.setattr(
        "app.api.v1.article_settings.create_article_category",
        AsyncMock(return_value=created),
    )

    response = client.post(
        "/api/v1/article-settings/categories",
        json={"company_id": 5, "name": "  cybersecurity  "},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Cybersecurity"


def test_create_article_category_rejects_duplicate(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.article_settings.create_article_category",
        AsyncMock(side_effect=ValueError("Category already exists.")),
    )

    response = client.post(
        "/api/v1/article-settings/categories",
        json={"company_id": 5, "name": "Cybersecurity"},
    )

    assert response.status_code == 409


def test_update_article_category_toggle(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.article_settings.update_article_category",
        AsyncMock(
            return_value={
                "id": 1,
                "company_id": 5,
                "name": "Cybersecurity",
                "priority": "medium",
                "is_active": False,
            }
        ),
    )

    response = client.patch(
        "/api/v1/article-settings/categories/1",
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_delete_article_category(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.article_settings.delete_article_category",
        AsyncMock(return_value=True),
    )

    response = client.delete("/api/v1/article-settings/categories/1")

    assert response.status_code == 200
    assert response.json()["deleted"] is True
