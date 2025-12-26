"""
Deployment Service for the Muppet Platform.

This service orchestrates the complete deployment process for muppets,
including container deployment to AWS Fargate, load balancer configuration,
and health monitoring setup.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..exceptions import DeploymentError, ValidationError
from ..integrations.aws import get_ecr_client, get_ecs_client
from ..logging_config import get_logger
from ..managers.github_manager import GitHubManager
from ..managers.infrastructure_manager import InfrastructureConfig as InfraConfig
from ..managers.infrastructure_manager import InfrastructureManager
from ..models import Muppet, MuppetStatus

logger = get_logger(__name__)


class DeploymentService:
    """
    High-level deployment service for muppet Fargate deployments.

    This service orchestrates the complete deployment process:
    1. Container image preparation and ECR push
    2. Infrastructure provisioning via Terraform
    3. Fargate service deployment and configuration
    4. Load balancer and networking setup
    5. Health monitoring and auto-scaling configuration
    """

    def __init__(self):
        self.settings = get_settings()
        self.infrastructure_manager = InfrastructureManager()
        self.github_manager = GitHubManager()
        logger.info("Initialized Deployment Service")

    async def deploy_muppet(
        self,
        muppet: Muppet,
        container_image: str,
        environment_variables: Optional[Dict[str, str]] = None,
        secrets: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Deploy a muppet to AWS Fargate.

        This method handles the complete deployment process:
        1. Validate deployment requirements
        2. Create infrastructure configuration
        3. Deploy infrastructure via Terraform
        4. Configure Fargate service
        5. Set up monitoring and health checks
        6. Update muppet status

        Args:
            muppet: Muppet instance to deploy
            container_image: Docker image URI for the muppet
            environment_variables: Environment variables for the container
            secrets: Secrets for the container (Parameter Store/Secrets Manager ARNs)

        Returns:
            Deployment information including service ARN, load balancer URL, etc.

        Raises:
            DeploymentError: If deployment fails
            ValidationError: If input parameters are invalid
        """
        try:
            logger.info(f"Starting Fargate deployment for muppet: {muppet.name}")

            # Update muppet status to creating
            muppet.status = MuppetStatus.CREATING
            await self.github_manager.update_muppet_status(muppet.name, "creating")

            # Validate deployment requirements
            await self._validate_deployment_requirements(muppet, container_image)

            # Create infrastructure configuration
            infra_config = self._create_infrastructure_config(
                muppet, container_image, environment_variables, secrets
            )

            # Deploy infrastructure
            deployment_state = await self.infrastructure_manager.deploy_infrastructure(
                infra_config
            )

            if deployment_state.status.value != "completed":
                raise DeploymentError(
                    f"Infrastructure deployment failed: {deployment_state.error_message}",
                    details={
                        "muppet_name": muppet.name,
                        "deployment_status": deployment_state.status.value,
                        "error": deployment_state.error_message,
                    },
                )

            # Extract deployment information from Terraform outputs
            deployment_info = self._extract_deployment_info(deployment_state.outputs)

            # Update muppet with deployment information
            muppet.fargate_service_arn = deployment_info.get("service_arn")
            muppet.status = MuppetStatus.RUNNING
            muppet.updated_at = datetime.utcnow()

            # Update GitHub status
            await self.github_manager.update_muppet_status(muppet.name, "running")

            # Wait for service to be stable
            await self._wait_for_service_stable(deployment_info.get("service_arn"))

            logger.info(f"Successfully deployed muppet {muppet.name} to Fargate")

            return {
                "muppet_name": muppet.name,
                "status": "deployed",
                "service_arn": deployment_info.get("service_arn"),
                "service_url": deployment_info.get("service_url"),
                "load_balancer_dns": deployment_info.get("load_balancer_dns"),
                "cluster_name": deployment_info.get("cluster_name"),
                "task_definition_arn": deployment_info.get("task_definition_arn"),
                "log_group_name": deployment_info.get("log_group_name"),
                "deployed_at": datetime.utcnow().isoformat(),
            }

        except (DeploymentError, ValidationError):
            # Update muppet status to error
            muppet.status = MuppetStatus.ERROR
            await self.github_manager.update_muppet_status(muppet.name, "error")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during deployment of {muppet.name}: {e}")
            muppet.status = MuppetStatus.ERROR
            await self.github_manager.update_muppet_status(muppet.name, "error")
            raise DeploymentError(
                f"Deployment failed with unexpected error: {str(e)}",
                details={"muppet_name": muppet.name},
            )

    async def undeploy_muppet(self, muppet_name: str) -> Dict[str, Any]:
        """
        Undeploy a muppet from AWS Fargate.

        This method handles the complete undeployment process:
        1. Update muppet status to deleting
        2. Destroy Fargate service and infrastructure
        3. Clean up resources
        4. Update muppet status

        Args:
            muppet_name: Name of the muppet to undeploy

        Returns:
            Undeployment information

        Raises:
            DeploymentError: If undeployment fails
        """
        try:
            logger.info(f"Starting Fargate undeployment for muppet: {muppet_name}")

            # Update status to deleting
            await self.github_manager.update_muppet_status(muppet_name, "deleting")

            # Destroy infrastructure
            deployment_state = await self.infrastructure_manager.destroy_infrastructure(
                muppet_name
            )

            if deployment_state.status.value != "destroyed":
                raise DeploymentError(
                    f"Infrastructure destruction failed: {deployment_state.error_message}",
                    details={
                        "muppet_name": muppet_name,
                        "deployment_status": deployment_state.status.value,
                        "error": deployment_state.error_message,
                    },
                )

            logger.info(f"Successfully undeployed muppet {muppet_name} from Fargate")

            return {
                "muppet_name": muppet_name,
                "status": "undeployed",
                "undeployed_at": datetime.utcnow().isoformat(),
            }

        except DeploymentError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during undeployment of {muppet_name}: {e}")
            raise DeploymentError(
                f"Undeployment failed with unexpected error: {str(e)}",
                details={"muppet_name": muppet_name},
            )

    async def get_deployment_status(self, muppet_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the current deployment status of a muppet.

        Args:
            muppet_name: Name of the muppet

        Returns:
            Deployment status information or None if not deployed
        """
        try:
            logger.debug(f"Getting deployment status for muppet: {muppet_name}")

            deployment_state = await self.infrastructure_manager.get_deployment_status(
                muppet_name
            )

            if not deployment_state:
                return None

            # Get additional service information from ECS
            service_info = await self._get_service_info(
                deployment_state.outputs.get("service_arn")
            )

            return {
                "muppet_name": muppet_name,
                "deployment_status": deployment_state.status.value,
                "service_arn": deployment_state.outputs.get("service_arn"),
                "service_url": deployment_state.outputs.get("service_url"),
                "cluster_name": deployment_state.outputs.get("cluster_name"),
                "task_definition_arn": deployment_state.outputs.get(
                    "task_definition_arn"
                ),
                "desired_count": service_info.get("desired_count", 0),
                "running_count": service_info.get("running_count", 0),
                "pending_count": service_info.get("pending_count", 0),
                "last_updated": deployment_state.last_updated,
                "health_status": service_info.get("health_status", "unknown"),
            }

        except Exception as e:
            logger.error(f"Failed to get deployment status for {muppet_name}: {e}")
            return None

    async def scale_muppet(
        self,
        muppet_name: str,
        desired_count: int,
        min_capacity: Optional[int] = None,
        max_capacity: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Scale a muppet deployment.

        Args:
            muppet_name: Name of the muppet to scale
            desired_count: Desired number of tasks
            min_capacity: Minimum capacity for auto-scaling (optional)
            max_capacity: Maximum capacity for auto-scaling (optional)

        Returns:
            Scaling operation result

        Raises:
            DeploymentError: If scaling fails
        """
        try:
            logger.info(f"Scaling muppet {muppet_name} to {desired_count} tasks")

            # Get current deployment status
            deployment_status = await self.get_deployment_status(muppet_name)
            if not deployment_status:
                raise DeploymentError(
                    f"Muppet {muppet_name} is not deployed",
                    details={"muppet_name": muppet_name},
                )

            service_arn = deployment_status["service_arn"]
            cluster_name = deployment_status["cluster_name"]

            # Update ECS service desired count
            ecs_client = await get_ecs_client()

            await ecs_client.update_service(
                cluster=cluster_name, service=service_arn, desiredCount=desired_count
            )

            # Update auto-scaling configuration if provided
            if min_capacity is not None or max_capacity is not None:
                await self._update_autoscaling_config(
                    muppet_name, min_capacity, max_capacity
                )

            logger.info(f"Successfully scaled muppet {muppet_name}")

            return {
                "muppet_name": muppet_name,
                "desired_count": desired_count,
                "min_capacity": min_capacity,
                "max_capacity": max_capacity,
                "scaled_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to scale muppet {muppet_name}: {e}")
            raise DeploymentError(
                f"Scaling failed: {str(e)}",
                details={"muppet_name": muppet_name, "desired_count": desired_count},
            )

    async def get_muppet_logs(
        self, muppet_name: str, lines: int = 100, start_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get logs for a muppet deployment.

        Args:
            muppet_name: Name of the muppet
            lines: Number of log lines to retrieve
            start_time: Start time for log retrieval (optional)

        Returns:
            List of log entries

        Raises:
            DeploymentError: If log retrieval fails
        """
        try:
            logger.debug(f"Getting logs for muppet: {muppet_name}")

            deployment_status = await self.get_deployment_status(muppet_name)
            if not deployment_status:
                raise DeploymentError(
                    f"Muppet {muppet_name} is not deployed",
                    details={"muppet_name": muppet_name},
                )

            # Get log group name from deployment outputs
            deployment_state = await self.infrastructure_manager.get_deployment_status(
                muppet_name
            )
            log_group_name = deployment_state.outputs.get("log_group_name")

            if not log_group_name:
                raise DeploymentError(
                    f"Log group not found for muppet {muppet_name}",
                    details={"muppet_name": muppet_name},
                )

            # Get logs from CloudWatch
            logs = await self._get_cloudwatch_logs(log_group_name, lines, start_time)

            return logs

        except DeploymentError:
            raise
        except Exception as e:
            logger.error(f"Failed to get logs for muppet {muppet_name}: {e}")
            raise DeploymentError(
                f"Log retrieval failed: {str(e)}", details={"muppet_name": muppet_name}
            )

    def _create_infrastructure_config(
        self,
        muppet: Muppet,
        container_image: str,
        environment_variables: Optional[Dict[str, str]] = None,
        secrets: Optional[Dict[str, str]] = None,
    ) -> InfraConfig:
        """Create infrastructure configuration for deployment."""

        # Default environment variables
        default_env_vars = {
            "ENVIRONMENT": "production",
            "AWS_REGION": self.settings.aws.region,
            "PORT": str(muppet.port),
            "MUPPET_NAME": muppet.name,
            "TEMPLATE": muppet.template,
        }

        if environment_variables:
            default_env_vars.update(environment_variables)

        # VPC configuration
        vpc_config = {
            "vpc_cidr": self.settings.aws.vpc_cidr,
            "public_subnet_count": 2,
            "private_subnet_count": 2,
            "enable_nat_gateway": True,
            "single_nat_gateway": False,  # Use multiple NAT gateways for HA
            "enable_vpc_endpoints": True,
        }

        # Fargate configuration
        fargate_config = {
            "container_image": container_image,
            "container_port": muppet.port,
            "cpu": 256,  # 0.25 vCPU
            "memory": 512,  # 512 MB
            "desired_count": 1,
            "enable_autoscaling": True,
            "autoscaling_min_capacity": 1,
            "autoscaling_max_capacity": 10,
            "health_check_path": "/health",
        }

        # Monitoring configuration
        monitoring_config = {
            "log_retention_days": self.settings.monitoring.cloudwatch_log_retention_days,
            "enable_alarms": self.settings.monitoring.cloudwatch_alarms_enabled,
            "cpu_alarm_threshold": 80,
            "memory_alarm_threshold": 85,
            "response_time_alarm_threshold": 2.0,
        }

        # Module versions (use latest for now)
        module_versions = {
            "networking": "1.0.0",
            "fargate-service": "1.0.0",
            "monitoring": "1.0.0",
            "iam": "1.0.0",
            "ecr": "1.0.0",
        }

        return InfraConfig(
            muppet_name=muppet.name,
            template_name=muppet.template,
            aws_region=self.settings.aws.region,
            environment="production",
            module_versions=module_versions,
            vpc_config=vpc_config,
            fargate_config=fargate_config,
            monitoring_config=monitoring_config,
            variables={
                "environment_variables": default_env_vars,
                "secrets": secrets or {},
            },
        )

    async def _validate_deployment_requirements(
        self, muppet: Muppet, container_image: str
    ) -> None:
        """Validate deployment requirements."""

        # Validate muppet
        if not muppet.name:
            raise ValidationError("Muppet name is required")

        if not muppet.template:
            raise ValidationError("Muppet template is required")

        # Validate container image
        if not container_image:
            raise ValidationError("Container image is required")

        # Validate container image exists in ECR
        try:
            ecr_client = await get_ecr_client()

            # Parse image URI
            if "/" in container_image:
                repository_name = container_image.split("/")[-1].split(":")[0]
            else:
                repository_name = container_image.split(":")[0]

            # Check if repository exists
            response = await ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )

            if not response.get("repositories"):
                raise ValidationError(
                    f"ECR repository not found: {repository_name}",
                    details={"container_image": container_image},
                )

        except Exception as e:
            logger.warning(f"Could not validate ECR repository: {e}")
            # Continue with deployment - ECR validation is not critical

    def _extract_deployment_info(
        self, terraform_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract deployment information from Terraform outputs."""
        return {
            "service_arn": terraform_outputs.get("service_arn"),
            "service_url": terraform_outputs.get("service_url"),
            "load_balancer_dns": terraform_outputs.get("load_balancer_dns_name"),
            "cluster_name": terraform_outputs.get("cluster_name"),
            "task_definition_arn": terraform_outputs.get("task_definition_arn"),
            "log_group_name": terraform_outputs.get("log_group_name"),
        }

    async def _wait_for_service_stable(
        self, service_arn: Optional[str], timeout: int = 600
    ) -> None:
        """Wait for ECS service to become stable."""
        if not service_arn:
            logger.warning("No service ARN provided, skipping stability check")
            return

        try:
            logger.info(f"Waiting for service to become stable: {service_arn}")

            ecs_client = await get_ecs_client()

            # Extract cluster and service names from ARN
            arn_parts = service_arn.split("/")
            if len(arn_parts) >= 2:
                cluster_name = arn_parts[-2]
                service_name = arn_parts[-1]
            else:
                logger.warning(f"Could not parse service ARN: {service_arn}")
                return

            # Wait for service to be stable
            waiter = ecs_client.get_waiter("services_stable")
            await waiter.wait(
                cluster=cluster_name,
                services=[service_name],
                WaiterConfig={"Delay": 15, "MaxAttempts": timeout // 15},
            )

            logger.info(f"Service is now stable: {service_arn}")

        except Exception as e:
            logger.warning(f"Failed to wait for service stability: {e}")
            # Don't fail deployment if stability check fails

    async def _get_service_info(self, service_arn: Optional[str]) -> Dict[str, Any]:
        """Get ECS service information."""
        if not service_arn:
            return {}

        try:
            ecs_client = await get_ecs_client()

            # Extract cluster and service names from ARN
            arn_parts = service_arn.split("/")
            if len(arn_parts) >= 2:
                cluster_name = arn_parts[-2]
                service_name = arn_parts[-1]
            else:
                return {}

            response = await ecs_client.describe_services(
                cluster=cluster_name, services=[service_name]
            )

            services = response.get("services", [])
            if not services:
                return {}

            service = services[0]

            return {
                "desired_count": service.get("desiredCount", 0),
                "running_count": service.get("runningCount", 0),
                "pending_count": service.get("pendingCount", 0),
                "health_status": "healthy"
                if service.get("runningCount", 0) > 0
                else "unhealthy",
            }

        except Exception as e:
            logger.error(f"Failed to get service info: {e}")
            return {}

    async def _update_autoscaling_config(
        self, muppet_name: str, min_capacity: Optional[int], max_capacity: Optional[int]
    ) -> None:
        """Update auto-scaling configuration."""
        # TODO: Implement auto-scaling configuration update
        # This would involve updating the Application Auto Scaling target
        logger.info(f"Auto-scaling config update not yet implemented for {muppet_name}")

    async def _get_cloudwatch_logs(
        self, log_group_name: str, lines: int, start_time: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get logs from CloudWatch."""
        # TODO: Implement CloudWatch logs retrieval
        # This would involve using the CloudWatch Logs client
        logger.info(
            f"CloudWatch logs retrieval not yet implemented for {log_group_name}"
        )
        return []

    async def close(self) -> None:
        """Close service connections."""
        await self.github_manager.close()
        logger.debug("Closed Deployment Service")
