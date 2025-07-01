import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Market Analysis API", "version": "1.0.0"}


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_articles_empty(client: TestClient):
    response = client.get("/api/v1/articles")
    assert response.status_code == 200
    assert response.json() == []


def test_get_positions_empty(client: TestClient):
    response = client.get("/api/v1/positions")
    assert response.status_code == 200
    assert response.json() == []


def test_start_analysis_requires_auth(client: TestClient):
    # This test assumes you'll add authentication later
    response = client.post("/api/v1/analysis/start", json={
        "max_positions": 5,
        "min_confidence": 0.8,
        "llm_model": "gpt-4-turbo-preview",
        "sources": ["finviz"]
    })
    # Should work without auth for now, but will return session_id
    assert response.status_code == 200
    assert "session_id" in response.json()