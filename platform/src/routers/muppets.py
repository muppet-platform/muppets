"""
Muppet management endpoints for the Muppet Platform.

This module provides REST API endpoints for muppet lifecycle management,
including deployment operations to AWS Fargate.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..exceptions import DeploymentError, PlatformException, ValidationError
from ..logging_config import get_logger
from ..models import MuppetStatus
from ..services.deployment_service import DeploymentService
from ..services.muppet_lifecycle_service import MuppetLifecycleService
from ..state_manager import get_state_manager

logger = get_logger(__name__)
router = APIRouter()


class MuppetSummary(BaseModel):
    """Summary information for a muppet."""

    name: str = Field(..., description="Name of the muppet")
    template: str = Field(..., description="Template type used")
    status: str = Field(..., description="Current status of the muppet")
    github_repo_url: str = Field(..., description="GitHub repository URL")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    fargate_service_arn: Optional[str] = Field(
        None, description="AWS Fargate service ARN"
    )


class MuppetCreationRequest(BaseModel):
    """Request model for muppet creation."""

    name: str = Field(
        ..., min_length=3, max_length=50, description="Name of the muppet to create"
    )
    template: str = Field(..., description="Template type (e.g., 'java-micronaut')")
    description: Optional[str] = Field(
        default="", description="Optional description for the muppet"
    )
    auto_deploy: bool = Field(
        default=False, description="Whether to automatically deploy after creation"
    )
    deployment_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional deployment configuration"
    )


class MuppetCreationResponse(BaseModel):
    """Response model for muppet creation."""

    success: bool
    muppet: Dict[str, Any]
    repository: Dict[str, Any]
    template_generation: Dict[str, Any]
    steering_setup: Dict[str, Any]
    deployment: Optional[Dict[str, Any]] = None
    created_at: str
    next_steps: List[str]


class MuppetDeletionRequest(BaseModel):
    """Request model for muppet deletion."""

    force: bool = Field(
        default=False, description="Force deletion even if muppet is in error state"
    )
    cleanup_github: bool = Field(
        default=True, description="Whether to delete the GitHub repository"
    )
    cleanup_infrastructure: bool = Field(
        default=True, description="Whether to destroy AWS infrastructure"
    )


class MuppetDeletionResponse(BaseModel):
    """Response model for muppet deletion."""

    success: bool
    muppet_name: str
    steps_completed: List[str]
    steps_failed: List[Dict[str, str]]
    warnings: List[str]
    deletion_completed_at: str


class MuppetInfo(BaseModel):
    """Basic muppet information model."""

    name: str
    template: str
    status: str
    github_repo_url: str
    created_at: Optional[datetime] = None
    fargate_service_arn: Optional[str] = None


class MuppetDetail(BaseModel):
    """Detailed muppet information model."""

    name: str
    template: str
    status: str
    github_repo_url: str
    fargate_service_arn: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    terraform_version: str
    port: int


class DeploymentRequest(BaseModel):
    """Request model for muppet deployment."""

    container_image: str = Field(..., description="Docker image URI for the muppet")
    environment_variables: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables for the container"
    )
    secrets: Optional[Dict[str, str]] = Field(
        default=None,
        description="Secrets for the container (Parameter Store/Secrets Manager ARNs)",
    )


class DeploymentResponse(BaseModel):
    """Response model for muppet deployment."""

    muppet_name: str
    status: str
    service_arn: Optional[str] = None
    service_url: Optional[str] = None
    load_balancer_dns: Optional[str] = None
    cluster_name: Optional[str] = None
    task_definition_arn: Optional[str] = None
    log_group_name: Optional[str] = None
    deployed_at: Optional[str] = None


class ScalingRequest(BaseModel):
    """Request model for muppet scaling."""

    desired_count: int = Field(..., ge=0, le=100, description="Desired number of tasks")
    min_capacity: Optional[int] = Field(
        default=None, ge=0, le=100, description="Minimum capacity for auto-scaling"
    )
    max_capacity: Optional[int] = Field(
        default=None, ge=1, le=100, description="Maximum capacity for auto-scaling"
    )


class DeploymentStatus(BaseModel):
    """Deployment status information model."""

    muppet_name: str
    deployment_status: str
    service_arn: Optional[str] = None
    service_url: Optional[str] = None
    cluster_name: Optional[str] = None
    task_definition_arn: Optional[str] = None
    desired_count: int = 0
    running_count: int = 0
    pending_count: int = 0
    last_updated: Optional[str] = None
    health_status: str = "unknown"


class LogEntry(BaseModel):
    """Log entry model."""

    timestamp: str
    message: str
    level: Optional[str] = None


def get_deployment_service() -> DeploymentService:
    """Dependency to get deployment service instance."""
    return DeploymentService()


def get_lifecycle_service() -> MuppetLifecycleService:
    """Dependency to get lifecycle service instance."""
    return MuppetLifecycleService()


@router.post(
    "/",
    response_model=MuppetCreationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new muppet",
    description="Create a new muppet from a template with complete lifecycle management",
)
async def create_muppet(
    creation_request: MuppetCreationRequest,
    lifecycle_service: MuppetLifecycleService = Depends(get_lifecycle_service),
) -> MuppetCreationResponse:
    """
    Create a new muppet with complete lifecycle management.

    This endpoint handles the complete muppet creation process:
    - Code generation from template
    - GitHub repository creation
    - Kiro configuration setup
    - Optional AWS Fargate deployment

    Args:
        creation_request: Muppet creation configuration

    Returns:
        Complete muppet creation result

    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(f"Creating muppet via REST API: {creation_request.name}")

        # Create muppet using lifecycle service
        creation_result = await lifecycle_service.create_muppet(
            name=creation_request.name,
            template=creation_request.template,
            description=creation_request.description or "",
            auto_deploy=creation_request.auto_deploy,
            deployment_config=creation_request.deployment_config,
        )

        if not creation_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Muppet creation failed: {creation_result.get('error', 'Unknown error')}",
            )

        # Convert to response model
        response = MuppetCreationResponse(
            success=creation_result["success"],
            muppet=creation_result["muppet"],
            repository=creation_result["repository"],
            template_generation=creation_result["template_generation"],
            steering_setup=creation_result["steering_setup"],
            deployment=creation_result.get("deployment"),
            created_at=creation_result["created_at"],
            next_steps=creation_result["next_steps"],
        )

        logger.info(
            f"Successfully created muppet via REST API: {creation_request.name}"
        )
        return response

    except HTTPException:
        raise
    except (ValidationError, PlatformException) as e:
        logger.error(f"Muppet creation error: {e}")
        raise HTTPException(status_code=400, detail=f"Muppet creation failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to create muppet {creation_request.name}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create muppet: {str(e)}"
        )


