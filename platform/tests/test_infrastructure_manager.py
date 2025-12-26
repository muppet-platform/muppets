"""
Unit tests for the Infrastructure Manager.

Tests Terraform execution, state management, and AWS resource provisioning
coordination functionality.
"""

import json
import shutil
from unittest.mock import AsyncMock, patch

import pytest

from src.exceptions import InfrastructureError
from src.managers.infrastructure_manager import (
    DeploymentState,
    DeploymentStatus,
    InfrastructureConfig,
    InfrastructureManager,
    TerraformOperation,
    TerraformOutput,
)


@pytest.fixture
def infrastructure_manager():
    """Create an infrastructure manager instance for testing."""
    return InfrastructureManager()


@pytest.fixture
def sample_config():
    """Create a sample infrastructure configuration."""
    return InfrastructureConfig(
        muppet_name="test-muppet",
        template_name="java-micronaut",
        aws_region="us-east-1",
        environment="development",
        module_versions={
            "fargate-service": "1.0.0",
            "networking": "1.0.0",
            "monitoring": "1.0.0",
            "iam": "1.0.0",
            "ecr": "1.0.0",
        },
        vpc_config={
            "vpc_cidr": "10.0.0.0/16",
            "public_subnet_count": 2,
            "private_subnet_count": 2,
            "enable_nat_gateway": True,
            "single_nat_gateway": False,
            "enable_vpc_endpoints": True,
        },
        fargate_config={
            "container_image": "test-muppet:latest",
            "container_port": 3000,
            "cpu": 256,
            "memory": 512,
            "desired_count": 1,
            "enable_autoscaling": True,
            "autoscaling_min_capacity": 1,
            "autoscaling_max_capacity": 10,
            "health_check_path": "/health",
        },
        monitoring_config={
            "log_retention_days": 7,
            "enable_alarms": True,
            "cpu_alarm_threshold": 80,
            "memory_alarm_threshold": 85,
            "response_time_alarm_threshold": 2.0,
        },
        variables={
            "environment_variables": {"APP_ENV": "development", "LOG_LEVEL": "INFO"}
        },
    )


@pytest.fixture
def mock_terraform_modules_path(tmp_path):
    """Create a mock terraform modules directory structure."""
    modules_path = tmp_path / "terraform-modules"
    modules_path.mkdir()

    # Create mock modules
    for module_name in ["fargate-service", "networking", "monitoring", "iam", "ecr"]:
        module_dir = modules_path / module_name
        module_dir.mkdir()
        (module_dir / "main.tf").write_text(f"# {module_name} module")
        (module_dir / "variables.tf").write_text(f"# {module_name} variables")
        (module_dir / "outputs.tf").write_text(f"# {module_name} outputs")

    return modules_path


