"""Unit tests for the health check endpoint."""

import pytest
from app.main import app
from app.config import settings


@pytest.mark.asyncio
async def test_health_check():
    """Test: GET /health returns expected status info."""
    # Use TestClient for this simple synchronous endpoint
    from fastapi.testclient import TestClient
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.APP_VERSION
    assert "debug" in data