@router.delete(
    "/{muppet_name}",
    response_model=MuppetDeletionResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a muppet",
    description="Delete a muppet with complete cleanup of all resources",
)
async def delete_muppet_complete(
    muppet_name: str,
    deletion_request: MuppetDeletionRequest,
    lifecycle_service: MuppetLifecycleService = Depends(get_lifecycle_service),
) -> MuppetDeletionResponse:
    """
    Delete a muppet with complete cleanup of all resources.

    This endpoint handles the complete muppet deletion process:
    - AWS Fargate undeployment
    - Infrastructure destruction
    - GitHub repository deletion (optional)
    - Platform state cleanup

    Args:
        muppet_name: Name of the muppet to delete
        deletion_request: Deletion configuration

    Returns:
        Complete deletion result

    Raises:
        HTTPException: If deletion fails
    """
    try:
        logger.info(f"Deleting muppet via REST API: {muppet_name}")

        # Delete muppet using lifecycle service
        deletion_result = await lifecycle_service.delete_muppet(
            name=muppet_name,
            force=deletion_request.force,
            cleanup_github=deletion_request.cleanup_github,
            cleanup_infrastructure=deletion_request.cleanup_infrastructure,
        )

        # Convert to response model
        response = MuppetDeletionResponse(
            success=deletion_result["success"],
            muppet_name=deletion_result["muppet_name"],
            steps_completed=deletion_result["steps_completed"],
            steps_failed=deletion_result["steps_failed"],
            warnings=deletion_result.get("warnings", []),
            deletion_completed_at=deletion_result["deletion_completed_at"],
        )

        if deletion_result["success"]:
            logger.info(f"Successfully deleted muppet via REST API: {muppet_name}")
        else:
            logger.warning(f"Muppet deletion completed with errors: {muppet_name}")

        return response

    except (ValidationError, PlatformException) as e:
        logger.error(f"Muppet deletion error: {e}")
        raise HTTPException(status_code=400, detail=f"Muppet deletion failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to delete muppet {muppet_name}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete muppet: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[MuppetSummary],
    status_code=status.HTTP_200_OK,
    summary="List muppets",
    description="Get a list of all muppets with basic information",
)
async def list_muppets(
    lifecycle_service: MuppetLifecycleService = Depends(get_lifecycle_service),
) -> List[MuppetSummary]:
    """
    List all muppets with comprehensive information.

    Returns basic information about all muppets discovered from the platform
    state and enriched with deployment status.
    """
    try:
        logger.info("Listing all muppets via REST API")

        # Use lifecycle service for comprehensive muppet listing
        muppets_info = await lifecycle_service.list_all_muppets()

        # Convert to response model
        muppet_summaries = []
        for muppet_data in muppets_info["muppets"]:
            summary = MuppetSummary(
                name=muppet_data["name"],
                template=muppet_data["template"],
                status=muppet_data["status"],
                github_repo_url=muppet_data["github_repo_url"],
                created_at=(
                    datetime.fromisoformat(muppet_data["created_at"])
                    if muppet_data.get("created_at")
                    else None
                ),
                fargate_service_arn=muppet_data.get("fargate_service_arn"),
            )
            muppet_summaries.append(summary)

        logger.info(f"Listed {len(muppet_summaries)} muppets via REST API")
        return muppet_summaries

    except PlatformException:
        raise
    except Exception as e:
        logger.exception("Failed to list muppets via REST API")
        raise HTTPException(status_code=500, detail=f"Failed to list muppets: {str(e)}")


