"""
Muppet Lifecycle Service for the Muppet Platform.

This service orchestrates the complete end-to-end lifecycle of muppets,
integrating all platform components for creation, deployment, monitoring,
and deletion operations.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import get_settings
from ..exceptions import (
    DeploymentError,
    GitHubError,
    PlatformException,
    ValidationError,
)
from ..integrations.github import GitHubClient
from ..logging_config import get_logger
from ..managers.github_manager import GitHubManager
from ..managers.infrastructure_manager import InfrastructureManager
from ..managers.steering_manager import SteeringManager
from ..managers.template_manager import GenerationContext, TemplateManager
from ..models import Muppet, MuppetStatus
from ..services.deployment_service import DeploymentService
from ..services.tls_auto_generator import TLSAutoGenerator
from ..state_manager import get_state_manager

logger = get_logger(__name__)


class MuppetLifecycleService:
    """
    Complete muppet lifecycle orchestration service.

    This service provides end-to-end muppet lifecycle management by
    coordinating all platform components:

    - Template Manager: Code generation from templates
    - GitHub Manager: Repository creation and management
    - Infrastructure Manager: AWS resource provisioning
    - Deployment Service: Fargate deployment orchestration
    - Steering Manager: Development guidelines distribution
    - State Manager: Platform state tracking
    """

    def __init__(self, tls_generator: Optional[TLSAutoGenerator] = None):
        self.settings = get_settings()

        # Initialize all managers and services
        self.template_manager = TemplateManager()
        self.github_manager = GitHubManager()
        self.infrastructure_manager = InfrastructureManager()
        self.deployment_service = DeploymentService()
        self.state_manager = get_state_manager()

        # Initialize TLS auto-generator for TLS-by-default support
        self.tls_generator = tls_generator or TLSAutoGenerator()

        # Initialize steering manager with GitHub client
        github_client = GitHubClient()
        self.steering_manager = SteeringManager(github_client)

        logger.info("Initialized Muppet Lifecycle Service with TLS-by-default support")

    async def create_muppet(
        self,
        name: str,
        template: str,
        description: str = "",
        auto_deploy: bool = True,  # Changed default to True for better DX
        enable_tls: bool = True,  # New parameter, defaults to True for TLS-by-default
        deployment_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a complete muppet with end-to-end lifecycle management.

        This method orchestrates the complete muppet creation process:
        1. Validate inputs and check for conflicts
        2. Generate code from template
        3. Create GitHub repository with generated code
        4. Set up Kiro configuration and steering docs
        5. Generate TLS configuration (if enabled)
        6. Optionally deploy to AWS Fargate with TLS
        7. Update platform state

        Args:
            name: Muppet name (must be unique)
            template: Template type to use
            description: Optional description for the muppet
            auto_deploy: Whether to automatically deploy after creation
            enable_tls: Whether to enable TLS by default (defaults to True)
            deployment_config: Optional deployment configuration

        Returns:
            Complete muppet creation result with all component information

        Raises:
            ValidationError: If inputs are invalid or muppet already exists
            PlatformException: If creation fails at any step
        """
        try:
            logger.info(
                f"Starting complete muppet creation: {name} with template {template}"
            )

            # Step 1: Validate inputs and check for conflicts
            await self._validate_muppet_creation(name, template)

            # Step 2: Create muppet model
            muppet = Muppet(
                name=name,
                template=template,
                status=MuppetStatus.CREATING,
                github_repo_url=f"https://github.com/{self.settings.github.organization}/{name}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                terraform_version="1.6.0",  # OpenTofu version
                port=3000,
            )

            # Step 3: Add to state immediately for tracking
            await self.state_manager.add_muppet_to_state(muppet)

            # Step 4: Generate code from template
            logger.info(f"Generating code for muppet {name} from template {template}")
            template_files = await self._generate_muppet_code(name, template)

            # Step 5: Create GitHub repository with generated code
            logger.info(f"Creating GitHub repository for muppet {name}")
            repo_info = await self.github_manager.create_muppet_repository(
                muppet_name=name,
                template=template,
                description=description or f"{template} muppet: {name}",
                template_files=template_files,
            )

            # Update muppet with actual repository URL
            muppet.github_repo_url = repo_info["url"]

            # Step 6: Set up Kiro configuration and steering docs
            logger.info(
                f"Setting up Kiro configuration and steering docs for muppet {name}"
            )
            steering_result = await self._setup_muppet_development_environment(
                muppet, template_files
            )

            # Step 7: Generate TLS configuration if enabled
            tls_config = None
            if enable_tls:
                logger.info(f"Generating TLS configuration for muppet {name}")
                try:
                    tls_config = self.tls_generator.generate_muppet_tls_config(name)
                    logger.info(
                        f"TLS configuration generated for muppet {name}: {tls_config['domain_name']}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to generate TLS configuration for muppet {name}: {e}"
                    )
                    if not auto_deploy:
                        # If not auto-deploying, TLS failure shouldn't block creation
                        tls_config = {"error": str(e), "enabled": False}
                    else:
                        raise PlatformException(
                            message=f"TLS configuration generation failed: {str(e)}",
                            error_type="TLS_CONFIG_ERROR",
                            status_code=500,
                            details={"muppet_name": name},
                        )

            # Step 8: Optionally deploy to AWS Fargate
            deployment_result = None
            if auto_deploy:
                logger.info(f"Auto-deploying muppet {name} to AWS Fargate")
                try:
                    # Include TLS configuration in deployment config
                    enhanced_deployment_config = deployment_config or {}
                    if tls_config and not tls_config.get("error"):
                        enhanced_deployment_config["tls_config"] = tls_config

                    deployment_result = await self._auto_deploy_muppet(
                        muppet, enhanced_deployment_config
                    )
                    muppet.status = MuppetStatus.RUNNING
                    muppet.fargate_service_arn = deployment_result.get("service_arn")
                except Exception as e:
                    logger.error(f"Auto-deployment failed for muppet {name}: {e}")
                    muppet.status = MuppetStatus.ERROR
                    deployment_result = {"error": str(e), "auto_deploy_failed": True}
            else:
                muppet.status = MuppetStatus.STOPPED  # Ready but not deployed

            # Step 9: Update final status
            muppet.updated_at = datetime.utcnow()
            await self.github_manager.update_muppet_status(name, muppet.status.value)
            await self.state_manager.add_muppet_to_state(muppet)

            # Step 10: Compile complete creation result
            creation_result = {
                "success": True,
                "muppet": muppet.to_dict(),
                "repository": repo_info,
                "template_generation": {
                    "template": template,
                    "files_generated": len(template_files),
                    "success": True,
                },
                "steering_setup": steering_result,
                "tls_configuration": tls_config,
                "deployment": deployment_result,
                "created_at": muppet.created_at.isoformat(),
                "next_steps": self._generate_next_steps(
                    muppet, auto_deploy, deployment_result, tls_config
                ),
            }

            # Add HTTPS endpoint if TLS is enabled and working
            if tls_config and not tls_config.get("error"):
                creation_result["endpoints"] = {
                    "https": f"https://{name}.s3u.dev",
                    "domain_name": tls_config["domain_name"],
                }
                if deployment_result and deployment_result.get("service_url"):
                    creation_result["endpoints"]["load_balancer"] = deployment_result[
                        "service_url"
                    ]

            logger.info(
                f"Successfully created muppet {name} with TLS {'enabled' if enable_tls else 'disabled'}"
            )
            return creation_result

        except (ValidationError, GitHubError, DeploymentError):
            # Remove muppet from state if creation failed
            try:
                await self.state_manager.remove_muppet_from_state(name)
                logger.info(f"Removed failed muppet {name} from state")
            except Exception as state_error:
                logger.warning(
                    f"Failed to remove failed muppet {name} from state: {state_error}"
                )
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating muppet {name}: {e}")
            # Remove muppet from state if creation failed
            try:
                await self.state_manager.remove_muppet_from_state(name)
                logger.info(f"Removed failed muppet {name} from state")
            except Exception as state_error:
                logger.warning(
                    f"Failed to remove failed muppet {name} from state: {state_error}"
                )
            raise PlatformException(
                message=f"Muppet creation failed: {str(e)}",
                error_type="MUPPET_CREATION_ERROR",
                status_code=500,
                details={"muppet_name": name, "template": template},
            )

    async def delete_muppet(
        self,
        name: str,
        force: bool = False,
        cleanup_github: bool = True,
        cleanup_infrastructure: bool = True,
    ) -> Dict[str, Any]:
        """
        Delete a muppet with complete cleanup of all resources.

        This method orchestrates the complete muppet deletion process:
        1. Validate deletion request
        2. Update muppet status to deleting
        3. Stop and undeploy from AWS Fargate
        4. Destroy AWS infrastructure
        5. Optionally delete GitHub repository
        6. Remove from platform state
        7. Clean up any remaining resources

        Args:
            name: Muppet name to delete
            force: Force deletion even if muppet is in error state
            cleanup_github: Whether to delete the GitHub repository
            cleanup_infrastructure: Whether to destroy AWS infrastructure

        Returns:
            Complete deletion result with cleanup information

        Raises:
            ValidationError: If muppet doesn't exist or deletion is not allowed
            PlatformException: If deletion fails at any step
        """
        try:
            logger.info(f"Starting complete muppet deletion: {name}")

            # Step 1: Get muppet and validate deletion
            muppet = await self.state_manager.get_muppet(name)
            if not muppet:
                raise ValidationError(
                    f"Muppet '{name}' not found", details={"muppet_name": name}
                )

            # Check if deletion is allowed
            if not force and muppet.status == MuppetStatus.CREATING:
                raise ValidationError(
                    f"Cannot delete muppet '{name}' while it is being created. Use force=True to override.",
                    details={"muppet_name": name, "status": muppet.status.value},
                )

            # Step 2: Update status to deleting
            logger.info(f"Updating muppet {name} status to deleting")
            muppet.status = MuppetStatus.DELETING
            muppet.updated_at = datetime.utcnow()
            await self.github_manager.update_muppet_status(name, "deleting")
            await self.state_manager.add_muppet_to_state(muppet)

            deletion_result = {
                "muppet_name": name,
                "deletion_started_at": datetime.utcnow().isoformat(),
                "steps_completed": [],
                "steps_failed": [],
                "warnings": [],
            }

            # Step 3: Undeploy from AWS Fargate if deployed
            deployment_cleanup_result = None
            if muppet.fargate_service_arn and cleanup_infrastructure:
                logger.info(f"Undeploying muppet {name} from AWS Fargate")
                try:
                    deployment_cleanup_result = (
                        await self.deployment_service.undeploy_muppet(name)
                    )
                    deletion_result["steps_completed"].append("fargate_undeployment")
                except Exception as e:
                    logger.error(f"Failed to undeploy muppet {name}: {e}")
                    deletion_result["steps_failed"].append(
                        {"step": "fargate_undeployment", "error": str(e)}
                    )
                    if not force:
                        raise DeploymentError(f"Failed to undeploy muppet: {str(e)}")

            # Step 4: Destroy AWS infrastructure
            infrastructure_cleanup_result = None
            if cleanup_infrastructure:
                logger.info(f"Destroying AWS infrastructure for muppet {name}")
                try:
                    infrastructure_state = (
                        await self.infrastructure_manager.destroy_infrastructure(name)
                    )
                    infrastructure_cleanup_result = {
                        "status": infrastructure_state.status.value,
                        "destroyed_at": infrastructure_state.last_updated,
                    }
                    deletion_result["steps_completed"].append(
                        "infrastructure_destruction"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to destroy infrastructure for muppet {name}: {e}"
                    )
                    deletion_result["steps_failed"].append(
                        {"step": "infrastructure_destruction", "error": str(e)}
                    )
                    if not force:
                        raise DeploymentError(
                            f"Failed to destroy infrastructure: {str(e)}"
                        )

            # Step 5: Delete GitHub repository
            github_cleanup_result = None
            if cleanup_github:
                logger.info(f"Deleting GitHub repository for muppet {name}")
                try:
                    github_cleanup_result = (
                        await self.github_manager.delete_muppet_repository(name)
                    )
                    if github_cleanup_result:
                        deletion_result["steps_completed"].append(
                            "github_repository_deletion"
                        )
                    else:
                        deletion_result["warnings"].append(
                            "GitHub repository deletion returned false"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to delete GitHub repository for muppet {name}: {e}"
                    )
                    deletion_result["steps_failed"].append(
                        {"step": "github_repository_deletion", "error": str(e)}
                    )
                    if not force:
                        raise GitHubError(
                            f"Failed to delete GitHub repository: {str(e)}"
                        )

            # Step 6: Remove from platform state
            logger.info(f"Removing muppet {name} from platform state")
            try:
                await self.state_manager.remove_muppet_from_state(name)
                deletion_result["steps_completed"].append("state_cleanup")
            except Exception as e:
                logger.error(f"Failed to remove muppet {name} from state: {e}")
                deletion_result["steps_failed"].append(
                    {"step": "state_cleanup", "error": str(e)}
                )

            # Step 7: Compile final deletion result
            deletion_result.update(
                {
                    "success": len(deletion_result["steps_failed"]) == 0,
                    "deployment_cleanup": deployment_cleanup_result,
                    "infrastructure_cleanup": infrastructure_cleanup_result,
                    "github_cleanup": github_cleanup_result,
                    "deletion_completed_at": datetime.utcnow().isoformat(),
                    "force_used": force,
                    "cleanup_github": cleanup_github,
                    "cleanup_infrastructure": cleanup_infrastructure,
                }
            )

            if deletion_result["success"]:
                logger.info(f"Successfully deleted muppet {name}")
            else:
                logger.warning(
                    f"Muppet {name} deletion completed with errors: {deletion_result['steps_failed']}"
                )

            return deletion_result

        except (ValidationError, DeploymentError, GitHubError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting muppet {name}: {e}")
            raise PlatformException(
                message=f"Muppet deletion failed: {str(e)}",
                error_type="MUPPET_DELETION_ERROR",
                status_code=500,
                details={"muppet_name": name},
            )

    async def get_muppet_status(self, name: str) -> Dict[str, Any]:
        """
        Get comprehensive status information for a muppet.

        This method aggregates status from all platform components:
        - Platform state (from state manager)
        - GitHub repository status
        - AWS deployment status
        - Health and monitoring information

        Args:
            name: Muppet name

        Returns:
            Comprehensive muppet status information

        Raises:
            ValidationError: If muppet doesn't exist
        """
        try:
            logger.debug(f"Getting comprehensive status for muppet: {name}")

            # Get muppet from state
            muppet = await self.state_manager.get_muppet(name)
            if not muppet:
                raise ValidationError(
                    f"Muppet '{name}' not found", details={"muppet_name": name}
                )

            # Get GitHub repository information
            github_info = None
            try:
                github_info = await self.github_manager.get_repository_info(name)
            except Exception as e:
                logger.warning(f"Failed to get GitHub info for muppet {name}: {e}")
                github_info = {"error": str(e)}

            # Get deployment status
            deployment_status = None
            try:
                deployment_status = await self.deployment_service.get_deployment_status(
                    name
                )
            except Exception as e:
                logger.warning(
                    f"Failed to get deployment status for muppet {name}: {e}"
                )
                deployment_status = {"error": str(e)}

            # Get infrastructure status
            infrastructure_status = None
            try:
                infra_state = await self.infrastructure_manager.get_deployment_status(
                    name
                )
                if infra_state:
                    infrastructure_status = {
                        "status": infra_state.status.value,
                        "last_operation": (
                            infra_state.last_operation.value
                            if infra_state.last_operation
                            else None
                        ),
                        "last_updated": infra_state.last_updated,
                        "terraform_workspace": infra_state.terraform_workspace,
                        "outputs": infra_state.outputs,
                        "error_message": infra_state.error_message,
                    }
            except Exception as e:
                logger.warning(
                    f"Failed to get infrastructure status for muppet {name}: {e}"
                )
                infrastructure_status = {"error": str(e)}

            # Compile comprehensive status
            status_info = {
                "muppet": muppet.to_dict(),
                "github": github_info,
                "deployment": deployment_status,
                "infrastructure": infrastructure_status,
                "health": self._assess_muppet_health(
                    muppet, deployment_status, infrastructure_status
                ),
                "retrieved_at": datetime.utcnow().isoformat(),
            }

            return status_info

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get status for muppet {name}: {e}")
            raise PlatformException(
                message=f"Failed to get muppet status: {str(e)}",
                error_type="STATUS_RETRIEVAL_ERROR",
                status_code=500,
                details={"muppet_name": name},
            )

    async def list_all_muppets(self) -> Dict[str, Any]:
        """
        List all muppets with their current status.

        Returns:
            Complete list of all muppets with summary information
        """
        try:
            logger.info("Listing all muppets with status information")

            # Get platform state
            state = await self.state_manager.get_state()

            # Get summary information for each muppet
            muppet_summaries = []
            for muppet in state.muppets:
                try:
                    # Get basic deployment status
                    deployment_status = (
                        await self.deployment_service.get_deployment_status(muppet.name)
                    )

                    summary = {
                        "name": muppet.name,
                        "template": muppet.template,
                        "status": muppet.status.value,
                        "github_repo_url": muppet.github_repo_url,
                        "created_at": (
                            muppet.created_at.isoformat() if muppet.created_at else None
                        ),
                        "updated_at": (
                            muppet.updated_at.isoformat() if muppet.updated_at else None
                        ),
                        "deployed": deployment_status is not None,
                        "health": (
                            "healthy"
                            if deployment_status
                            and deployment_status.get("health_status") == "healthy"
                            else "unknown"
                        ),
                    }

                    if deployment_status:
                        summary["service_url"] = deployment_status.get("service_url")
                        summary["running_tasks"] = deployment_status.get(
                            "running_count", 0
                        )

                    muppet_summaries.append(summary)

                except Exception as e:
                    logger.warning(
                        f"Failed to get summary for muppet {muppet.name}: {e}"
                    )
                    # Include muppet with error information
                    summary = {
                        "name": muppet.name,
                        "template": muppet.template,
                        "status": muppet.status.value,
                        "github_repo_url": muppet.github_repo_url,
                        "created_at": (
                            muppet.created_at.isoformat() if muppet.created_at else None
                        ),
                        "error": f"Failed to get status: {str(e)}",
                    }
                    muppet_summaries.append(summary)

            # Get platform health summary
            platform_health = await self.state_manager.get_platform_health()

            return {
                "muppets": muppet_summaries,
                "summary": {
                    "total_muppets": len(muppet_summaries),
                    "by_status": platform_health["status_counts"],
                    "deployed_muppets": len(
                        [m for m in muppet_summaries if m.get("deployed", False)]
                    ),
                    "healthy_muppets": len(
                        [m for m in muppet_summaries if m.get("health") == "healthy"]
                    ),
                },
                "platform_health": platform_health,
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to list muppets: {e}")
            raise PlatformException(
                message=f"Failed to list muppets: {str(e)}",
                error_type="MUPPET_LIST_ERROR",
                status_code=500,
            )

    async def migrate_existing_muppet_to_tls(self, muppet_name: str) -> Dict[str, Any]:
        """
        Migrate an existing muppet to use TLS.

        This method enables TLS for muppets that were created before TLS-by-default
        was implemented. It generates TLS configuration and provides instructions
        for applying the changes.

        Args:
            muppet_name: Name of the muppet to migrate

        Returns:
            Migration result with TLS configuration and next steps

        Raises:
            ValidationError: If muppet doesn't exist
            PlatformException: If migration fails
        """
        try:
            logger.info(f"Starting TLS migration for muppet: {muppet_name}")

            # Validate muppet exists
            muppet = await self.state_manager.get_muppet(muppet_name)
            if not muppet:
                raise ValidationError(
                    f"Muppet '{muppet_name}' not found",
                    details={"muppet_name": muppet_name},
                )

            # Generate TLS configuration
            logger.info(f"Generating TLS configuration for muppet {muppet_name}")
            tls_config = self.tls_generator.generate_muppet_tls_config(muppet_name)

            # Update muppet's terraform variables (this would be done by updating the repository)
            migration_instructions = await self._generate_tls_migration_instructions(
                muppet_name, tls_config
            )

            # Prepare migration result
            migration_result = {
                "success": True,
                "muppet_name": muppet_name,
                "message": "TLS migration configuration generated. Follow the instructions to complete migration.",
                "https_endpoint": f"https://{muppet_name}.s3u.dev",
                "tls_config": tls_config,
                "migration_instructions": migration_instructions,
                "migration_initiated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"TLS migration configuration generated for muppet {muppet_name}"
            )
            return migration_result

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to migrate muppet {muppet_name} to TLS: {e}")
            return {
                "success": False,
                "error": str(e),
                "muppet_name": muppet_name,
                "migration_failed_at": datetime.utcnow().isoformat(),
            }

    async def _generate_tls_migration_instructions(
        self, muppet_name: str, tls_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate step-by-step instructions for TLS migration."""

        return {
            "overview": "To enable TLS for your muppet, you need to update the terraform configuration and redeploy.",
            "steps": [
                {
                    "step": 1,
                    "title": "Update Terraform Variables",
                    "description": "Add TLS configuration to your muppet's terraform.tfvars file",
                    "terraform_variables": {
                        "enable_https": tls_config["enable_https"],
                        "certificate_arn": tls_config["certificate_arn"],
                        "domain_name": tls_config["domain_name"],
                        "zone_id": tls_config["zone_id"],
                        "redirect_http_to_https": tls_config["redirect_http_to_https"],
                        "ssl_policy": tls_config["ssl_policy"],
                        "create_dns_record": tls_config["create_dns_record"],
                    },
                },
                {
                    "step": 2,
                    "title": "Update Terraform Configuration",
                    "description": "Ensure your main.tf references the TLS variables",
                    "note": "Most muppet templates should already support TLS configuration",
                },
                {
                    "step": 3,
                    "title": "Deploy Changes",
                    "description": "Run your CI/CD pipeline or deploy manually",
                    "commands": [
                        "git add terraform.tfvars",
                        "git commit -m 'Enable TLS for muppet'",
                        "git push origin main",
                    ],
                },
                {
                    "step": 4,
                    "title": "Verify TLS Endpoint",
                    "description": f"Test your HTTPS endpoint: https://{muppet_name}.s3u.dev",
                    "validation_commands": [
                        f"curl -I https://{muppet_name}.s3u.dev/health",
                        f"curl -I http://{muppet_name}.s3u.dev/health  # Should redirect to HTTPS",
                    ],
                },
            ],
            "automatic_features": [
                "DNS record creation (automatic)",
                "Certificate management (automatic)",
                "HTTP to HTTPS redirect (automatic)",
                "TLS 1.3 support (automatic)",
            ],
            "support": "Contact the platform team if you encounter issues during migration",
        }

    async def _validate_muppet_creation(self, name: str, template: str) -> None:
        """Validate muppet creation inputs and check for conflicts."""

        # Validate muppet name
        if not name or not isinstance(name, str):
            raise ValidationError("Muppet name must be a non-empty string")

        if len(name) < 3 or len(name) > 50:
            raise ValidationError("Muppet name must be between 3 and 50 characters")

        # GitHub repository name validation
        import re

        if not re.match(r"^[a-zA-Z0-9._-]+$", name):
            raise ValidationError(
                "Muppet name can only contain alphanumeric characters, periods, hyphens, and underscores"
            )

        # Check if muppet already exists
        existing_muppet = await self.state_manager.get_muppet(name)
        if existing_muppet:
            raise ValidationError(
                f"Muppet '{name}' already exists",
                details={"existing_muppet": existing_muppet.to_dict()},
            )

        # Validate template
        available_templates = self.template_manager.discover_templates()
        template_names = [t.name for t in available_templates]

        if template not in template_names:
            raise ValidationError(
                f"Unknown template '{template}'. Available templates: {', '.join(template_names)}",
                details={"template": template, "available_templates": template_names},
            )

    async def _generate_muppet_code(self, name: str, template: str) -> Dict[str, Any]:
        """Generate muppet code from template."""

        # Create temporary directory for code generation
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / name

            # Create generation context
            context = GenerationContext(
                muppet_name=name,
                template_name=template,
                parameters={
                    "github_organization": self.settings.github.organization,
                    "aws_region": self.settings.aws.region,
                },
                output_path=output_path,
                aws_region=self.settings.aws.region,
                environment="production",
            )

            # Generate code
            generated_path = self.template_manager.generate_code(context)

            # Read all generated files into memory
            template_files = {}
            for file_path in generated_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(generated_path)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            template_files[str(relative_path)] = content
                            logger.debug(
                                f"Collected file: {relative_path} ({len(content)} chars)"
                            )
                    except UnicodeDecodeError:
                        # Handle binary files
                        with open(file_path, "rb") as f:
                            content = f.read()
                            template_files[str(relative_path)] = content
                            logger.debug(
                                f"Collected binary file: {relative_path} ({len(content)} bytes)"
                            )

            logger.info(f"Generated {len(template_files)} files for muppet {name}")

            # Log workflow files specifically
            workflow_files = [
                f for f in template_files.keys() if ".github/workflows" in f
            ]
            if workflow_files:
                logger.info(f"Generated workflow files: {workflow_files}")
            else:
                logger.warning("No workflow files found in generated template files")

            return template_files

    async def _setup_muppet_development_environment(
        self, muppet: Muppet, template_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Set up Kiro configuration and steering docs for muppet development."""

        try:
            # Distribute steering documents
            steering_success = (
                await self.steering_manager.distribute_steering_to_muppet(muppet)
            )

            # Generate Kiro configuration (this would be part of template files)
            kiro_config = {
                "muppet_name": muppet.name,
                "template": muppet.template,
                "github_repo": muppet.github_repo_url,
                "development_port": muppet.port,
                "aws_region": self.settings.aws.region,
            }

            return {
                "success": True,
                "steering_distributed": steering_success,
                "kiro_config": kiro_config,
                "development_ready": True,
            }

        except Exception as e:
            logger.error(
                f"Failed to setup development environment for muppet {muppet.name}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "steering_distributed": False,
                "development_ready": False,
            }

    async def _auto_deploy_muppet(
        self, muppet: Muppet, deployment_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Auto-deploy muppet to AWS Fargate."""

        # Use default container image based on template
        container_image = self._get_default_container_image(
            muppet.template, muppet.name
        )

        # Extract deployment configuration
        config = deployment_config or {}
        environment_variables = config.get("environment_variables", {})
        secrets = config.get("secrets", {})

        # Deploy using deployment service
        return await self.deployment_service.deploy_muppet(
            muppet=muppet,
            container_image=container_image,
            environment_variables=environment_variables,
            secrets=secrets,
            tls_config=config.get("tls_config"),
        )

    def _get_default_container_image(self, template: str, muppet_name: str) -> str:
        """Get default container image for a template."""
        # This would typically be built from the generated code
        # For now, return a placeholder based on template
        ecr_registry = f"{self.settings.aws.account_id}.dkr.ecr.{self.settings.aws.region}.amazonaws.com"
        return f"{ecr_registry}/{muppet_name}:latest"

    def _generate_next_steps(
        self,
        muppet: Muppet,
        auto_deploy: bool,
        deployment_result: Optional[Dict[str, Any]],
        tls_config: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Generate next steps for the user after muppet creation."""

        steps = [
            f"Clone the repository: git clone {muppet.github_repo_url}",
            "Open the project in Kiro for development",
            "Review the generated code and steering documentation",
        ]

        if not auto_deploy:
            steps.extend(
                [
                    f"Build the container image: docker build -t {muppet.name} .",
                    "Deploy to AWS Fargate using the platform MCP tools",
                ]
            )
        elif deployment_result and deployment_result.get("service_url"):
            steps.append(
                f"Access your deployed muppet at: {deployment_result['service_url']}"
            )

        # Add TLS-specific next steps
        if tls_config and not tls_config.get("error"):
            steps.append(
                f"Your muppet will be available at: https://{muppet.name}.s3u.dev (after deployment)"
            )
            steps.append("TLS certificate and DNS are configured automatically")

        return steps

    def _assess_muppet_health(
        self,
        muppet: Muppet,
        deployment_status: Optional[Dict[str, Any]],
        infrastructure_status: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Assess overall muppet health based on all status information."""

        health_score = 1.0
        issues = []

        # Check muppet status
        if muppet.status == MuppetStatus.ERROR:
            health_score *= 0.0
            issues.append("Muppet is in error state")
        elif muppet.status == MuppetStatus.CREATING:
            health_score *= 0.5
            issues.append("Muppet is still being created")
        elif muppet.status == MuppetStatus.DELETING:
            health_score *= 0.0
            issues.append("Muppet is being deleted")

        # Check deployment status
        if deployment_status:
            if deployment_status.get("error"):
                health_score *= 0.3
                issues.append(f"Deployment error: {deployment_status['error']}")
            elif deployment_status.get("running_count", 0) == 0:
                health_score *= 0.4
                issues.append("No running tasks")

        # Check infrastructure status
        if infrastructure_status:
            if infrastructure_status.get("error"):
                health_score *= 0.5
                issues.append(f"Infrastructure error: {infrastructure_status['error']}")
            elif infrastructure_status.get("status") == "failed":
                health_score *= 0.2
                issues.append("Infrastructure deployment failed")

        # Determine overall health
        if health_score >= 0.8:
            overall_health = "healthy"
        elif health_score >= 0.5:
            overall_health = "degraded"
        elif health_score >= 0.2:
            overall_health = "unhealthy"
        else:
            overall_health = "critical"

        return {
            "overall_health": overall_health,
            "health_score": round(health_score, 2),
            "issues": issues,
            "last_assessed": datetime.utcnow().isoformat(),
        }

    async def close(self) -> None:
        """Close all service connections."""
        await self.github_manager.close()
        await self.deployment_service.close()
        await self.steering_manager.close()
        logger.debug("Closed Muppet Lifecycle Service")