class TestInfrastructureManager:
    """Test cases for InfrastructureManager."""

    def test_initialization(self, infrastructure_manager):
        """Test infrastructure manager initialization."""
        assert infrastructure_manager.settings is not None
        assert infrastructure_manager.terraform_modules_path.exists()
        assert infrastructure_manager.workspace_path.exists()

    def test_get_available_modules(
        self, infrastructure_manager, mock_terraform_modules_path
    ):
        """Test getting available Terraform modules."""
        # Mock the terraform modules path
        infrastructure_manager.terraform_modules_path = mock_terraform_modules_path

        modules = infrastructure_manager.get_available_modules()

        expected_modules = ["fargate-service", "networking", "monitoring", "iam", "ecr"]
        assert set(modules) == set(expected_modules)

    def test_get_available_modules_empty_directory(
        self, infrastructure_manager, tmp_path
    ):
        """Test getting modules from empty directory."""
        empty_path = tmp_path / "empty"
        empty_path.mkdir()
        infrastructure_manager.terraform_modules_path = empty_path

        modules = infrastructure_manager.get_available_modules()
        assert modules == []

    def test_get_available_modules_nonexistent_directory(
        self, infrastructure_manager, tmp_path
    ):
        """Test getting modules from nonexistent directory."""
        nonexistent_path = tmp_path / "nonexistent"
        infrastructure_manager.terraform_modules_path = nonexistent_path

        modules = infrastructure_manager.get_available_modules()
        assert modules == []

    def test_create_workspace(self, infrastructure_manager):
        """Test workspace creation."""
        muppet_name = "test-workspace"
        workspace_dir = infrastructure_manager._create_workspace(muppet_name)

        assert workspace_dir.exists()
        assert workspace_dir.is_dir()
        assert workspace_dir.name == muppet_name

        # Clean up
        shutil.rmtree(workspace_dir, ignore_errors=True)

    def test_get_workspace_path(self, infrastructure_manager):
        """Test workspace path generation."""
        muppet_name = "test-path"
        workspace_path = infrastructure_manager._get_workspace_path(muppet_name)

        assert workspace_path.name == muppet_name
        assert workspace_path.parent == infrastructure_manager.workspace_path

    def test_generate_main_tf(
        self, infrastructure_manager, sample_config, mock_terraform_modules_path
    ):
        """Test main.tf generation."""
        infrastructure_manager.terraform_modules_path = mock_terraform_modules_path

        main_tf_content = infrastructure_manager._generate_main_tf(sample_config)

        # Check that all required modules are included
        assert 'module "networking"' in main_tf_content
        assert 'module "iam"' in main_tf_content
        assert 'module "ecr"' in main_tf_content
        assert 'module "fargate_service"' in main_tf_content
        assert 'module "monitoring"' in main_tf_content

        # Check provider configuration
        assert 'provider "aws"' in main_tf_content
        assert "region = var.aws_region" in main_tf_content

        # Check common tags
        assert 'Project     = "muppet-platform"' in main_tf_content
        assert "Muppet      = var.muppet_name" in main_tf_content

    def test_generate_variables_tf(self, infrastructure_manager, sample_config):
        """Test variables.tf generation."""
        variables_tf_content = infrastructure_manager._generate_variables_tf(
            sample_config
        )

        # Check that all required variables are defined
        required_variables = [
            "muppet_name",
            "template_name",
            "aws_region",
            "environment",
            "container_image",
            "container_port",
            "vpc_cidr",
            "fargate_cpu",
            "fargate_memory",
            "enable_monitoring_alarms",
        ]

        for var in required_variables:
            assert f'variable "{var}"' in variables_tf_content

    def test_generate_tfvars(self, infrastructure_manager, sample_config):
        """Test terraform.tfvars generation."""
        tfvars_content = infrastructure_manager._generate_tfvars(sample_config)

        # Check basic configuration
        assert f'muppet_name   = "{sample_config.muppet_name}"' in tfvars_content
        assert f'template_name = "{sample_config.template_name}"' in tfvars_content
        assert f'aws_region    = "{sample_config.aws_region}"' in tfvars_content

        # Check container configuration
        assert (
            f"container_port  = {sample_config.fargate_config['container_port']}"
            in tfvars_content
        )

        # Check networking configuration
        assert (
            f"vpc_cidr             = \"{sample_config.vpc_config['vpc_cidr']}\""
            in tfvars_content
        )

        # Check environment variables
        assert "environment_variables = {" in tfvars_content
        assert '"ENVIRONMENT" = "development"' in tfvars_content
        assert '"AWS_REGION" = "us-east-1"' in tfvars_content

    @pytest.mark.asyncio
    async def test_run_terraform_success(self, infrastructure_manager, tmp_path):
        """Test successful Terraform command execution."""
        workspace_dir = tmp_path / "test-workspace"
        workspace_dir.mkdir()

        # Mock successful terraform command
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Success", b"")
            mock_subprocess.return_value = mock_process

            result = await infrastructure_manager._run_terraform(
                workspace_dir, TerraformOperation.VALIDATE
            )

            assert result.success is True
            assert result.stdout == "Success"
            assert result.stderr == ""
            assert result.exit_code == 0
            assert result.operation == TerraformOperation.VALIDATE

    @pytest.mark.asyncio
    async def test_run_terraform_failure(self, infrastructure_manager, tmp_path):
        """Test failed Terraform command execution."""
        workspace_dir = tmp_path / "test-workspace"
        workspace_dir.mkdir()

        # Mock failed terraform command
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"Error occurred")
            mock_subprocess.return_value = mock_process

            result = await infrastructure_manager._run_terraform(
                workspace_dir, TerraformOperation.VALIDATE
            )

            assert result.success is False
            assert result.stdout == ""
            assert result.stderr == "Error occurred"
            assert result.exit_code == 1
            assert result.operation == TerraformOperation.VALIDATE

    @pytest.mark.asyncio
    async def test_run_terraform_exception(self, infrastructure_manager, tmp_path):
        """Test Terraform command execution with exception."""
        workspace_dir = tmp_path / "test-workspace"
        workspace_dir.mkdir()

        # Mock exception during terraform command
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_subprocess.side_effect = Exception("Command failed")

            result = await infrastructure_manager._run_terraform(
                workspace_dir, TerraformOperation.VALIDATE
            )

            assert result.success is False
            assert result.stderr == "Command failed"
            assert result.exit_code == -1

    @pytest.mark.asyncio
    async def test_get_terraform_outputs_success(
        self, infrastructure_manager, tmp_path
    ):
        """Test getting Terraform outputs successfully."""
        workspace_dir = tmp_path / "test-workspace"
        workspace_dir.mkdir()

        # Mock terraform output command
        mock_outputs = {
            "vpc_id": {"value": "vpc-12345"},
            "load_balancer_dns": {"value": "test-lb.amazonaws.com"},
        }

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                json.dumps(mock_outputs).encode("utf-8"),
                b"",
            )
            mock_subprocess.return_value = mock_process

            outputs = await infrastructure_manager._get_terraform_outputs(workspace_dir)

            assert outputs["vpc_id"] == "vpc-12345"
            assert outputs["load_balancer_dns"] == "test-lb.amazonaws.com"

    @pytest.mark.asyncio
    async def test_get_terraform_outputs_failure(
        self, infrastructure_manager, tmp_path
    ):
        """Test getting Terraform outputs with failure."""
        workspace_dir = tmp_path / "test-workspace"
        workspace_dir.mkdir()

        # Mock failed terraform output command
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"No outputs found")
            mock_subprocess.return_value = mock_process

            outputs = await infrastructure_manager._get_terraform_outputs(workspace_dir)

            assert outputs == {}

    @pytest.mark.asyncio
    async def test_deploy_infrastructure_success(
        self, infrastructure_manager, sample_config, mock_terraform_modules_path
    ):
        """Test successful infrastructure deployment."""
        infrastructure_manager.terraform_modules_path = mock_terraform_modules_path

        # Mock all terraform operations as successful
        with patch.object(
            infrastructure_manager, "_run_terraform"
        ) as mock_run_terraform:
            mock_run_terraform.return_value = TerraformOutput(
                success=True,
                stdout="Success",
                stderr="",
                exit_code=0,
                operation=TerraformOperation.APPLY,
            )

            with patch.object(
                infrastructure_manager, "_get_terraform_outputs"
            ) as mock_get_outputs:
                mock_get_outputs.return_value = {
                    "vpc_id": "vpc-12345",
                    "load_balancer_dns": "test-lb.amazonaws.com",
                }

                deployment_state = await infrastructure_manager.deploy_infrastructure(
                    sample_config
                )

                assert deployment_state.muppet_name == sample_config.muppet_name
                assert deployment_state.status == DeploymentStatus.COMPLETED
                assert deployment_state.last_operation == TerraformOperation.APPLY
                assert deployment_state.outputs["vpc_id"] == "vpc-12345"
                assert deployment_state.error_message is None

    @pytest.mark.asyncio
    async def test_deploy_infrastructure_terraform_failure(
        self, infrastructure_manager, sample_config, mock_terraform_modules_path
    ):
        """Test infrastructure deployment with Terraform failure."""
        infrastructure_manager.terraform_modules_path = mock_terraform_modules_path

        # Mock terraform init success, but apply failure
        def mock_terraform_side_effect(workspace_dir, operation, auto_approve=False):
            if operation == TerraformOperation.APPLY:
                return TerraformOutput(
                    success=False,
                    stdout="",
                    stderr="Apply failed",
                    exit_code=1,
                    operation=operation,
                )
            return TerraformOutput(
                success=True,
                stdout="Success",
                stderr="",
                exit_code=0,
                operation=operation,
            )

        with patch.object(
            infrastructure_manager,
            "_run_terraform",
            side_effect=mock_terraform_side_effect,
        ):
            deployment_state = await infrastructure_manager.deploy_infrastructure(
                sample_config
            )

            assert deployment_state.muppet_name == sample_config.muppet_name
            assert deployment_state.status == DeploymentStatus.FAILED
            assert deployment_state.error_message is not None
            assert "Apply failed" in deployment_state.error_message

    @pytest.mark.asyncio
    async def test_destroy_infrastructure_success(self, infrastructure_manager):
        """Test successful infrastructure destruction."""
        muppet_name = "test-destroy"

        # Create a mock workspace
        workspace_dir = infrastructure_manager._create_workspace(muppet_name)
        (workspace_dir / "terraform.tfstate").write_text("{}")

        # Mock successful terraform destroy
        with patch.object(
            infrastructure_manager, "_run_terraform"
        ) as mock_run_terraform:
            mock_run_terraform.return_value = TerraformOutput(
                success=True,
                stdout="Destroy complete",
                stderr="",
                exit_code=0,
                operation=TerraformOperation.DESTROY,
            )

            deployment_state = await infrastructure_manager.destroy_infrastructure(
                muppet_name
            )

            assert deployment_state.muppet_name == muppet_name
            assert deployment_state.status == DeploymentStatus.DESTROYED
            assert deployment_state.last_operation == TerraformOperation.DESTROY
            assert not workspace_dir.exists()  # Workspace should be cleaned up

    @pytest.mark.asyncio
    async def test_destroy_infrastructure_no_workspace(self, infrastructure_manager):
        """Test destroying infrastructure when no workspace exists."""
        muppet_name = "nonexistent-muppet"

        deployment_state = await infrastructure_manager.destroy_infrastructure(
            muppet_name
        )

        assert deployment_state.muppet_name == muppet_name
        assert deployment_state.status == DeploymentStatus.DESTROYED
        assert deployment_state.terraform_workspace == ""

    @pytest.mark.asyncio
    async def test_destroy_infrastructure_terraform_failure(
        self, infrastructure_manager
    ):
        """Test infrastructure destruction with Terraform failure."""
        muppet_name = "test-destroy-fail"

        # Create a mock workspace
        workspace_dir = infrastructure_manager._create_workspace(muppet_name)
        (workspace_dir / "terraform.tfstate").write_text("{}")

        # Mock failed terraform destroy
        with patch.object(
            infrastructure_manager, "_run_terraform"
        ) as mock_run_terraform:
            mock_run_terraform.return_value = TerraformOutput(
                success=False,
                stdout="",
                stderr="Destroy failed",
                exit_code=1,
                operation=TerraformOperation.DESTROY,
            )

            with pytest.raises(InfrastructureError) as exc_info:
                await infrastructure_manager.destroy_infrastructure(muppet_name)

            assert "Destroy failed" in str(exc_info.value)

        # Clean up
        shutil.rmtree(workspace_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_deployment_status_completed(self, infrastructure_manager):
        """Test getting deployment status for completed deployment."""
        muppet_name = "test-status"

        # Create a mock workspace with state file
        workspace_dir = infrastructure_manager._create_workspace(muppet_name)
        (workspace_dir / "terraform.tfstate").write_text("{}")

        # Mock terraform outputs
        with patch.object(
            infrastructure_manager, "_get_terraform_outputs"
        ) as mock_get_outputs:
            mock_get_outputs.return_value = {"vpc_id": "vpc-12345"}

            deployment_state = await infrastructure_manager.get_deployment_status(
                muppet_name
            )

            assert deployment_state is not None
            assert deployment_state.muppet_name == muppet_name
            assert deployment_state.status == DeploymentStatus.COMPLETED
            assert deployment_state.outputs["vpc_id"] == "vpc-12345"

        # Clean up
        shutil.rmtree(workspace_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_deployment_status_pending(self, infrastructure_manager):
        """Test getting deployment status for pending deployment."""
        muppet_name = "test-pending"

        # Create a mock workspace without state file
        workspace_dir = infrastructure_manager._create_workspace(muppet_name)

        deployment_state = await infrastructure_manager.get_deployment_status(
            muppet_name
        )

        assert deployment_state is not None
        assert deployment_state.muppet_name == muppet_name
        assert deployment_state.status == DeploymentStatus.PENDING
        assert deployment_state.last_operation is None

        # Clean up
        shutil.rmtree(workspace_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_get_deployment_status_not_found(self, infrastructure_manager):
        """Test getting deployment status for non-existent deployment."""
        muppet_name = "nonexistent"

        deployment_state = await infrastructure_manager.get_deployment_status(
            muppet_name
        )

        assert deployment_state is None

    @pytest.mark.asyncio
    async def test_update_module_versions_success(
        self, infrastructure_manager, mock_terraform_modules_path
    ):
        """Test successful module version update."""
        infrastructure_manager.terraform_modules_path = mock_terraform_modules_path

        module_versions = {"fargate-service": "1.1.0", "networking": "1.0.1"}

        result = await infrastructure_manager.update_module_versions(module_versions)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_module_versions_invalid_module(
        self, infrastructure_manager, mock_terraform_modules_path
    ):
        """Test module version update with invalid module."""
        infrastructure_manager.terraform_modules_path = mock_terraform_modules_path

        module_versions = {"nonexistent-module": "1.0.0"}

        with pytest.raises(InfrastructureError) as exc_info:
            await infrastructure_manager.update_module_versions(module_versions)

        assert "Module nonexistent-module not found" in str(exc_info.value)

    def test_get_current_timestamp(self, infrastructure_manager):
        """Test current timestamp generation."""
        timestamp = infrastructure_manager._get_current_timestamp()

        # Check format (ISO 8601 with Z suffix)
        assert timestamp.endswith("Z")
        assert "T" in timestamp

        # Should be parseable as datetime
        from datetime import datetime

        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None

    def test_get_file_timestamp(self, infrastructure_manager, tmp_path):
        """Test file timestamp generation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        timestamp = infrastructure_manager._get_file_timestamp(test_file)

        # Check format (ISO 8601 with Z suffix)
        assert timestamp.endswith("Z")
        assert "T" in timestamp

        # Should be parseable as datetime
        from datetime import datetime

        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None


class TestInfrastructureConfig:
    """Test cases for InfrastructureConfig dataclass."""

    def test_infrastructure_config_creation(self):
        """Test creating an infrastructure configuration."""
        config = InfrastructureConfig(
            muppet_name="test-muppet",
            template_name="java-micronaut",
            aws_region="us-west-2",
            environment="production",
            module_versions={"fargate-service": "1.0.0"},
            vpc_config={"vpc_cidr": "10.0.0.0/16"},
            fargate_config={"cpu": 512, "memory": 1024},
            monitoring_config={"log_retention_days": 14},
            variables={"custom_var": "value"},
        )

        assert config.muppet_name == "test-muppet"
        assert config.template_name == "java-micronaut"
        assert config.aws_region == "us-west-2"
        assert config.environment == "production"
        assert config.module_versions["fargate-service"] == "1.0.0"
        assert config.vpc_config["vpc_cidr"] == "10.0.0.0/16"
        assert config.fargate_config["cpu"] == 512
        assert config.monitoring_config["log_retention_days"] == 14
        assert config.variables["custom_var"] == "value"


class TestDeploymentState:
    """Test cases for DeploymentState dataclass."""

    def test_deployment_state_creation(self):
        """Test creating a deployment state."""
        state = DeploymentState(
            muppet_name="test-muppet",
            status=DeploymentStatus.COMPLETED,
            terraform_workspace="/tmp/workspace",
            state_backend="s3",
            last_operation=TerraformOperation.APPLY,
            last_updated="2023-01-01T00:00:00Z",
            outputs={"vpc_id": "vpc-12345"},
            error_message=None,
        )

        assert state.muppet_name == "test-muppet"
        assert state.status == DeploymentStatus.COMPLETED
        assert state.terraform_workspace == "/tmp/workspace"
        assert state.state_backend == "s3"
        assert state.last_operation == TerraformOperation.APPLY
        assert state.last_updated == "2023-01-01T00:00:00Z"
        assert state.outputs["vpc_id"] == "vpc-12345"
        assert state.error_message is None


class TestTerraformOutput:
    """Test cases for TerraformOutput dataclass."""

    def test_terraform_output_success(self):
        """Test creating a successful Terraform output."""
        output = TerraformOutput(
            success=True,
            stdout="Apply complete!",
            stderr="",
            exit_code=0,
            operation=TerraformOperation.APPLY,
        )

        assert output.success is True
        assert output.stdout == "Apply complete!"
        assert output.stderr == ""
        assert output.exit_code == 0
        assert output.operation == TerraformOperation.APPLY

    def test_terraform_output_failure(self):
        """Test creating a failed Terraform output."""
        output = TerraformOutput(
            success=False,
            stdout="",
            stderr="Error: Invalid configuration",
            exit_code=1,
            operation=TerraformOperation.VALIDATE,
        )

        assert output.success is False
        assert output.stdout == ""
        assert output.stderr == "Error: Invalid configuration"
        assert output.exit_code == 1
        assert output.operation == TerraformOperation.VALIDATE