@router.get(
    "/{muppet_name}",
    response_model=MuppetDetail,
    status_code=status.HTTP_200_OK,
    summary="Get muppet details",
    description="Get detailed information about a specific muppet",
)
async def get_muppet(
    muppet_name: str, state_manager=Depends(get_state_manager)
) -> MuppetDetail:
    """
    Get detailed information about a specific muppet.

    Args:
        muppet_name: Name of the muppet to retrieve

    Returns:
        Detailed muppet information

    Raises:
        HTTPException: If muppet is not found
    """
    try:
        logger.info(f"Getting muppet details: {muppet_name}")

        muppet = await state_manager.get_muppet(muppet_name)

        if not muppet:
            logger.warning(f"Muppet not found: {muppet_name}")
            raise HTTPException(
                status_code=404, detail=f"Muppet '{muppet_name}' not found"
            )

        # Convert to response model
        detail = MuppetDetail(
            name=muppet.name,
            template=muppet.template,
            status=muppet.status.value,
            github_repo_url=muppet.github_repo_url,
            fargate_service_arn=muppet.fargate_service_arn,
            created_at=muppet.created_at,
            updated_at=muppet.updated_at,
            terraform_version=muppet.terraform_version,
            port=muppet.port,
        )

        logger.info(f"Retrieved muppet details: {muppet_name}")
        return detail

    except HTTPException:
        raise
    except PlatformException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get muppet {muppet_name}")
        raise HTTPException(status_code=500, detail=f"Failed to get muppet: {str(e)}")


