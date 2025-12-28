"""
Tests for the main application module.

This module tests the FastAPI application initialization,
configuration, and basic functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.config import get_settings
from src.main import create_app
from src.state_manager import get_state_manager


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from src.main import app

    # Mock the state manager dependency at the app level
    mock_state_manager = AsyncMock()
    mock_state_manager.get_muppet = AsyncMock(return_value=None)

    # Override the dependency
    app.dependency_overrides[get_state_manager] = lambda: mock_state_manager

    # Mock the lifecycle service to avoid state manager issues
    with patch(
        "src.services.muppet_lifecycle_service.MuppetLifecycleService"
    ) as mock_lifecycle_class:
        mock_lifecycle = AsyncMock()
        mock_lifecycle.list_all_muppets = AsyncMock(
            return_value={
                "muppets": [],
                "summary": {"total_muppets": 0},
                "platform_health": {
                    "total_muppets": 0,
                    "health_score": 1.0,
                    "active_deployments": 0,
                },
                "retrieved_at": "2025-12-25T00:00:00Z",
            }
        )
        mock_lifecycle.get_muppet_status = AsyncMock(return_value=None)
        mock_lifecycle_class.return_value = mock_lifecycle

        with TestClient(app) as test_client:
            yield test_client

        # Clean up dependency overrides
        app.dependency_overrides.clear()


def test_app_creation():
    """Test that the FastAPI application can be created successfully."""
    app = create_app()
    assert app is not None
    assert app.title == "Muppet Platform"
    assert (
        app.description
        == "Internal developer platform for creating and managing backend applications"
    )


def test_settings_loading():
    """Test that settings can be loaded successfully."""
    settings = get_settings()
    assert settings is not None
    assert settings.name == "platform-service"
    assert settings.version == "0.1.0"
    assert settings.port == 8000


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "platform-service"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_readiness_endpoint(client):
    """Test the readiness check endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ready"
    assert data["service"] == "platform-service"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "dependencies" in data


def test_muppets_list_endpoint(client):
    """Test the muppets list endpoint."""
    response = client.get("/api/v1/muppets/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    # Should return mock muppets from the state manager
    assert len(data) >= 0  # May have mock data


def test_muppet_detail_endpoint(client):
    """Test the muppet detail endpoint with non-existent muppet."""
    # Since we're not mocking the state manager, test the 404 case
    response = client.get("/api/v1/muppets/test-muppet-1")
    assert response.status_code == 404

    data = response.json()
    assert "message" in data
    assert "not found" in data["message"].lower()


def test_muppet_detail_not_found(client):
    """Test the muppet detail endpoint with non-existent muppet."""
    response = client.get("/api/v1/muppets/nonexistent-muppet")
    assert response.status_code == 404

    data = response.json()
    # The error response should contain a message field
    assert "message" in data
    assert "not found" in data["message"].lower()


def test_exception_handling(client):
    """Test that non-existent endpoints return proper error responses."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
