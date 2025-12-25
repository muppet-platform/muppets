"""
Infrastructure Manager for the Muppet Platform.

This module provides Terraform execution and state management for AWS resource
provisioning. It coordinates the deployment of shared infrastructure modules
and manages module versioning and updates.
"""

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..exceptions import InfrastructureError, ValidationError
from ..logging_config import get_logger

logger = get_logger(__name__)


class TerraformOperation(Enum):
    """Terraform operation types."""

    PLAN = "plan"
    APPLY = "apply"
    DESTROY = "destroy"
    INIT = "init"
    VALIDATE = "validate"


class DeploymentStatus(Enum):
    """Deployment status types."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DESTROYED = "destroyed"


@dataclass
class TerraformOutput:
    """Terraform command output."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    operation: TerraformOperation


@dataclass
class ModuleVersion:
    """Terraform module version information."""

    name: str
    version: str
    source_path: Path
    checksum: str


@dataclass
class InfrastructureConfig:
    """Infrastructure configuration for a muppet deployment."""

    muppet_name: str
    template_name: str
    aws_region: str
    environment: str

    # Module versions
    module_versions: Dict[str, str]

    # Resource configuration
    vpc_config: Dict[str, Any]
    fargate_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]

    # Custom variables
    variables: Dict[str, Any]


@dataclass
class DeploymentState:
    """Current deployment state."""

    muppet_name: str
    status: DeploymentStatus
    terraform_workspace: str
    state_backend: str
    last_operation: Optional[TerraformOperation]
    last_updated: str
    outputs: Dict[str, Any]
    error_message: Optional[str] = None