@router.post(
    "/{muppet_name}/deploy",
    response_model=DeploymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Deploy muppet to Fargate",
    description="Deploy a muppet to AWS Fargate with load balancer and monitoring",
)
async def deploy_muppet(
    muppet_name: str,
    deployment_request: DeploymentRequest,
    deployment_service: DeploymentService = Depends(get_deployment_service),
    state_manager=Depends(get_state_manager),
) -> DeploymentResponse:
    """
    Deploy a muppet to AWS Fargate.

    This endpoint handles the complete deployment process including:
    - Infrastructure provisioning via Terraform
    - Fargate service deployment
    - Load balancer configuration
    - Health monitoring setup

    Args:
        muppet_name: Name of the muppet to deploy
        deployment_request: Deployment configuration

    Returns:
        Deployment information including service ARN and URL

    Raises:
        HTTPException: If deployment fails or muppet is not found
    """
    try:
        logger.info(f"Starting deployment for muppet: {muppet_name}")

        # Get muppet information
        muppet = await state_manager.get_muppet(muppet_name)

        if not muppet:
            logger.warning(f"Muppet not found for deployment: {muppet_name}")
            raise HTTPException(
                status_code=404, detail=f"Muppet '{muppet_name}' not found"
            )

        # Deploy the muppet
        deployment_info = await deployment_service.deploy_muppet(
            muppet=muppet,
            container_image=deployment_request.container_image,
            environment_variables=deployment_request.environment_variables,
            secrets=deployment_request.secrets,
        )

        # Convert to response model
        response = DeploymentResponse(
            muppet_name=deployment_info["muppet_name"],
            status=deployment_info["status"],
            service_arn=deployment_info.get("service_arn"),
            service_url=deployment_info.get("service_url"),
            load_balancer_dns=deployment_info.get("load_balancer_dns"),
            cluster_name=deployment_info.get("cluster_name"),
            task_definition_arn=deployment_info.get("task_definition_arn"),
            log_group_name=deployment_info.get("log_group_name"),
            deployed_at=deployment_info.get("deployed_at"),
        )

        logger.info(f"Successfully started deployment for muppet: {muppet_name}")
        return response

    except HTTPException:
        raise
    except (DeploymentError, ValidationError) as e:
        logger.error(f"Deployment error for muppet {muppet_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Deployment failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to deploy muppet {muppet_name}")
        raise HTTPException(
            status_code=500, detail=f"Failed to deploy muppet: {str(e)}"
        )


@router.delete(
    "/{muppet_name}/deploy",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Undeploy muppet from Fargate",
    description="Remove a muppet deployment from AWS Fargate and clean up resources",
)
async def undeploy_muppet(
    muppet_name: str,
    deployment_service: DeploymentService = Depends(get_deployment_service),
) -> Dict[str, Any]:
    """
    Undeploy a muppet from AWS Fargate.

    This endpoint handles the complete undeployment process including:
    - Fargate service termination
    - Infrastructure destruction via Terraform
    - Resource cleanup

    Args:
        muppet_name: Name of the muppet to undeploy

    Returns:
        Undeployment confirmation

    Raises:
        HTTPException: If undeployment fails
    """
    try:
        logger.info(f"Starting undeployment for muppet: {muppet_name}")

        # Undeploy the muppet
        undeployment_info = await deployment_service.undeploy_muppet(muppet_name)

        logger.info(f"Successfully started undeployment for muppet: {muppet_name}")
        return undeployment_info

    except DeploymentError as e:
        logger.error(f"Undeployment error for muppet {muppet_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Undeployment failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to undeploy muppet {muppet_name}")
        raise HTTPException(
            status_code=500, detail=f"Failed to undeploy muppet: {str(e)}"
        )


@router.get(
    "/{muppet_name}/deployment",
    response_model=DeploymentStatus,
    status_code=status.HTTP_200_OK,
    summary="Get muppet deployment status",
    description="Get detailed deployment status and health information for a muppet",
)
async def get_deployment_status(
    muppet_name: str,
    deployment_service: DeploymentService = Depends(get_deployment_service),
) -> DeploymentStatus:
    """
    Get deployment status for a muppet.

    Args:
        muppet_name: Name of the muppet

    Returns:
        Detailed deployment status information

    Raises:
        HTTPException: If muppet is not found or not deployed
    """
    try:
        logger.debug(f"Getting deployment status for muppet: {muppet_name}")

        deployment_status = await deployment_service.get_deployment_status(muppet_name)

        if not deployment_status:
            raise HTTPException(
                status_code=404, detail=f"Muppet '{muppet_name}' is not deployed"
            )

        # Convert to response model
        response = DeploymentStatus(
            muppet_name=deployment_status["muppet_name"],
            deployment_status=deployment_status["deployment_status"],
            service_arn=deployment_status.get("service_arn"),
            service_url=deployment_status.get("service_url"),
            cluster_name=deployment_status.get("cluster_name"),
            task_definition_arn=deployment_status.get("task_definition_arn"),
            desired_count=deployment_status.get("desired_count", 0),
            running_count=deployment_status.get("running_count", 0),
            pending_count=deployment_status.get("pending_count", 0),
            last_updated=deployment_status.get("last_updated"),
            health_status=deployment_status.get("health_status", "unknown"),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get deployment status for muppet {muppet_name}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get deployment status: {str(e)}"
        )


