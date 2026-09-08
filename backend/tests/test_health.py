from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["application"] == "AI Media Intelligence"
    assert data["status"] == "running"
    assert data["version"] == "0.1.0"


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["application"] == "AI Media Intelligence"
    assert "timestamp" in data


def test_readiness_endpoint():
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert data["application"] == "AI Media Intelligence"


def test_openapi_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    data = response.json()

    assert data["info"]["title"] == "AI Media Intelligence"