class InfrastructureManager:
    """
    Manages AWS infrastructure provisioning using Terraform.

    This manager handles:
    - Terraform execution and state management
    - Module versioning and update mechanisms
    - AWS resource provisioning coordination
    - Deployment state tracking
    """

    def __init__(self):
        self.settings = get_settings()
        self.terraform_modules_path = (
            Path(__file__).parent.parent.parent.parent / "terraform-modules"
        )
        self.workspace_path = Path(tempfile.gettempdir()) / "muppet-platform-terraform"
        self.workspace_path.mkdir(exist_ok=True)

        logger.info(
            f"Infrastructure manager initialized with modules path: {self.terraform_modules_path}"
        )

    async def deploy_infrastructure(
        self, config: InfrastructureConfig
    ) -> DeploymentState:
        """
        Deploy infrastructure for a muppet.

        Args:
            config: Infrastructure configuration

        Returns:
            Deployment state

        Raises:
            InfrastructureError: If deployment fails
        """
        logger.info(
            f"Starting infrastructure deployment for muppet: {config.muppet_name}"
        )

        try:
            # Create workspace for this deployment
            workspace_dir = self._create_workspace(config.muppet_name)

            # Generate Terraform configuration
            await self._generate_terraform_config(workspace_dir, config)

            # Initialize Terraform
            init_result = await self._run_terraform(
                workspace_dir, TerraformOperation.INIT
            )
            if not init_result.success:
                raise InfrastructureError(
                    f"Terraform init failed: {init_result.stderr}"
                )

            # Validate configuration
            validate_result = await self._run_terraform(
                workspace_dir, TerraformOperation.VALIDATE
            )
            if not validate_result.success:
                raise InfrastructureError(
                    f"Terraform validation failed: {validate_result.stderr}"
                )

            # Plan deployment
            plan_result = await self._run_terraform(
                workspace_dir, TerraformOperation.PLAN
            )
            if not plan_result.success:
                raise InfrastructureError(
                    f"Terraform plan failed: {plan_result.stderr}"
                )

            # Apply deployment
            apply_result = await self._run_terraform(
                workspace_dir, TerraformOperation.APPLY, auto_approve=True
            )
            if not apply_result.success:
                raise InfrastructureError(
                    f"Terraform apply failed: {apply_result.stderr}"
                )

            # Get outputs
            outputs = await self._get_terraform_outputs(workspace_dir)

            # Create deployment state
            deployment_state = DeploymentState(
                muppet_name=config.muppet_name,
                status=DeploymentStatus.COMPLETED,
                terraform_workspace=str(workspace_dir),
                state_backend="local",  # TODO: Implement remote state backend
                last_operation=TerraformOperation.APPLY,
                last_updated=self._get_current_timestamp(),
                outputs=outputs,
            )

            logger.info(
                f"Infrastructure deployment completed for muppet: {config.muppet_name}"
            )
            return deployment_state

        except Exception as e:
            logger.error(
                f"Infrastructure deployment failed for muppet {config.muppet_name}: {e}"
            )

            # Return failed state
            return DeploymentState(
                muppet_name=config.muppet_name,
                status=DeploymentStatus.FAILED,
                terraform_workspace=str(workspace_dir)
                if "workspace_dir" in locals()
                else "",
                state_backend="local",
                last_operation=TerraformOperation.APPLY,
                last_updated=self._get_current_timestamp(),
                outputs={},
                error_message=str(e),
            )

    async def destroy_infrastructure(self, muppet_name: str) -> DeploymentState:
        """
        Destroy infrastructure for a muppet.

        Args:
            muppet_name: Name of the muppet

        Returns:
            Deployment state

        Raises:
            InfrastructureError: If destruction fails
        """
        logger.info(f"Starting infrastructure destruction for muppet: {muppet_name}")

        try:
            workspace_dir = self._get_workspace_path(muppet_name)

            if not workspace_dir.exists():
                logger.warning(
                    f"No workspace found for muppet {muppet_name}, assuming already destroyed"
                )
                return DeploymentState(
                    muppet_name=muppet_name,
                    status=DeploymentStatus.DESTROYED,
                    terraform_workspace="",
                    state_backend="local",
                    last_operation=TerraformOperation.DESTROY,
                    last_updated=self._get_current_timestamp(),
                    outputs={},
                )

            # Destroy infrastructure
            destroy_result = await self._run_terraform(
                workspace_dir, TerraformOperation.DESTROY, auto_approve=True
            )
            if not destroy_result.success:
                raise InfrastructureError(
                    f"Terraform destroy failed: {destroy_result.stderr}"
                )

            # Clean up workspace
            shutil.rmtree(workspace_dir, ignore_errors=True)

            deployment_state = DeploymentState(
                muppet_name=muppet_name,
                status=DeploymentStatus.DESTROYED,
                terraform_workspace="",
                state_backend="local",
                last_operation=TerraformOperation.DESTROY,
                last_updated=self._get_current_timestamp(),
                outputs={},
            )

            logger.info(
                f"Infrastructure destruction completed for muppet: {muppet_name}"
            )
            return deployment_state

        except Exception as e:
            logger.error(
                f"Infrastructure destruction failed for muppet {muppet_name}: {e}"
            )
            raise InfrastructureError(f"Failed to destroy infrastructure: {e}")

    async def get_deployment_status(
        self, muppet_name: str
    ) -> Optional[DeploymentState]:
        """
        Get current deployment status for a muppet.

        Args:
            muppet_name: Name of the muppet

        Returns:
            Deployment state or None if not found
        """
        workspace_dir = self._get_workspace_path(muppet_name)

        if not workspace_dir.exists():
            return None

        try:
            # Check if state file exists
            state_file = workspace_dir / "terraform.tfstate"
            if not state_file.exists():
                return DeploymentState(
                    muppet_name=muppet_name,
                    status=DeploymentStatus.PENDING,
                    terraform_workspace=str(workspace_dir),
                    state_backend="local",
                    last_operation=None,
                    last_updated=self._get_current_timestamp(),
                    outputs={},
                )

            # Get outputs
            outputs = await self._get_terraform_outputs(workspace_dir)

            return DeploymentState(
                muppet_name=muppet_name,
                status=DeploymentStatus.COMPLETED,
                terraform_workspace=str(workspace_dir),
                state_backend="local",
                last_operation=TerraformOperation.APPLY,
                last_updated=self._get_file_timestamp(state_file),
                outputs=outputs,
            )

        except Exception as e:
            logger.error(f"Failed to get deployment status for {muppet_name}: {e}")
            return DeploymentState(
                muppet_name=muppet_name,
                status=DeploymentStatus.FAILED,
                terraform_workspace=str(workspace_dir),
                state_backend="local",
                last_operation=None,
                last_updated=self._get_current_timestamp(),
                outputs={},
                error_message=str(e),
            )

    async def update_module_versions(self, module_versions: Dict[str, str]) -> bool:
        """
        Update Terraform module versions.

        Args:
            module_versions: Dictionary of module names to versions

        Returns:
            True if update was successful

        Raises:
            InfrastructureError: If update fails
        """
        logger.info(f"Updating module versions: {module_versions}")

        try:
            # Validate module versions exist
            for module_name, version in module_versions.items():
                module_path = self.terraform_modules_path / module_name
                if not module_path.exists():
                    raise ValidationError(
                        f"Module {module_name} not found at {module_path}"
                    )

            # TODO: Implement version management (git tags, semantic versioning)
            # For now, we'll use the current module versions

            logger.info("Module versions updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to update module versions: {e}")
            raise InfrastructureError(f"Module version update failed: {e}")

    def get_available_modules(self) -> List[str]:
        """
        Get list of available Terraform modules.

        Returns:
            List of module names
        """
        modules = []

        if not self.terraform_modules_path.exists():
            logger.warning(
                f"Terraform modules path does not exist: {self.terraform_modules_path}"
            )
            return modules

        for item in self.terraform_modules_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Check if it's a valid Terraform module
                if (item / "main.t").exists() or (item / "variables.t").exists():
                    modules.append(item.name)

        logger.debug(f"Found {len(modules)} available modules: {modules}")
        return modules

    def _create_workspace(self, muppet_name: str) -> Path:
        """Create a workspace directory for Terraform operations."""
        workspace_dir = self._get_workspace_path(muppet_name)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir

    def _get_workspace_path(self, muppet_name: str) -> Path:
        """Get the workspace path for a muppet."""
        return self.workspace_path / muppet_name

    async def _generate_terraform_config(
        self, workspace_dir: Path, config: InfrastructureConfig
    ) -> None:
        """Generate Terraform configuration files."""
        logger.debug(f"Generating Terraform configuration for {config.muppet_name}")

        # Generate main.tf
        main_tf_content = self._generate_main_tf(config)
        (workspace_dir / "main.t").write_text(main_tf_content)

        # Generate variables.tf
        variables_tf_content = self._generate_variables_tf(config)
        (workspace_dir / "variables.t").write_text(variables_tf_content)

        # Generate terraform.tfvars
        tfvars_content = self._generate_tfvars(config)
        (workspace_dir / "terraform.tfvars").write_text(tfvars_content)

        logger.debug(f"Terraform configuration generated in {workspace_dir}")

    def _generate_main_tf(self, config: InfrastructureConfig) -> str:
        """Generate main.tf content."""
        return """# Generated Terraform configuration for {config.muppet_name}

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region

  default_tags {{
    tags = {{
      Project     = "muppet-platform"
      Muppet      = var.muppet_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }}
  }}
}}

# Networking Module
module "networking" {{
  source = "{self.terraform_modules_path}/networking"

  name_prefix          = var.muppet_name
  vpc_cidr            = var.vpc_cidr
  public_subnet_count = var.public_subnet_count
  private_subnet_count = var.private_subnet_count
  enable_nat_gateway   = var.enable_nat_gateway
  single_nat_gateway   = var.single_nat_gateway
  enable_vpc_endpoints = var.enable_vpc_endpoints

  tags = local.common_tags
}}

# IAM Module
module "iam" {{
  source = "{self.terraform_modules_path}/iam"

  name_prefix = var.muppet_name

  tags = local.common_tags
}}

# ECR Module
module "ecr" {{
  source = "{self.terraform_modules_path}/ecr"

  registry_name   = var.muppet_name
  enable_scanning = var.enable_ecr_scanning

  tags = local.common_tags
}}

# Fargate Service Module
module "fargate_service" {{
  source = "{self.terraform_modules_path}/fargate-service"

  service_name    = var.muppet_name
  cluster_name    = "${{var.muppet_name}}-cluster"
  container_image = var.container_image
  container_port  = var.container_port

  # Networking
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids

  # Resource allocation
  cpu    = var.fargate_cpu
  memory = var.fargate_memory

  # Scaling
  desired_count            = var.desired_count
  enable_autoscaling       = var.enable_autoscaling
  autoscaling_min_capacity = var.autoscaling_min_capacity
  autoscaling_max_capacity = var.autoscaling_max_capacity

  # Environment variables
  environment_variables = var.environment_variables
  secrets              = var.secrets

  # Health checks
  health_check_path = var.health_check_path

  # Logging
  log_retention_days = var.log_retention_days

  tags = local.common_tags
}}

# Monitoring Module
module "monitoring" {{
  source = "{self.terraform_modules_path}/monitoring"

  service_name   = var.muppet_name
  cluster_name   = module.fargate_service.cluster_name
  log_group_name = module.fargate_service.log_group_name

  # Load balancer metrics
  load_balancer_arn_suffix = module.fargate_service.load_balancer_arn != null ? split("/", module.fargate_service.load_balancer_arn)[1] : ""
  target_group_arn_suffix  = module.fargate_service.target_group_arn != null ? split("/", module.fargate_service.target_group_arn)[1] : ""

  # Alarm configuration
  enable_alarms = var.enable_monitoring_alarms
  alarm_actions = var.alarm_actions

  # Thresholds
  cpu_alarm_threshold          = var.cpu_alarm_threshold
  memory_alarm_threshold       = var.memory_alarm_threshold
  response_time_alarm_threshold = var.response_time_alarm_threshold

  tags = local.common_tags
}}

# Local values
locals {{
  common_tags = {{
    Project     = "muppet-platform"
    Muppet      = var.muppet_name
    Environment = var.environment
    Template    = var.template_name
    ManagedBy   = "terraform"
  }}
}}

# Outputs
output "service_arn" {{
  description = "ARN of the ECS service"
  value       = module.fargate_service.service_arn
}}

output "service_url" {{
  description = "URL to access the service"
  value       = module.fargate_service.service_url
}}

output "load_balancer_dns_name" {{
  description = "DNS name of the load balancer"
  value       = module.fargate_service.load_balancer_dns_name
}}

output "cluster_name" {{
  description = "Name of the ECS cluster"
  value       = module.fargate_service.cluster_name
}}

output "task_definition_arn" {{
  description = "ARN of the task definition"
  value       = module.fargate_service.task_definition_arn
}}

output "log_group_name" {{
  description = "Name of the CloudWatch log group"
  value       = module.fargate_service.log_group_name
}}

output "vpc_id" {{
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}}

output "private_subnet_ids" {{
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}}

output "public_subnet_ids" {{
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}}

output "ecr_repository_url" {{
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}}
"""

    def _generate_variables_tf(self, config: InfrastructureConfig) -> str:
        """Generate variables.tf content."""
        return """# Variables for muppet infrastructure

# Basic Configuration
variable "muppet_name" {
  description = "Name of the muppet"
  type        = string
}

variable "template_name" {
  description = "Template used for the muppet"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"
}

# Container Configuration
variable "container_image" {
  description = "Docker image for the muppet"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 3000
}

# Networking Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_count" {
  description = "Number of public subnets"
  type        = number
  default     = 2
}

variable "private_subnet_count" {
  description = "Number of private subnets"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway for cost optimization"
  type        = bool
  default     = false
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints"
  type        = bool
  default     = true
}

# Fargate Configuration
variable "fargate_cpu" {
  description = "CPU units for Fargate task"
  type        = number
  default     = 256
}

variable "fargate_memory" {
  description = "Memory for Fargate task"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "enable_autoscaling" {
  description = "Enable auto scaling"
  type        = bool
  default     = true
}

variable "autoscaling_min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

# Environment Variables
variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets for the container"
  type        = map(string)
  default     = {}
}

# Health Check Configuration
variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/health"
}

# Logging Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention days"
  type        = number
  default     = 7
}

# ECR Configuration
variable "enable_ecr_scanning" {
  description = "Enable ECR image scanning"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "enable_monitoring_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "SNS topic ARNs for alarm notifications"
  type        = list(string)
  default     = []
}

variable "cpu_alarm_threshold" {
  description = "CPU alarm threshold percentage"
  type        = number
  default     = 80
}

variable "memory_alarm_threshold" {
  description = "Memory alarm threshold percentage"
  type        = number
  default     = 85
}

variable "response_time_alarm_threshold" {
  description = "Response time alarm threshold in seconds"
  type        = number
  default     = 2.0
}
"""

    def _generate_tfvars(self, config: InfrastructureConfig) -> str:
        """Generate terraform.tfvars content."""
        # Build environment variables
        env_vars = {
            "ENVIRONMENT": config.environment,
            "AWS_REGION": config.aws_region,
            "PORT": str(config.fargate_config.get("container_port", 3000)),
        }
        env_vars.update(config.variables.get("environment_variables", {}))

        # Format environment variables for Terraform
        env_vars_tf = "{\n"
        for key, value in env_vars.items():
            env_vars_tf += f'    "{key}" = "{value}"\n'
        env_vars_tf += "  }"

        return """# Terraform variables for {config.muppet_name}

# Basic Configuration
muppet_name   = "{config.muppet_name}"
template_name = "{config.template_name}"
aws_region    = "{config.aws_region}"
environment   = "{config.environment}"

# Container Configuration
container_image = "{config.fargate_config.get('container_image', 'nginx:latest')}"
container_port  = {config.fargate_config.get('container_port', 3000)}

# Networking Configuration
vpc_cidr             = "{config.vpc_config.get('vpc_cidr', '10.0.0.0/16')}"
public_subnet_count  = {config.vpc_config.get('public_subnet_count', 2)}
private_subnet_count = {config.vpc_config.get('private_subnet_count', 2)}
enable_nat_gateway   = {str(config.vpc_config.get('enable_nat_gateway', True)).lower()}
single_nat_gateway   = {str(config.vpc_config.get('single_nat_gateway', False)).lower()}
enable_vpc_endpoints = {str(config.vpc_config.get('enable_vpc_endpoints', True)).lower()}

# Fargate Configuration
fargate_cpu    = {config.fargate_config.get('cpu', 256)}
fargate_memory = {config.fargate_config.get('memory', 512)}
desired_count  = {config.fargate_config.get('desired_count', 1)}

# Auto Scaling
enable_autoscaling       = {str(config.fargate_config.get('enable_autoscaling', True)).lower()}
autoscaling_min_capacity = {config.fargate_config.get('autoscaling_min_capacity', 1)}
autoscaling_max_capacity = {config.fargate_config.get('autoscaling_max_capacity', 10)}

# Environment Variables
environment_variables = {env_vars_tf}

# Health Check
health_check_path = "{config.fargate_config.get('health_check_path', '/health')}"

# Logging
log_retention_days = {config.monitoring_config.get('log_retention_days', 7)}

# Monitoring
enable_monitoring_alarms      = {str(config.monitoring_config.get('enable_alarms', True)).lower()}
cpu_alarm_threshold          = {config.monitoring_config.get('cpu_alarm_threshold', 80)}
memory_alarm_threshold       = {config.monitoring_config.get('memory_alarm_threshold', 85)}
response_time_alarm_threshold = {config.monitoring_config.get('response_time_alarm_threshold', 2.0)}
"""

    async def _run_terraform(
        self,
        workspace_dir: Path,
        operation: TerraformOperation,
        auto_approve: bool = False,
    ) -> TerraformOutput:
        """Run a Terraform command."""
        logger.debug(f"Running terraform {operation.value} in {workspace_dir}")

        # Build command
        cmd = ["terraform", operation.value]

        if operation == TerraformOperation.APPLY and auto_approve:
            cmd.append("-auto-approve")
        elif operation == TerraformOperation.DESTROY and auto_approve:
            cmd.append("-auto-approve")
        elif operation == TerraformOperation.PLAN:
            cmd.extend(["-out", "tfplan"])

        # Set environment variables
        env = os.environ.copy()
        env["TF_IN_AUTOMATION"] = "true"
        env["TF_INPUT"] = "false"

        try:
            # Run command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=workspace_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            result = TerraformOutput(
                success=process.returncode == 0,
                stdout=stdout.decode("utf-8"),
                stderr=stderr.decode("utf-8"),
                exit_code=process.returncode,
                operation=operation,
            )

            if result.success:
                logger.debug(f"Terraform {operation.value} completed successfully")
            else:
                logger.error(
                    f"Terraform {operation.value} failed with exit code {result.exit_code}"
                )
                logger.error(f"Stderr: {result.stderr}")

            return result

        except Exception as e:
            logger.error(f"Failed to run terraform {operation.value}: {e}")
            return TerraformOutput(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                operation=operation,
            )

    async def _get_terraform_outputs(self, workspace_dir: Path) -> Dict[str, Any]:
        """Get Terraform outputs."""
        try:
            process = await asyncio.create_subprocess_exec(
                "terraform",
                "output",
                "-json",
                cwd=workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                outputs_raw = json.loads(stdout.decode("utf-8"))
                # Extract values from Terraform output format
                outputs = {}
                for key, value in outputs_raw.items():
                    outputs[key] = value.get("value")
                return outputs
            else:
                logger.warning(
                    f"Failed to get Terraform outputs: {stderr.decode('utf-8')}"
                )
                return {}

        except Exception as e:
            logger.error(f"Error getting Terraform outputs: {e}")
            return {}

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def _get_file_timestamp(self, file_path: Path) -> str:
        """Get file modification timestamp as ISO string."""
        from datetime import datetime

        timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
        return timestamp.isoformat() + "Z"
