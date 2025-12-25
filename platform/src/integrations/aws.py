"""
AWS service integrations for the Muppet Platform.

This module provides functionality to interact with AWS services including
Parameter Store, ECS, and other AWS APIs.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
import json

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

from ..config import get_settings
from ..exceptions import AWSError
from ..logging_config import get_logger

logger = get_logger(__name__)


class ParameterStoreClient:
    """
    AWS Systems Manager Parameter Store client.

    Handles configuration storage and retrieval from Parameter Store
    with hierarchical parameter organization.
    """

    def __init__(self):
        self.settings = get_settings()
        self.region = self.settings.aws.region
        self.parameter_prefix = "/muppet-platform"
        self.integration_mode = self.settings.integration_mode

        try:
            # Configure boto3 client based on integration mode
            client_config = {"region_name": self.region}

            # Use custom endpoint for LocalStack in local mode
            if self.integration_mode == "local" and self.settings.aws_endpoint_url:
                client_config["endpoint_url"] = self.settings.aws_endpoint_url
                logger.info(
                    f"Initialized Parameter Store client in LOCAL mode (LocalStack) for region: {self.region}"
                )
            elif self.integration_mode == "real":
                logger.info(
                    f"Initialized Parameter Store client in REAL mode for region: {self.region}"
                )
            else:
                logger.info(
                    f"Initialized Parameter Store client in MOCK mode for region: {self.region}"
                )

            self.ssm_client = boto3.client("ssm", **client_config)

        except NoCredentialsError:
            if self.integration_mode == "real":
                logger.error("AWS credentials not found for real integration mode")
                raise AWSError(
                    message="AWS credentials not configured for real integration mode",
                    service="ssm",
                    details={"region": self.region, "mode": self.integration_mode},
                )
            else:
                logger.warning("AWS credentials not found, using mock mode")
                self.ssm_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Parameter Store client: {e}")
            if self.integration_mode == "real":
                raise AWSError(
                    message=f"Failed to initialize Parameter Store client: {str(e)}",
                    service="ssm",
                    details={"region": self.region, "mode": self.integration_mode},
                )
            else:
                logger.warning(
                    f"Parameter Store client initialization failed, using mock mode: {e}"
                )
                self.ssm_client = None

    async def get_parameter(self, name: str, decrypt: bool = False) -> Optional[str]:
        """
        Get a single parameter value.

        Args:
            name: Parameter name (without prefix)
            decrypt: Whether to decrypt SecureString parameters

        Returns:
            Parameter value or None if not found

        Raises:
            AWSError: If Parameter Store operation fails
        """
        try:
            full_name = f"{self.parameter_prefix}/{name.lstrip('/')}"
            logger.debug(f"Getting parameter: {full_name}")

            if not self.ssm_client:
                # Mock mode
                logger.info(f"MOCK: Would get parameter {full_name}")
                # Return mock values for common parameters
                if "terraform/modules" in name:
                    return "1.0.0"
                elif "github/token" in name:
                    return "mock-github-token"
                else:
                    return f"mock-value-for-{name}"

            # Use asyncio to run the synchronous boto3 call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ssm_client.get_parameter(
                    Name=full_name, WithDecryption=decrypt
                ),
            )

            value = response["Parameter"]["Value"]
            logger.debug(f"Retrieved parameter: {full_name}")
            return value

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ParameterNotFound":
                logger.debug(f"Parameter not found: {full_name}")
                return None
            else:
                logger.error(f"AWS error getting parameter {name}: {e}")
                raise AWSError(
                    message=f"Failed to get parameter: {e.response['Error']['Message']}",
                    service="ssm",
                    details={"parameter": name, "error_code": error_code},
                )
        except Exception as e:
            logger.error(f"Failed to get parameter {name}: {e}")
            raise AWSError(
                message=f"Failed to get parameter: {str(e)}",
                service="ssm",
                details={"parameter": name},
            )

    async def get_parameters_by_path(
        self, path: str, recursive: bool = True
    ) -> Dict[str, str]:
        """
        Get multiple parameters by path prefix.

        Args:
            path: Parameter path prefix
            recursive: Whether to retrieve parameters recursively

        Returns:
            Dictionary of parameter names to values

        Raises:
            AWSError: If Parameter Store operation fails
        """
        try:
            full_path = f"{self.parameter_prefix}/{path.lstrip('/')}"
            logger.debug(f"Getting parameters by path: {full_path}")

            parameters = {}

            # Use asyncio to run the synchronous boto3 paginator
            def get_parameters_sync():
                paginator = self.ssm_client.get_paginator("get_parameters_by_path")
                params = {}
                for page in paginator.paginate(
                    Path=full_path, Recursive=recursive, WithDecryption=True
                ):
                    for param in page.get("Parameters", []):
                        # Remove the full prefix to get relative name
                        relative_name = param["Name"][
                            len(self.parameter_prefix) :
                        ].lstrip("/")
                        params[relative_name] = param["Value"]
                return params

            parameters = await asyncio.get_event_loop().run_in_executor(
                None, get_parameters_sync
            )

            logger.debug(
                f"Retrieved {len(parameters)} parameters from path: {full_path}"
            )
            return parameters

        except ClientError as e:
            logger.error(f"AWS error getting parameters by path {path}: {e}")
            raise AWSError(
                message=f"Failed to get parameters by path: {e.response['Error']['Message']}",
                service="ssm",
                details={"path": path, "error_code": e.response["Error"]["Code"]},
            )
        except Exception as e:
            logger.error(f"Failed to get parameters by path {path}: {e}")
            raise AWSError(
                message=f"Failed to get parameters by path: {str(e)}",
                service="ssm",
                details={"path": path},
            )

    async def put_parameter(
        self,
        name: str,
        value: str,
        parameter_type: str = "String",
        overwrite: bool = True,
    ) -> bool:
        """
        Store a parameter value.

        Args:
            name: Parameter name (without prefix)
            value: Parameter value
            parameter_type: Parameter type (String, StringList, SecureString)
            overwrite: Whether to overwrite existing parameter

        Returns:
            True if parameter was stored successfully

        Raises:
            AWSError: If Parameter Store operation fails
        """
        try:
            full_name = f"{self.parameter_prefix}/{name.lstrip('/')}"
            logger.debug(f"Storing parameter: {full_name}")

            # Use asyncio to run the synchronous boto3 call
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.ssm_client.put_parameter(
                    Name=full_name,
                    Value=value,
                    Type=parameter_type,
                    Overwrite=overwrite,
                ),
            )

            logger.debug(f"Stored parameter: {full_name}")
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ParameterAlreadyExists" and not overwrite:
                raise AWSError(
                    message=f"Parameter already exists: {full_name}",
                    service="ssm",
                    details={"parameter": name, "error_code": error_code},
                )
            else:
                logger.error(f"AWS error storing parameter {name}: {e}")
                raise AWSError(
                    message=f"Failed to store parameter: {e.response['Error']['Message']}",
                    service="ssm",
                    details={"parameter": name, "error_code": error_code},
                )
        except Exception as e:
            logger.error(f"Failed to store parameter {name}: {e}")
            raise AWSError(
                message=f"Failed to store parameter: {str(e)}",
                service="ssm",
                details={"parameter": name},
            )

    async def delete_parameter(self, name: str) -> bool:
        """
        Delete a parameter.

        Args:
            name: Parameter name (without prefix)

        Returns:
            True if parameter was deleted successfully

        Raises:
            AWSError: If Parameter Store operation fails
        """
        try:
            full_name = f"{self.parameter_prefix}/{name.lstrip('/')}"
            logger.debug(f"Deleting parameter: {full_name}")

            # Use asyncio to run the synchronous boto3 call
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.ssm_client.delete_parameter(Name=full_name)
            )

            logger.debug(f"Deleted parameter: {full_name}")
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ParameterNotFound":
                logger.debug(f"Parameter not found for deletion: {full_name}")
                return False
            else:
                logger.error(f"AWS error deleting parameter {name}: {e}")
                raise AWSError(
                    message=f"Failed to delete parameter: {e.response['Error']['Message']}",
                    service="ssm",
                    details={"parameter": name, "error_code": error_code},
                )
        except Exception as e:
            logger.error(f"Failed to delete parameter {name}: {e}")
            raise AWSError(
                message=f"Failed to delete parameter: {str(e)}",
                service="ssm",
                details={"parameter": name},
            )


class ECSClient:
    """
    Amazon ECS client for service discovery and management.

    Handles ECS service operations and status monitoring.
    """

    def __init__(self):
        self.settings = get_settings()
        self.region = self.settings.aws.region
        self.cluster_name = self.settings.aws.fargate_cluster_name

        try:
            self.ecs_client = boto3.client("ecs", region_name=self.region)
            logger.info(f"Initialized ECS client for cluster: {self.cluster_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise AWSError(
                message="AWS credentials not configured",
                service="ecs",
                details={"region": self.region},
            )
        except Exception as e:
            logger.error(f"Failed to initialize ECS client: {e}")
            raise AWSError(
                message=f"Failed to initialize ECS client: {str(e)}",
                service="ecs",
                details={"region": self.region},
            )

    async def list_services(self) -> List[Dict[str, Any]]:
        """
        List all services in the ECS cluster.

        Returns:
            List of service information dictionaries

        Raises:
            AWSError: If ECS operation fails
        """
        try:
            logger.debug(f"Listing services in cluster: {self.cluster_name}")

            # Use asyncio to run the synchronous boto3 calls
            def list_services_sync():
                # Get list of service ARNs
                response = self.ecs_client.list_services(cluster=self.cluster_name)
                service_arns = response.get("serviceArns", [])

                if not service_arns:
                    return []

                # Get detailed service information
                services_response = self.ecs_client.describe_services(
                    cluster=self.cluster_name, services=service_arns
                )

                services = []
                for service in services_response.get("services", []):
                    service_info = {
                        "serviceName": service["serviceName"],
                        "serviceArn": service["serviceArn"],
                        "status": service["status"],
                        "runningCount": service["runningCount"],
                        "desiredCount": service["desiredCount"],
                        "taskDefinition": service["taskDefinition"],
                        "createdAt": service.get("createdAt"),
                        "platformVersion": service.get("platformVersion"),
                        "launchType": service.get("launchType", "FARGATE"),
                    }
                    services.append(service_info)

                return services

            services = await asyncio.get_event_loop().run_in_executor(
                None, list_services_sync
            )

            logger.debug(f"Found {len(services)} services")
            return services

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ClusterNotFoundException":
                logger.warning(f"ECS cluster not found: {self.cluster_name}")
                return []
            else:
                logger.error(f"AWS error listing ECS services: {e}")
                raise AWSError(
                    message=f"Failed to list ECS services: {e.response['Error']['Message']}",
                    service="ecs",
                    details={"cluster": self.cluster_name, "error_code": error_code},
                )
        except Exception as e:
            logger.error(f"Failed to list ECS services: {e}")
            raise AWSError(
                message=f"Failed to list ECS services: {str(e)}",
                service="ecs",
                details={"cluster": self.cluster_name},
            )

    async def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific service.

        Args:
            service_name: Name of the ECS service

        Returns:
            Service information or None if not found

        Raises:
            AWSError: If ECS operation fails
        """
        try:
            logger.debug(f"Getting service: {service_name}")

            # Use asyncio to run the synchronous boto3 call
            def get_service_sync():
                response = self.ecs_client.describe_services(
                    cluster=self.cluster_name, services=[service_name]
                )

                services = response.get("services", [])
                if not services:
                    return None

                service = services[0]
                return {
                    "serviceName": service["serviceName"],
                    "serviceArn": service["serviceArn"],
                    "status": service["status"],
                    "runningCount": service["runningCount"],
                    "desiredCount": service["desiredCount"],
                    "taskDefinition": service["taskDefinition"],
                    "createdAt": service.get("createdAt"),
                    "platformVersion": service.get("platformVersion"),
                    "launchType": service.get("launchType", "FARGATE"),
                }

            service_info = await asyncio.get_event_loop().run_in_executor(
                None, get_service_sync
            )

            if service_info:
                logger.debug(f"Found service: {service_name}")
            else:
                logger.debug(f"Service not found: {service_name}")

            return service_info

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ["ClusterNotFoundException", "ServiceNotFoundException"]:
                logger.debug(f"Service not found: {service_name}")
                return None
            else:
                logger.error(f"AWS error getting ECS service {service_name}: {e}")
                raise AWSError(
                    message=f"Failed to get ECS service: {e.response['Error']['Message']}",
                    service="ecs",
                    details={"service": service_name, "error_code": error_code},
                )
        except Exception as e:
            logger.error(f"Failed to get ECS service {service_name}: {e}")
            raise AWSError(
                message=f"Failed to get ECS service: {str(e)}",
                service="ecs",
                details={"service": service_name},
            )

    async def get_active_deployments(self) -> Dict[str, str]:
        """
        Get mapping of active muppet deployments.

        Returns:
            Dictionary mapping muppet names to service ARNs

        Raises:
            AWSError: If ECS operation fails
        """
        try:
            logger.debug("Getting active deployments")

            services = await self.list_services()
            deployments = {}

            for service in services:
                if (
                    service["status"] == "ACTIVE"
                    and service["runningCount"] > 0
                    and service["desiredCount"] > 0
                ):
                    deployments[service["serviceName"]] = service["serviceArn"]

            logger.debug(f"Found {len(deployments)} active deployments")
            return deployments

        except Exception as e:
            logger.error(f"Failed to get active deployments: {e}")
            raise AWSError(
                message=f"Failed to get active deployments: {str(e)}",
                service="ecs",
                details={"cluster": self.cluster_name},
            )