@router.post(
    "/{muppet_name}/scale",
    status_code=status.HTTP_200_OK,
    summary="Scale muppet deployment",
    description="Scale a muppet deployment by adjusting the desired task count and auto-scaling limits",
)
async def scale_muppet(
    muppet_name: str,
    scaling_request: ScalingRequest,
    deployment_service: DeploymentService = Depends(get_deployment_service),
) -> Dict[str, Any]:
    """
    Scale a muppet deployment.

    Args:
        muppet_name: Name of the muppet to scale
        scaling_request: Scaling configuration

    Returns:
        Scaling operation result

    Raises:
        HTTPException: If scaling fails or muppet is not deployed
    """
    try:
        logger.info(
            f"Scaling muppet {muppet_name} to {scaling_request.desired_count} tasks"
        )

        # Validate scaling parameters
        if (
            scaling_request.min_capacity is not None
            and scaling_request.max_capacity is not None
            and scaling_request.min_capacity > scaling_request.max_capacity
        ):
            raise HTTPException(
                status_code=400,
                detail="min_capacity cannot be greater than max_capacity",
            )

        if (
            scaling_request.min_capacity is not None
            and scaling_request.desired_count < scaling_request.min_capacity
        ):
            raise HTTPException(
                status_code=400, detail="desired_count cannot be less than min_capacity"
            )

        if (
            scaling_request.max_capacity is not None
            and scaling_request.desired_count > scaling_request.max_capacity
        ):
            raise HTTPException(
                status_code=400,
                detail="desired_count cannot be greater than max_capacity",
            )

        # Scale the muppet
        scaling_result = await deployment_service.scale_muppet(
            muppet_name=muppet_name,
            desired_count=scaling_request.desired_count,
            min_capacity=scaling_request.min_capacity,
            max_capacity=scaling_request.max_capacity,
        )

        logger.info(f"Successfully scaled muppet: {muppet_name}")
        return scaling_result

    except HTTPException:
        raise
    except DeploymentError as e:
        logger.error(f"Scaling error for muppet {muppet_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Scaling failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to scale muppet {muppet_name}")
        raise HTTPException(status_code=500, detail=f"Failed to scale muppet: {str(e)}")


@router.get(
    "/{muppet_name}/logs",
    response_model=List[LogEntry],
    status_code=status.HTTP_200_OK,
    summary="Get muppet logs",
    description="Retrieve logs from a muppet deployment",
)
async def get_muppet_logs(
    muppet_name: str,
    lines: int = 100,
    deployment_service: DeploymentService = Depends(get_deployment_service),
) -> List[LogEntry]:
    """
    Get logs for a muppet deployment.

    Args:
        muppet_name: Name of the muppet
        lines: Number of log lines to retrieve (default: 100, max: 1000)

    Returns:
        List of log entries

    Raises:
        HTTPException: If log retrieval fails or muppet is not deployed
    """
    try:
        logger.debug(f"Getting logs for muppet: {muppet_name}")

        # Validate lines parameter
        if lines < 1 or lines > 1000:
            raise HTTPException(
                status_code=400, detail="lines parameter must be between 1 and 1000"
            )

        # Get logs
        logs = await deployment_service.get_muppet_logs(muppet_name, lines)

        # Convert to response model
        log_entries = []
        for log in logs:
            entry = LogEntry(
                timestamp=log.get("timestamp", ""),
                message=log.get("message", ""),
                level=log.get("level"),
            )
            log_entries.append(entry)

        return log_entries

    except HTTPException:
        raise
    except DeploymentError as e:
        logger.error(f"Log retrieval error for muppet {muppet_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Log retrieval failed: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to get logs for muppet {muppet_name}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")
