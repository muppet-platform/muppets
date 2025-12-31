"""
Integration tests for Fargate deployment system.

Tests the complete integration between deployment service, infrastructure manager,
and API endpoints for muppet deployment to AWS Fargate.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.managers.infrastructure_manager import DeploymentState, DeploymentStatus
from src.models import Muppet, MuppetStatus
from src.services.deployment_service import DeploymentService
from src.state_manager import get_state_manager


@asynccontextmanager
async def mock_lifespan(app):
    """Mock lifespan context manager for testing."""
    # Mock startup
    app.state.github_client = AsyncMock()
    app.state.state_manager = AsyncMock()
    yield
    # Mock shutdown


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    return AsyncMock()


@pytest.fixture
def mock_deployment_service():
    """Create a mock deployment service."""
    return AsyncMock(spec=DeploymentService)


@pytest.fixture
def mock_lifecycle_service():
    """Create a mock lifecycle service."""
    return AsyncMock()


@pytest.fixture
def app(mock_state_manager, mock_deployment_service, mock_lifecycle_service):
    """Create FastAPI app for testing with mocked dependencies."""
    # Create app without lifespan to avoid AWS client initialization
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse

    from src.exceptions import PlatformException
    from src.routers import health, muppets

    app = FastAPI(
        title="Muppet Platform",
        description="Internal developer platform for creating and managing backend applications",
        version="0.1.0",
        lifespan=mock_lifespan,
    )

    # Add CORS middleware
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        health.router, tags=["health"]
    )  # Remove prefix to match main app
    app.include_router(muppets.router, prefix="/api/v1/muppets", tags=["muppets"])

    # Override dependencies
    def override_get_state_manager():
        return mock_state_manager

    def override_get_deployment_service():
        return mock_deployment_service

    def override_get_lifecycle_service():
        return mock_lifecycle_service

    app.dependency_overrides[get_state_manager] = override_get_state_manager
    app.dependency_overrides[
        muppets.get_deployment_service
    ] = override_get_deployment_service
    app.dependency_overrides[
        muppets.get_lifecycle_service
    ] = override_get_lifecycle_service

    # Global exception handlers
    @app.exception_handler(PlatformException)
    async def platform_exception_handler(request, exc: PlatformException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_type,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP_ERROR", "message": exc.detail, "details": None},
        )

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_muppet():
    """Create a mock muppet for testing."""
    return Muppet(
        name="test-integration-muppet",
        template="java-micronaut",
        status=MuppetStatus.RUNNING,
        github_repo_url="https://github.com/muppet-platform/test-integration-muppet",
        fargate_service_arn="arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-integration-muppet",
        port=3000,
    )


@pytest.fixture
def mock_deployment_state():
    """Create a mock successful deployment state."""
    return DeploymentState(
        muppet_name="test-integration-muppet",
        status=DeploymentStatus.COMPLETED,
        terraform_workspace="/tmp/test-workspace",
        state_backend="local",
        last_operation=None,
        last_updated="2023-01-01T00:00:00Z",
        outputs={
            "service_arn": "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-integration-muppet",
            "service_url": "http://test-lb.amazonaws.com",
            "load_balancer_dns_name": "test-lb.amazonaws.com",
            "cluster_name": "test-cluster",
            "task_definition_arn": "arn:aws:ecs:us-east-1:123456789012:task-definition/test-integration-muppet:1",
            "log_group_name": "/aws/fargate/test-integration-muppet",
        },
    )


class TestFargateDeploymentIntegration:
    """Integration tests for Fargate deployment system."""

    def test_health_endpoint(self, client):
        """Test that the health endpoint works."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_list_muppets_endpoint(self, client, mock_lifecycle_service, mock_muppet):
        """Test the list muppets endpoint."""
        # Configure mock lifecycle service
        mock_lifecycle_service.list_all_muppets.return_value = {
            "muppets": [
                {
                    "name": "test-integration-muppet",
                    "template": "java-micronaut",
                    "status": "running",
                    "github_repo_url": "https://github.com/muppet-platform/test-integration-muppet",
                    # Remove Z suffix for fromisoformat compatibility
                    "created_at": "2023-01-01T00:00:00",
                    "fargate_service_arn": "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-integration-muppet",
                }
            ]
        }

        response = client.get("/api/v1/muppets/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-integration-muppet"
        assert data[0]["template"] == "java-micronaut"
        assert data[0]["status"] == "running"

    def test_get_muppet_endpoint(self, client, mock_state_manager, mock_muppet):
        """Test the get muppet details endpoint."""
        # Configure mock state manager
        mock_state_manager.get_muppet.return_value = mock_muppet

        response = client.get("/api/v1/muppets/test-integration-muppet")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "test-integration-muppet"
        assert data["template"] == "java-micronaut"
        assert data["status"] == "running"
        assert data["fargate_service_arn"] == mock_muppet.fargate_service_arn

    def test_deploy_muppet_endpoint(
        self, client, mock_state_manager, mock_deployment_service, mock_muppet
    ):
        """Test the deploy muppet endpoint."""
        # Configure mock state manager
        mock_state_manager.get_muppet.return_value = mock_muppet

        # Configure mock deployment service
        mock_deployment_service.deploy_muppet.return_value = {
            "muppet_name": "test-integration-muppet",
            "status": "deployed",
            "service_arn": "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-integration-muppet",
            "service_url": "http://test-lb.amazonaws.com",
            "load_balancer_dns": "test-lb.amazonaws.com",
            "cluster_name": "test-cluster",
            "task_definition_arn": "arn:aws:ecs:us-east-1:123456789012:task-definition/test-integration-muppet:1",
            "log_group_name": "/aws/fargate/test-integration-muppet",
            "deployed_at": "2023-01-01T00:00:00Z",
        }

        deployment_request = {
            "container_image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-integration-muppet:latest",
            "environment_variables": {"CUSTOM_VAR": "test-value"},
        }

        response = client.post(
            "/api/v1/muppets/test-integration-muppet/deploy", json=deployment_request
        )
        assert response.status_code == 202

        data = response.json()
        assert data["muppet_name"] == "test-integration-muppet"
        assert data["status"] == "deployed"
        assert data["service_arn"] is not None
        assert data["service_url"] is not None

        # Verify deployment service was called
        mock_deployment_service.deploy_muppet.assert_called_once()

    def test_undeploy_muppet_endpoint(self, client, mock_deployment_service):
        """Test the undeploy muppet endpoint."""
        # Configure mock deployment service
        mock_deployment_service.undeploy_muppet.return_value = {
            "muppet_name": "test-integration-muppet",
            "status": "undeployed",
            "undeployed_at": "2023-01-01T00:00:00Z",
        }

        response = client.delete("/api/v1/muppets/test-integration-muppet/deploy")
        assert response.status_code == 202

        data = response.json()
        assert data["muppet_name"] == "test-integration-muppet"
        assert data["status"] == "undeployed"

        # Verify deployment service was called
        mock_deployment_service.undeploy_muppet.assert_called_once_with(
            "test-integration-muppet"
        )

    def test_get_deployment_status_endpoint(self, client, mock_deployment_service):
        """Test the get deployment status endpoint."""
        # Configure mock deployment service
        mock_deployment_service.get_deployment_status.return_value = {
            "muppet_name": "test-integration-muppet",
            "deployment_status": "completed",
            "service_arn": "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-integration-muppet",
            "service_url": "http://test-lb.amazonaws.com",
            "cluster_name": "test-cluster",
            "task_definition_arn": "arn:aws:ecs:us-east-1:123456789012:task-definition/test-integration-muppet:1",
            "desired_count": 1,
            "running_count": 1,
            "pending_count": 0,
            "last_updated": "2023-01-01T00:00:00Z",
            "health_status": "healthy",
        }

        response = client.get("/api/v1/muppets/test-integration-muppet/deployment")
        assert response.status_code == 200

        data = response.json()
        assert data["muppet_name"] == "test-integration-muppet"
        assert data["deployment_status"] == "completed"
        assert data["running_count"] == 1
        assert data["health_status"] == "healthy"

        # Verify deployment service was called
        mock_deployment_service.get_deployment_status.assert_called_once_with(
            "test-integration-muppet"
        )

    def test_scale_muppet_endpoint(self, client, mock_deployment_service):
        """Test the scale muppet endpoint."""
        # Configure mock deployment service
        mock_deployment_service.scale_muppet.return_value = {
            "muppet_name": "test-integration-muppet",
            "desired_count": 3,
            "min_capacity": 1,
            "max_capacity": 10,
            "scaled_at": "2023-01-01T00:00:00Z",
        }

        scaling_request = {"desired_count": 3, "min_capacity": 1, "max_capacity": 10}

        response = client.post(
            "/api/v1/muppets/test-integration-muppet/scale", json=scaling_request
        )
        assert response.status_code == 200

        data = response.json()
        assert data["muppet_name"] == "test-integration-muppet"
        assert data["desired_count"] == 3
        assert data["min_capacity"] == 1
        assert data["max_capacity"] == 10

        # Verify deployment service was called
        mock_deployment_service.scale_muppet.assert_called_once_with(
            muppet_name="test-integration-muppet",
            desired_count=3,
            min_capacity=1,
            max_capacity=10,
        )

    def test_get_muppet_logs_endpoint(self, client, mock_deployment_service):
        """Test the get muppet logs endpoint."""
        # Configure mock deployment service
        mock_deployment_service.get_muppet_logs.return_value = [
            {
                "timestamp": "2023-01-01T00:00:00Z",
                "message": "Application started successfully",
                "level": "INFO",
            },
            {
                "timestamp": "2023-01-01T00:01:00Z",
                "message": "Health check passed",
                "level": "DEBUG",
            },
        ]

        response = client.get("/api/v1/muppets/test-integration-muppet/logs?lines=50")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["message"] == "Application started successfully"
        assert data[0]["level"] == "INFO"
        assert data[1]["message"] == "Health check passed"
        assert data[1]["level"] == "DEBUG"

        # Verify deployment service was called
        mock_deployment_service.get_muppet_logs.assert_called_once_with(
            "test-integration-muppet", 50
        )

    def test_deploy_muppet_validation_error(self, client):
        """Test deploy muppet endpoint with validation error."""
        # Invalid deployment request (missing container_image)
        deployment_request = {"environment_variables": {"CUSTOM_VAR": "test-value"}}

        response = client.post(
            "/api/v1/muppets/test-integration-muppet/deploy", json=deployment_request
        )
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data
        # Check that the validation error mentions the missing field
        assert any("container_image" in str(error) for error in data["detail"])

    def test_scale_muppet_validation_error(self, client):
        """Test scale muppet endpoint with validation error."""
        # Invalid scaling request (min_capacity > max_capacity)
        scaling_request = {"desired_count": 5, "min_capacity": 10, "max_capacity": 5}

        response = client.post(
            "/api/v1/muppets/test-integration-muppet/scale", json=scaling_request
        )
        assert response.status_code == 400  # Bad request

        data = response.json()
        assert "error" in data
        assert "min_capacity cannot be greater than max_capacity" in data["message"]

    def test_get_logs_validation_error(self, client):
        """Test get logs endpoint with validation error."""
        # Invalid lines parameter (too high)
        response = client.get("/api/v1/muppets/test-integration-muppet/logs?lines=2000")
        assert response.status_code == 400  # Bad request

        data = response.json()
        assert "error" in data
        assert "lines parameter must be between 1 and 1000" in data["message"]

    def test_muppet_not_found_error(self, client, mock_state_manager):
        """Test endpoints with non-existent muppet."""
        # Configure mock state manager to return None
        mock_state_manager.get_muppet.return_value = None

        # Test get muppet
        response = client.get("/api/v1/muppets/nonexistent-muppet")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["message"]

        # Test deploy muppet
        deployment_request = {"container_image": "test-image:latest"}
        response = client.post(
            "/api/v1/muppets/nonexistent-muppet/deploy", json=deployment_request
        )
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["message"]

    def test_deployment_not_found_error(self, client, mock_deployment_service):
        """Test deployment status endpoint with non-deployed muppet."""
        # Configure mock deployment service to return None
        mock_deployment_service.get_deployment_status.return_value = None

        response = client.get("/api/v1/muppets/test-integration-muppet/deployment")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not deployed" in data["message"]

        # Verify deployment service was called
        mock_deployment_service.get_deployment_status.assert_called_once_with(
            "test-integration-muppet"
        )

    def test_list_muppets_empty(self, client, mock_lifecycle_service):
        """Test list muppets endpoint with no muppets."""
        # Configure mock lifecycle service to return empty list
        mock_lifecycle_service.list_all_muppets.return_value = {"muppets": []}

        response = client.get("/api/v1/muppets/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 0
        assert data == []

        # Verify lifecycle service was called
        mock_lifecycle_service.list_all_muppets.assert_called_once()

    def test_deploy_muppet_with_secrets(
        self, client, mock_state_manager, mock_deployment_service, mock_muppet
    ):
        """Test deploy muppet endpoint with secrets."""
        # Configure mock state manager
        mock_state_manager.get_muppet.return_value = mock_muppet

        # Configure mock deployment service
        mock_deployment_service.deploy_muppet.return_value = {
            "muppet_name": "test-integration-muppet",
            "status": "deployed",
            "service_arn": "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-integration-muppet",
            "service_url": "http://test-lb.amazonaws.com",
            "deployed_at": "2023-01-01T00:00:00Z",
        }

        deployment_request = {
            "container_image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-integration-muppet:latest",
            "environment_variables": {"CUSTOM_VAR": "test-value"},
            "secrets": {
                "DB_PASSWORD": "arn:aws:ssm:us-east-1:123456789012:parameter/db-password"
            },
        }

        response = client.post(
            "/api/v1/muppets/test-integration-muppet/deploy", json=deployment_request
        )
        assert response.status_code == 202

        data = response.json()
        assert data["muppet_name"] == "test-integration-muppet"
        assert data["status"] == "deployed"

        # Verify deployment service was called with secrets
        mock_deployment_service.deploy_muppet.assert_called_once()
        call_args = mock_deployment_service.deploy_muppet.call_args
        assert (
            call_args.kwargs["secrets"]["DB_PASSWORD"]
            == "arn:aws:ssm:us-east-1:123456789012:parameter/db-password"
        )