class ECRClient:
    """
    Amazon ECR client for container registry operations.

    Handles ECR repository management and image operations.
    """

    def __init__(self):
        self.settings = get_settings()
        self.region = self.settings.aws.region

        try:
            self.ecr_client = boto3.client("ecr", region_name=self.region)
            logger.info(f"Initialized ECR client for region: {self.region}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise AWSError(
                message="AWS credentials not configured",
                service="ecr",
                details={"region": self.region},
            )
        except Exception as e:
            logger.error(f"Failed to initialize ECR client: {e}")
            raise AWSError(
                message=f"Failed to initialize ECR client: {str(e)}",
                service="ecr",
                details={"region": self.region},
            )

    async def describe_repositories(
        self, repository_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Describe ECR repositories.

        Args:
            repository_names: List of repository names to describe (optional)

        Returns:
            List of repository information

        Raises:
            AWSError: If ECR operation fails
        """
        try:
            logger.debug(f"Describing ECR repositories: {repository_names}")

            def describe_repos_sync():
                kwargs = {}
                if repository_names:
                    kwargs["repositoryNames"] = repository_names

                response = self.ecr_client.describe_repositories(**kwargs)
                return response.get("repositories", [])

            repositories = await asyncio.get_event_loop().run_in_executor(
                None, describe_repos_sync
            )

            logger.debug(f"Found {len(repositories)} repositories")
            return repositories

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "RepositoryNotFound":
                logger.debug(f"Repositories not found: {repository_names}")
                return []
            else:
                logger.error(f"AWS error describing ECR repositories: {e}")
                raise AWSError(
                    message=f"Failed to describe ECR repositories: {e.response['Error']['Message']}",
                    service="ecr",
                    details={
                        "repositories": repository_names,
                        "error_code": error_code,
                    },
                )
        except Exception as e:
            logger.error(f"Failed to describe ECR repositories: {e}")
            raise AWSError(
                message=f"Failed to describe ECR repositories: {str(e)}",
                service="ecr",
                details={"repositories": repository_names},
            )

    async def create_repository(self, repository_name: str) -> Dict[str, Any]:
        """
        Create an ECR repository.

        Args:
            repository_name: Name of the repository to create

        Returns:
            Repository information

        Raises:
            AWSError: If ECR operation fails
        """
        try:
            logger.info(f"Creating ECR repository: {repository_name}")

            def create_repo_sync():
                response = self.ecr_client.create_repository(
                    repositoryName=repository_name,
                    imageScanningConfiguration={"scanOnPush": True},
                    encryptionConfiguration={"encryptionType": "AES256"},
                )
                return response["repository"]

            repository = await asyncio.get_event_loop().run_in_executor(
                None, create_repo_sync
            )

            logger.info(f"Created ECR repository: {repository_name}")
            return repository

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "RepositoryAlreadyExistsException":
                logger.info(f"ECR repository already exists: {repository_name}")
                # Return existing repository info
                repositories = await self.describe_repositories([repository_name])
                return repositories[0] if repositories else {}
            else:
                logger.error(
                    f"AWS error creating ECR repository {repository_name}: {e}"
                )
                raise AWSError(
                    message=f"Failed to create ECR repository: {e.response['Error']['Message']}",
                    service="ecr",
                    details={"repository": repository_name, "error_code": error_code},
                )
        except Exception as e:
            logger.error(f"Failed to create ECR repository {repository_name}: {e}")
            raise AWSError(
                message=f"Failed to create ECR repository: {str(e)}",
                service="ecr",
                details={"repository": repository_name},
            )

    async def delete_repository(self, repository_name: str, force: bool = True) -> bool:
        """
        Delete an ECR repository.

        Args:
            repository_name: Name of the repository to delete
            force: Whether to force delete (delete even if contains images)

        Returns:
            True if repository was deleted successfully

        Raises:
            AWSError: If ECR operation fails
        """
        try:
            logger.info(f"Deleting ECR repository: {repository_name}")

            def delete_repo_sync():
                self.ecr_client.delete_repository(
                    repositoryName=repository_name, force=force
                )
                return True

            success = await asyncio.get_event_loop().run_in_executor(
                None, delete_repo_sync
            )

            logger.info(f"Deleted ECR repository: {repository_name}")
            return success

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "RepositoryNotFoundException":
                logger.info(f"ECR repository not found for deletion: {repository_name}")
                return False
            else:
                logger.error(
                    f"AWS error deleting ECR repository {repository_name}: {e}"
                )
                raise AWSError(
                    message=f"Failed to delete ECR repository: {e.response['Error']['Message']}",
                    service="ecr",
                    details={"repository": repository_name, "error_code": error_code},
                )
        except Exception as e:
            logger.error(f"Failed to delete ECR repository {repository_name}: {e}")
            raise AWSError(
                message=f"Failed to delete ECR repository: {str(e)}",
                service="ecr",
                details={"repository": repository_name},
            )


# Global client instances
_parameter_store_client = None
_ecs_client = None
_ecr_client = None


async def get_parameter_store_client() -> ParameterStoreClient:
    """Get a shared Parameter Store client instance."""
    global _parameter_store_client
    if _parameter_store_client is None:
        _parameter_store_client = ParameterStoreClient()
    return _parameter_store_client


async def get_ecs_client() -> ECSClient:
    """Get a shared ECS client instance."""
    global _ecs_client
    if _ecs_client is None:
        _ecs_client = ECSClient()
    return _ecs_client


async def get_ecr_client() -> ECRClient:
    """Get a shared ECR client instance."""
    global _ecr_client
    if _ecr_client is None:
        _ecr_client = ECRClient()
    return _ecr_client
