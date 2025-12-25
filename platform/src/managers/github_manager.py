"""
GitHub Manager for the Muppet Platform.

This module provides high-level GitHub operations for muppet lifecycle management,
including repository creation, configuration, and code deployment.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..config import get_settings
from ..exceptions import GitHubError, ValidationError
from ..integrations.github import GitHubClient
from ..logging_config import get_logger

logger = get_logger(__name__)


class GitHubManager:
    """
    High-level GitHub manager for muppet repository operations.

    This manager orchestrates complex GitHub operations including:
    - Complete repository setup with configuration
    - Branch protection and workflow automation
    - Code deployment from templates
    - Access control and permissions management
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = GitHubClient()
        logger.info("Initialized GitHub Manager")

    async def create_muppet_repository(
        self,
        muppet_name: str,
        template: str,
        description: str = "",
        template_files: Optional[Dict[str, str]] = None,
        team_permissions: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a complete muppet repository with full configuration.

        This method handles the entire repository creation process:
        1. Create the repository
        2. Set up branch protection rules
        3. Configure CI/CD workflows
        4. Set up issue and PR templates
        5. Configure team permissions
        6. Push template code (if provided)

        Args:
            muppet_name: Name of the muppet (repository name)
            template: Template type used for the muppet
            description: Repository description
            template_files: Dictionary of file paths to content for template code
            team_permissions: Custom team permissions (optional)

        Returns:
            Repository information including URL and configuration status

        Raises:
            GitHubError: If repository creation or configuration fails
            ValidationError: If input parameters are invalid
        """
        try:
            logger.info(
                f"Creating muppet repository: {muppet_name} with template: {template}"
            )

            # Validate inputs
            self._validate_repository_inputs(muppet_name, template)

            # Create the repository
            repo_data = await self.client.create_repository(
                name=muppet_name,
                template=template,
                description=description or f"{template} muppet: {muppet_name}",
            )

            # Set up repository permissions
            if self.settings.github.branch_protection:
                await self.client.setup_repository_permissions(
                    muppet_name, team_permissions
                )

            # Push template code if provided
            if template_files:
                await self.client.push_template_code(
                    muppet_name, template, template_files
                )

            # Return comprehensive repository information
            result = {
                "name": muppet_name,
                "full_name": repo_data["full_name"],
                "url": repo_data["html_url"],
                "private": repo_data["private"],
                "template": template,
                "created_at": repo_data["created_at"],
                "configuration": {
                    "branch_protection": self.settings.github.branch_protection,
                    "workflows_configured": True,
                    "templates_configured": True,
                    "permissions_configured": bool(
                        team_permissions or self.settings.github.branch_protection
                    ),
                },
            }

            logger.info(f"Successfully created muppet repository: {muppet_name}")
            return result

        except GitHubError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create muppet repository {muppet_name}: {e}")
            raise GitHubError(
                message=f"Failed to create muppet repository: {str(e)}",
                details={"muppet_name": muppet_name, "template": template},
            )

    async def delete_muppet_repository(self, muppet_name: str) -> bool:
        """
        Delete a muppet repository completely.

        Args:
            muppet_name: Name of the muppet repository to delete

        Returns:
            True if deletion was successful

        Raises:
            GitHubError: If repository deletion fails
        """
        try:
            logger.info(f"Deleting muppet repository: {muppet_name}")

            # Validate repository exists
            repo_data = await self.client.get_repository(muppet_name)
            if not repo_data:
                logger.warning(f"Repository {muppet_name} not found for deletion")
                return False

            # Delete the repository
            success = await self.client.delete_repository(muppet_name)

            if success:
                logger.info(f"Successfully deleted muppet repository: {muppet_name}")
            else:
                logger.warning(f"Failed to delete muppet repository: {muppet_name}")

            return success

        except GitHubError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete muppet repository {muppet_name}: {e}")
            raise GitHubError(
                message=f"Failed to delete muppet repository: {str(e)}",
                details={"muppet_name": muppet_name},
            )

    async def update_muppet_status(self, muppet_name: str, status: str) -> bool:
        """
        Update the status of a muppet repository.

        Args:
            muppet_name: Name of the muppet repository
            status: New status (creating, running, stopped, error, deleting)

        Returns:
            True if status update was successful

        Raises:
            GitHubError: If status update fails
        """
        try:
            logger.debug(f"Updating muppet {muppet_name} status to: {status}")

            # Validate status
            valid_statuses = [
                "creating",
                "running",
                "stopped",
                "error",
                "deleting",
                "ready",
            ]
            if status not in valid_statuses:
                raise ValidationError(
                    f"Invalid status '{status}'. Must be one of: {valid_statuses}",
                    details={"status": status, "valid_statuses": valid_statuses},
                )

            success = await self.client.update_repository_status(muppet_name, status)

            if success:
                logger.debug(f"Updated muppet {muppet_name} status to {status}")
            else:
                logger.warning(f"Failed to update muppet {muppet_name} status")

            return success

        except (GitHubError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update muppet {muppet_name} status: {e}")
            raise GitHubError(
                message=f"Failed to update muppet status: {str(e)}",
                details={"muppet_name": muppet_name, "status": status},
            )

    async def get_muppet_repositories(self) -> List[Dict[str, Any]]:
        """
        Get all muppet repositories from the organization.

        Returns:
            List of muppet repository information

        Raises:
            GitHubError: If repository discovery fails
        """
        try:
            logger.info("Discovering muppet repositories")

            # Discover all muppets
            muppets = await self.client.discover_muppets()

            # Convert to repository information format
            repositories = []
            for muppet in muppets:
                repo_info = {
                    "name": muppet.name,
                    "template": muppet.template,
                    "status": muppet.status.value,
                    "url": muppet.github_repo_url,
                    "created_at": muppet.created_at.isoformat()
                    if muppet.created_at
                    else None,
                    "updated_at": muppet.updated_at.isoformat()
                    if muppet.updated_at
                    else None,
                }
                repositories.append(repo_info)

            logger.info(f"Found {len(repositories)} muppet repositories")
            return repositories

        except Exception as e:
            logger.error(f"Failed to get muppet repositories: {e}")
            raise GitHubError(
                message=f"Failed to get muppet repositories: {str(e)}", details={}
            )

    async def get_repository_info(self, muppet_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific muppet repository.

        Args:
            muppet_name: Name of the muppet repository

        Returns:
            Repository information or None if not found

        Raises:
            GitHubError: If repository lookup fails
        """
        try:
            logger.debug(f"Getting repository info for: {muppet_name}")

            repo_data = await self.client.get_repository(muppet_name)
            if not repo_data:
                return None

            # Get collaborators
            collaborators = await self.client.get_repository_collaborators(muppet_name)

            # Extract template and status from topics
            topics = repo_data.get("topics", [])
            template = "unknown"
            status = "unknown"

            for topic in topics:
                if topic.startswith("template:"):
                    template = topic.replace("template:", "")
                elif topic.startswith("status:"):
                    status = topic.replace("status:", "")

            return {
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "url": repo_data["html_url"],
                "description": repo_data.get("description", ""),
                "private": repo_data["private"],
                "template": template,
                "status": status,
                "topics": topics,
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"],
                "collaborators": len(collaborators),
                "default_branch": repo_data.get("default_branch", "main"),
            }

        except Exception as e:
            logger.error(f"Failed to get repository info for {muppet_name}: {e}")
            raise GitHubError(
                message=f"Failed to get repository info: {str(e)}",
                details={"muppet_name": muppet_name},
            )

    async def add_collaborator(
        self, muppet_name: str, username: str, permission: str = "push"
    ) -> bool:
        """
        Add a collaborator to a muppet repository.

        Args:
            muppet_name: Name of the muppet repository
            username: GitHub username to add
            permission: Permission level (pull, push, admin)

        Returns:
            True if collaborator was added successfully

        Raises:
            GitHubError: If adding collaborator fails
            ValidationError: If permission level is invalid
        """
        try:
            logger.info(f"Adding collaborator {username} to {muppet_name}")

            # Validate permission level
            valid_permissions = ["pull", "push", "admin"]
            if permission not in valid_permissions:
                raise ValidationError(
                    f"Invalid permission '{permission}'. Must be one of: {valid_permissions}",
                    details={
                        "permission": permission,
                        "valid_permissions": valid_permissions,
                    },
                )

            success = await self.client.add_repository_collaborator(
                muppet_name, username, permission
            )

            if success:
                logger.info(f"Added collaborator {username} to {muppet_name}")
            else:
                logger.warning(
                    f"Failed to add collaborator {username} to {muppet_name}"
                )

            return success

        except (GitHubError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to add collaborator {username} to {muppet_name}: {e}")
            raise GitHubError(
                message=f"Failed to add collaborator: {str(e)}",
                details={"muppet_name": muppet_name, "username": username},
            )

    async def remove_collaborator(self, muppet_name: str, username: str) -> bool:
        """
        Remove a collaborator from a muppet repository.

        Args:
            muppet_name: Name of the muppet repository
            username: GitHub username to remove

        Returns:
            True if collaborator was removed successfully

        Raises:
            GitHubError: If removing collaborator fails
        """
        try:
            logger.info(f"Removing collaborator {username} from {muppet_name}")

            success = await self.client.remove_repository_collaborator(
                muppet_name, username
            )

            if success:
                logger.info(f"Removed collaborator {username} from {muppet_name}")
            else:
                logger.warning(
                    f"Failed to remove collaborator {username} from {muppet_name}"
                )

            return success

        except GitHubError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to remove collaborator {username} from {muppet_name}: {e}"
            )
            raise GitHubError(
                message=f"Failed to remove collaborator: {str(e)}",
                details={"muppet_name": muppet_name, "username": username},
            )

    def _validate_repository_inputs(self, muppet_name: str, template: str) -> None:
        """
        Validate repository creation inputs.

        Args:
            muppet_name: Repository name to validate
            template: Template name to validate

        Raises:
            ValidationError: If inputs are invalid
        """
        # Validate muppet name
        if not muppet_name or not isinstance(muppet_name, str):
            raise ValidationError(
                "Muppet name must be a non-empty string",
                details={"muppet_name": muppet_name},
            )

        if len(muppet_name) > 100:
            raise ValidationError(
                "Muppet name must be 100 characters or less",
                details={"muppet_name": muppet_name, "length": len(muppet_name)},
            )

        # GitHub repository name validation
        import re

        if not re.match(r"^[a-zA-Z0-9._-]+$", muppet_name):
            raise ValidationError(
                "Muppet name can only contain alphanumeric characters, periods, hyphens, and underscores",
                details={"muppet_name": muppet_name},
            )

        # Validate template
        if not template or not isinstance(template, str):
            raise ValidationError(
                "Template must be a non-empty string", details={"template": template}
            )

        # TODO: Add template validation against available templates when template manager is implemented
        valid_templates = ["java-micronaut"]
        if template not in valid_templates:
            logger.warning(
                f"Template '{template}' not in known templates: {valid_templates}"
            )

    async def close(self) -> None:
        """Close the GitHub client connection."""
        await self.client.close()
        logger.debug("Closed GitHub Manager")
