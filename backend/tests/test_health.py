from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health_endpoint() -> None:
    """Verify that GET /health returns 200 OK and valid health metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data
    assert "timestamp" in data


def test_database_health_endpoint() -> None:
    """Verify that GET /health/db verifies live database connectivity."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["connected"] is True
    assert "database" in data
    assert "latency_ms" in data
    assert data["latency_ms"] >= 0.0


def test_v1_api_health_endpoints() -> None:
    """Verify that versioned API routes /api/v1/health work seamlessly."""
    response_health = client.get("/api/v1/health")
    assert response_health.status_code == 200
    assert response_health.json()["status"] == "ok"

    response_db = client.get("/api/v1/health/db")
    assert response_db.status_code == 200
    assert response_db.json()["connected"] is True


def test_openapi_documentation_endpoint() -> None:
    """Verify that the OpenAPI JSON schema is generated and accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "/health" in data["paths"]
    assert "/health/db" in data["paths"]
