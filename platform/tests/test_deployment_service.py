"""
Unit tests for the Deployment Service.

Tests the complete deployment orchestration for muppets to AWS Fargate.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.exceptions import DeploymentError, ValidationError
from src.managers.infrastructure_manager import DeploymentState, DeploymentStatus
from src.models import Muppet, MuppetStatus
from src.services.deployment_service import DeploymentService


@pytest.fixture
def deployment_service():
    """Create a deployment service instance for testing."""
    return DeploymentService()


@pytest.fixture
def sample_muppet():
    """Create a sample muppet for testing."""
    return Muppet(
        name="test-muppet",
        template="java-micronaut",
        status=MuppetStatus.CREATING,
        github_repo_url="https://github.com/muppet-platform/test-muppet",
        port=3000,
    )


@pytest.fixture
def mock_deployment_state():
    """Create a mock successful deployment state."""
    return DeploymentState(
        muppet_name="test-muppet",
        status=DeploymentStatus.COMPLETED,
        terraform_workspace="/tmp/test-workspace",
        state_backend="local",
        last_operation=None,
        last_updated="2023-01-01T00:00:00Z",
        outputs={
            "service_arn": "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-muppet",
            "service_url": "http://test-lb.amazonaws.com",
            "load_balancer_dns_name": "test-lb.amazonaws.com",
            "cluster_name": "test-cluster",
            "task_definition_arn": "arn:aws:ecs:us-east-1:123456789012:task-definition/test-muppet:1",
            "log_group_name": "/aws/fargate/test-muppet",
        },
    )


class TestDeploymentService:
    """Test cases for DeploymentService."""

    def test_initialization(self, deployment_service):
        """Test deployment service initialization."""
        assert deployment_service.settings is not None
        assert deployment_service.infrastructure_manager is not None
        assert deployment_service.github_manager is not None

    @pytest.mark.asyncio
    async def test_deploy_muppet_success(
        self, deployment_service, sample_muppet, mock_deployment_state
    ):
        """Test successful muppet deployment."""
        container_image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-muppet:latest"
        )

        # Mock infrastructure manager
        with patch.object(
            deployment_service.infrastructure_manager, "deploy_infrastructure"
        ) as mock_deploy:
            mock_deploy.return_value = mock_deployment_state

            # Mock GitHub manager
            with patch.object(
                deployment_service.github_manager, "update_muppet_status"
            ) as mock_update_status:
                mock_update_status.return_value = True

                # Mock ECR validation
                with patch(
                    "src.services.deployment_service.get_ecr_client"
                ) as mock_get_ecr:
                    mock_ecr_client = AsyncMock()
                    mock_ecr_client.describe_repositories.return_value = {
                        "repositories": [{"repositoryName": "test-muppet"}]
                    }
                    mock_get_ecr.return_value = mock_ecr_client

                    # Mock service stability check
                    with patch.object(
                        deployment_service, "_wait_for_service_stable"
                    ) as mock_wait:
                        mock_wait.return_value = None

                        result = await deployment_service.deploy_muppet(
                            muppet=sample_muppet, container_image=container_image
                        )

                        assert result["muppet_name"] == "test-muppet"
                        assert result["status"] == "deployed"
                        assert (
                            result["service_arn"]
                            == mock_deployment_state.outputs["service_arn"]
                        )
                        assert (
                            result["service_url"]
                            == mock_deployment_state.outputs["service_url"]
                        )
                        assert sample_muppet.status == MuppetStatus.RUNNING

                        # Verify GitHub status updates
                        assert mock_update_status.call_count == 2
                        mock_update_status.assert_any_call("test-muppet", "creating")
                        mock_update_status.assert_any_call("test-muppet", "running")

    @pytest.mark.asyncio
    async def test_deploy_muppet_infrastructure_failure(
        self, deployment_service, sample_muppet
    ):
        """Test muppet deployment with infrastructure failure."""
        container_image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-muppet:latest"
        )

        # Mock failed deployment state
        failed_state = DeploymentState(
            muppet_name="test-muppet",
            status=DeploymentStatus.FAILED,
            terraform_workspace="/tmp/test-workspace",
            state_backend="local",
            last_operation=None,
            last_updated="2023-01-01T00:00:00Z",
            outputs={},
            error_message="Terraform apply failed",
        )

        # Mock infrastructure manager
        with patch.object(
            deployment_service.infrastructure_manager, "deploy_infrastructure"
        ) as mock_deploy:
            mock_deploy.return_value = failed_state

            # Mock GitHub manager
            with patch.object(
                deployment_service.github_manager, "update_muppet_status"
            ) as mock_update_status:
                mock_update_status.return_value = True

                # Mock ECR validation
                with patch(
                    "src.services.deployment_service.get_ecr_client"
                ) as mock_get_ecr:
                    mock_ecr_client = AsyncMock()
                    mock_ecr_client.describe_repositories.return_value = {
                        "repositories": [{"repositoryName": "test-muppet"}]
                    }
                    mock_get_ecr.return_value = mock_ecr_client

                    with pytest.raises(DeploymentError) as exc_info:
                        await deployment_service.deploy_muppet(
                            muppet=sample_muppet, container_image=container_image
                        )

                    assert "Infrastructure deployment failed" in str(exc_info.value)
                    assert sample_muppet.status == MuppetStatus.ERROR

                    # Verify GitHub status updates
                    mock_update_status.assert_any_call("test-muppet", "creating")
                    mock_update_status.assert_any_call("test-muppet", "error")

    @pytest.mark.asyncio
    async def test_deploy_muppet_validation_error(self, deployment_service):
        """Test muppet deployment with validation error."""
        # Create muppet with missing name
        invalid_muppet = Muppet(
            name="",  # Invalid empty name
            template="java-micronaut",
            status=MuppetStatus.CREATING,
            github_repo_url="https://github.com/muppet-platform/test-muppet",
            port=3000,
        )

        container_image = "test-image:latest"

        # Mock GitHub manager to avoid actual API calls
        with patch.object(
            deployment_service.github_manager, "update_muppet_status"
        ) as mock_update_status:
            mock_update_status.return_value = True

            with pytest.raises(ValidationError) as exc_info:
                await deployment_service.deploy_muppet(
                    muppet=invalid_muppet, container_image=container_image
                )

            assert "Muppet name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_undeploy_muppet_success(self, deployment_service):
        """Test successful muppet undeployment."""
        muppet_name = "test-muppet"

        # Mock successful destruction
        destroyed_state = DeploymentState(
            muppet_name=muppet_name,
            status=DeploymentStatus.DESTROYED,
            terraform_workspace="",
            state_backend="local",
            last_operation=None,
            last_updated="2023-01-01T00:00:00Z",
            outputs={},
        )

        # Mock infrastructure manager
        with patch.object(
            deployment_service.infrastructure_manager, "destroy_infrastructure"
        ) as mock_destroy:
            mock_destroy.return_value = destroyed_state

            # Mock GitHub manager
            with patch.object(
                deployment_service.github_manager, "update_muppet_status"
            ) as mock_update_status:
                mock_update_status.return_value = True

                result = await deployment_service.undeploy_muppet(muppet_name)

                assert result["muppet_name"] == muppet_name
                assert result["status"] == "undeployed"
                assert "undeployed_at" in result

                # Verify GitHub status update
                mock_update_status.assert_called_once_with(muppet_name, "deleting")

    @pytest.mark.asyncio
    async def test_undeploy_muppet_failure(self, deployment_service):
        """Test muppet undeployment with failure."""
        muppet_name = "test-muppet"

        # Mock failed destruction
        failed_state = DeploymentState(
            muppet_name=muppet_name,
            status=DeploymentStatus.FAILED,
            terraform_workspace="/tmp/test-workspace",
            state_backend="local",
            last_operation=None,
            last_updated="2023-01-01T00:00:00Z",
            outputs={},
            error_message="Terraform destroy failed",
        )

        # Mock infrastructure manager
        with patch.object(
            deployment_service.infrastructure_manager, "destroy_infrastructure"
        ) as mock_destroy:
            mock_destroy.return_value = failed_state

            # Mock GitHub manager
            with patch.object(
                deployment_service.github_manager, "update_muppet_status"
            ) as mock_update_status:
                mock_update_status.return_value = True

                with pytest.raises(DeploymentError) as exc_info:
                    await deployment_service.undeploy_muppet(muppet_name)

                assert "Infrastructure destruction failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_deployment_status_success(
        self, deployment_service, mock_deployment_state
    ):
        """Test getting deployment status successfully."""
        muppet_name = "test-muppet"

        # Mock infrastructure manager
        with patch.object(
            deployment_service.infrastructure_manager, "get_deployment_status"
        ) as mock_get_status:
            mock_get_status.return_value = mock_deployment_state

            # Mock ECS service info
            with patch.object(
                deployment_service, "_get_service_info"
            ) as mock_get_service_info:
                mock_get_service_info.return_value = {
                    "desired_count": 1,
                    "running_count": 1,
                    "pending_count": 0,
                    "health_status": "healthy",
                }

                result = await deployment_service.get_deployment_status(muppet_name)

                assert result is not None
                assert result["muppet_name"] == muppet_name
                assert result["deployment_status"] == "completed"
                assert (
                    result["service_arn"]
                    == mock_deployment_state.outputs["service_arn"]
                )
                assert result["running_count"] == 1
                assert result["health_status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_deployment_status_not_found(self, deployment_service):
        """Test getting deployment status for non-existent deployment."""
        muppet_name = "nonexistent-muppet"

        # Mock infrastructure manager
        with patch.object(
            deployment_service.infrastructure_manager, "get_deployment_status"
        ) as mock_get_status:
            mock_get_status.return_value = None

            result = await deployment_service.get_deployment_status(muppet_name)

            assert result is None

    def test_create_infrastructure_config(self, deployment_service, sample_muppet):
        """Test infrastructure configuration creation."""
        container_image = "test-image:latest"
        environment_variables = {"CUSTOM_VAR": "value"}
        secrets = {"SECRET_KEY": "arn:aws:ssm:us-east-1:123456789012:parameter/secret"}

        config = deployment_service._create_infrastructure_config(
            sample_muppet, container_image, environment_variables, secrets
        )

        assert config.muppet_name == sample_muppet.name
        assert config.template_name == sample_muppet.template
        assert config.fargate_config["container_image"] == container_image
        assert config.fargate_config["container_port"] == sample_muppet.port
        assert config.variables["environment_variables"]["CUSTOM_VAR"] == "value"
        assert config.variables["secrets"]["SECRET_KEY"] == secrets["SECRET_KEY"]

        # Check default environment variables
        env_vars = config.variables["environment_variables"]
        assert env_vars["ENVIRONMENT"] == "production"
        assert env_vars["MUPPET_NAME"] == sample_muppet.name
        assert env_vars["TEMPLATE"] == sample_muppet.template

    @pytest.mark.asyncio
    async def test_validate_deployment_requirements_success(
        self, deployment_service, sample_muppet
    ):
        """Test successful deployment requirements validation."""
        container_image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-muppet:latest"
        )

        # Mock ECR validation
        with patch("src.services.deployment_service.get_ecr_client") as mock_get_ecr:
            mock_ecr_client = AsyncMock()
            mock_ecr_client.describe_repositories.return_value = {
                "repositories": [{"repositoryName": "test-muppet"}]
            }
            mock_get_ecr.return_value = mock_ecr_client

            # Should not raise any exception
            await deployment_service._validate_deployment_requirements(
                sample_muppet, container_image
            )

    @pytest.mark.asyncio
    async def test_validate_deployment_requirements_invalid_muppet(
        self, deployment_service
    ):
        """Test deployment requirements validation with invalid muppet."""
        invalid_muppet = Muppet(
            name="",  # Invalid empty name
            template="java-micronaut",
            status=MuppetStatus.CREATING,
            github_repo_url="https://github.com/muppet-platform/test-muppet",
            port=3000,
        )
        container_image = "test-image:latest"

        with pytest.raises(ValidationError) as exc_info:
            await deployment_service._validate_deployment_requirements(
                invalid_muppet, container_image
            )

        assert "Muppet name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_deployment_requirements_invalid_image(
        self, deployment_service, sample_muppet
    ):
        """Test deployment requirements validation with invalid container image."""
        container_image = ""  # Invalid empty image

        with pytest.raises(ValidationError) as exc_info:
            await deployment_service._validate_deployment_requirements(
                sample_muppet, container_image
            )

        assert "Container image is required" in str(exc_info.value)

    def test_extract_deployment_info(self, deployment_service):
        """Test deployment information extraction from Terraform outputs."""
        terraform_outputs = {
            "service_arn": "arn:aws:ecs:us-east-1:123456789012:service/test-cluster/test-muppet",
            "service_url": "http://test-lb.amazonaws.com",
            "load_balancer_dns_name": "test-lb.amazonaws.com",
            "cluster_name": "test-cluster",
            "task_definition_arn": "arn:aws:ecs:us-east-1:123456789012:task-definition/test-muppet:1",
            "log_group_name": "/aws/fargate/test-muppet",
        }

        deployment_info = deployment_service._extract_deployment_info(terraform_outputs)

        assert deployment_info["service_arn"] == terraform_outputs["service_arn"]
        assert deployment_info["service_url"] == terraform_outputs["service_url"]
        assert (
            deployment_info["load_balancer_dns"]
            == terraform_outputs["load_balancer_dns_name"]
        )
        assert deployment_info["cluster_name"] == terraform_outputs["cluster_name"]
        assert (
            deployment_info["task_definition_arn"]
            == terraform_outputs["task_definition_arn"]
        )
        assert deployment_info["log_group_name"] == terraform_outputs["log_group_name"]

    @pytest.mark.asyncio
    async def test_close(self, deployment_service):
        """Test deployment service cleanup."""
        # Mock GitHub manager close
        with patch.object(deployment_service.github_manager, "close") as mock_close:
            mock_close.return_value = None

            await deployment_service.close()

            mock_close.assert_called_once()
