from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.v1 import ingestion
from app.ingestion.multi_runner import SourceIngestionResult
from app.main import app


client = TestClient(app)


def test_list_ingestion_sources():
    response = client.get(
        "/api/v1/ingestion/sources"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    keys = {
        source["key"]
        for source in data
    }

    assert keys == {
        "google_news_vee",
        "newsapi_vee",
    }


def test_run_selected_sources(
    monkeypatch,
):
    run_mock = AsyncMock(
        return_value=[
            SourceIngestionResult(
                source_key="google_news_vee",
                source_name=(
                    "Google News - VEE Technologies"
                ),
                collected=3,
                inserted=1,
                skipped=2,
            )
        ]
    )

    monkeypatch.setattr(
        ingestion,
        "run_sources",
        run_mock,
    )

    response = client.post(
        "/api/v1/ingestion/run",
        json={
            "source_keys": [
                "google_news_vee"
            ],
            "per_source_limit": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_collected"] == 3
    assert data["total_inserted"] == 1
    assert data["total_skipped"] == 2
    assert data["failures"] == 0
    assert len(data["sources"]) == 1

    assert (
        data["sources"][0]["source_key"]
        == "google_news_vee"
    )

    run_mock.assert_awaited_once()


def test_run_unknown_source():
    response = client.post(
        "/api/v1/ingestion/run",
        json={
            "source_keys": [
                "does_not_exist"
            ],
            "per_source_limit": 3,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Unknown source: does_not_exist"
    )


def test_run_single_source(
    monkeypatch,
):
    run_mock = AsyncMock(
        return_value=[
            SourceIngestionResult(
                source_key="newsapi_vee",
                source_name=(
                    "NewsAPI - VEE Technologies"
                ),
                collected=2,
                inserted=0,
                skipped=2,
            )
        ]
    )

    monkeypatch.setattr(
        ingestion,
        "run_sources",
        run_mock,
    )

    response = client.post(
        "/api/v1/ingestion/run/"
        "newsapi_vee",
        json={
            "per_source_limit": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_collected"] == 2
    assert data["total_inserted"] == 0
    assert data["total_skipped"] == 2
    assert data["failures"] == 0


def test_run_single_unknown_source():
    response = client.post(
        "/api/v1/ingestion/run/"
        "does_not_exist",
        json={
            "per_source_limit": 2,
        },
    )

    assert response.status_code == 404


def test_ingestion_limit_validation():
    response = client.post(
        "/api/v1/ingestion/run",
        json={
            "per_source_limit": 0,
        },
    )

    assert response.status_code == 422
