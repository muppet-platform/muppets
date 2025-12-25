"""
State management for the Muppet Platform.

This module provides centralized state management by loading muppet data
from GitHub at server startup and maintaining it in memory.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio

from .config import get_settings
from .models import PlatformState, Muppet, MuppetStatus
from .integrations.github import GitHubClient
from .integrations.aws import ParameterStoreClient, ECSClient
from .exceptions import PlatformException
from .logging_config import get_logger

logger = get_logger(__name__)


class StateManager:
    """
    Centralized state manager for the Muppet Platform.

    Loads platform state from GitHub at startup and maintains it in memory.
    State is updated when muppets are created, updated, or deleted.
    """

    def __init__(self):
        self.settings = get_settings()
        self.github_client = GitHubClient()
        self.parameter_store = ParameterStoreClient()
        self.ecs_client = ECSClient()

        # In-memory state storage
        self._state: Optional[PlatformState] = None
        self._initialized = False

        logger.info("Initialized StateManager")

    async def initialize(self) -> None:
        """
        Initialize the state manager by loading muppets from GitHub.

        This should be called once at server startup.

        Raises:
            PlatformException: If initialization fails
        """
        if self._initialized:
            logger.debug("StateManager already initialized")
            return

        logger.info("Initializing StateManager - loading muppets from GitHub")

        try:
            # Load initial state from all sources
            self._state = await self._load_state_from_sources()
            self._initialized = True

            logger.info(
                f"StateManager initialized successfully with {len(self._state.muppets)} muppets"
            )

        except Exception as e:
            logger.error(f"Failed to initialize StateManager: {e}")
            raise PlatformException(
                message=f"Failed to initialize state manager: {str(e)}",
                error_type="INITIALIZATION_ERROR",
                status_code=500,
            )

    async def get_state(self) -> PlatformState:
        """
        Get the current platform state.

        Returns:
            Current platform state

        Raises:
            PlatformException: If state is not initialized
        """
        if not self._initialized or self._state is None:
            raise PlatformException(
                message="StateManager not initialized. Call initialize() first.",
                error_type="STATE_NOT_INITIALIZED",
                status_code=500,
            )

        return self._state

    async def get_muppet(self, name: str) -> Optional[Muppet]:
        """
        Get a specific muppet by name.

        Args:
            name: Muppet name

        Returns:
            Muppet instance or None if not found
        """
        state = await self.get_state()
        return state.get_muppet(name)

    async def list_muppets(self) -> List[Muppet]:
        """
        List all muppets.

        Returns:
            List of all muppets
        """
        state = await self.get_state()
        return state.muppets

    async def refresh_state(self) -> None:
        """
        Refresh the platform state by reloading from all sources.

        This can be called manually when needed to sync with external changes.
        """
        logger.info("Refreshing platform state from sources")

        try:
            self._state = await self._load_state_from_sources()
            logger.info(
                f"State refreshed successfully with {len(self._state.muppets)} muppets"
            )

        except Exception as e:
            logger.error(f"Failed to refresh state: {e}")
            raise PlatformException(
                message=f"Failed to refresh state: {str(e)}",
                error_type="STATE_REFRESH_ERROR",
                status_code=500,
            )

    async def update_muppet_status(
        self, muppet_name: str, status: MuppetStatus
    ) -> bool:
        """
        Update a muppet's status in both GitHub and local state.

        Args:
            muppet_name: Name of the muppet to update
            status: New status to set

        Returns:
            True if update was successful

        Raises:
            PlatformException: If update fails
        """
        try:
            logger.info(f"Updating muppet {muppet_name} status to {status.value}")

            # Update GitHub repository status
            success = await self.github_client.update_repository_status(
                muppet_name, status.value
            )

            if success:
                # Update local state
                if self._state:
                    muppet = self._state.get_muppet(muppet_name)
                    if muppet:
                        muppet.status = status
                        muppet.updated_at = datetime.utcnow()
                        self._state.last_updated = datetime.utcnow()

                logger.info(f"Successfully updated muppet {muppet_name} status")
                return True
            else:
                logger.warning(
                    f"Failed to update GitHub status for muppet {muppet_name}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to update muppet {muppet_name} status: {e}")
            raise PlatformException(
                message=f"Failed to update muppet status: {str(e)}",
                error_type="STATUS_UPDATE_ERROR",
                status_code=500,
                details={"muppet_name": muppet_name, "status": status.value},
            )

    async def add_muppet_to_state(self, muppet: Muppet) -> None:
        """
        Add a new muppet to the platform state.

        Args:
            muppet: Muppet instance to add
        """
        logger.debug(f"Adding muppet {muppet.name} to state")

        if self._state is not None:
            self._state.add_muppet(muppet)
            logger.debug(f"Added muppet {muppet.name} to state")

    async def remove_muppet_from_state(self, muppet_name: str) -> None:
        """
        Remove a muppet from the platform state.

        Args:
            muppet_name: Name of muppet to remove
        """
        logger.debug(f"Removing muppet {muppet_name} from state")

        if self._state is not None:
            self._state.remove_muppet(muppet_name)
            logger.debug(f"Removed muppet {muppet_name} from state")

    async def get_platform_health(self) -> Dict[str, Any]:
        """
        Get overall platform health information.

        Returns:
            Dictionary containing platform health metrics
        """
        try:
            state = await self.get_state()

            # Count muppets by status
            status_counts = {}
            for status in MuppetStatus:
                status_counts[status.value] = 0

            for muppet in state.muppets:
                status_counts[muppet.status.value] += 1

            # Calculate health metrics
            total_muppets = len(state.muppets)
            running_muppets = status_counts.get(MuppetStatus.RUNNING.value, 0)
            error_muppets = status_counts.get(MuppetStatus.ERROR.value, 0)

            health_score = 1.0
            if total_muppets > 0:
                health_score = (running_muppets / total_muppets) * (
                    1.0 - (error_muppets / total_muppets)
                )

            return {
                "total_muppets": total_muppets,
                "status_counts": status_counts,
                "active_deployments": len(state.active_deployments),
                "terraform_modules": len(state.terraform_versions),
                "health_score": round(health_score, 2),
                "last_updated": state.last_updated.isoformat(),
                "initialized": self._initialized,
            }

        except Exception as e:
            logger.error(f"Failed to get platform health: {e}")
            raise PlatformException(
                message=f"Failed to get platform health: {str(e)}",
                error_type="HEALTH_CHECK_ERROR",
                status_code=500,
            )

    async def _load_state_from_sources(self) -> PlatformState:
        """
        Load complete platform state from all sources.

        This method aggregates data from:
        1. GitHub - Muppet repositories and metadata
        2. Parameter Store - Configuration and Terraform versions
        3. ECS - Active service deployments

        Returns:
            Complete platform state

        Raises:
            PlatformException: If state loading fails
        """
        try:
            # Run all data gathering operations concurrently
            github_task = self.github_client.discover_muppets()
            terraform_versions_task = self._get_terraform_versions()
            active_deployments_task = self.ecs_client.get_active_deployments()

            # Wait for all tasks to complete
            muppets, terraform_versions, active_deployments = await asyncio.gather(
                github_task,
                terraform_versions_task,
                active_deployments_task,
                return_exceptions=True,
            )

            # Handle any exceptions from the tasks
            if isinstance(muppets, Exception):
                logger.error(f"Failed to discover muppets from GitHub: {muppets}")
                muppets = []

            if isinstance(terraform_versions, Exception):
                logger.error(f"Failed to get Terraform versions: {terraform_versions}")
                terraform_versions = {}

            if isinstance(active_deployments, Exception):
                logger.error(f"Failed to get active deployments: {active_deployments}")
                active_deployments = {}

            # Enrich muppet data with ECS deployment information
            for muppet in muppets:
                if muppet.name in active_deployments:
                    muppet.fargate_service_arn = active_deployments[muppet.name]
                    # Update status based on deployment presence
                    if muppet.status == MuppetStatus.CREATING:
                        muppet.status = MuppetStatus.RUNNING

            # Create platform state
            state = PlatformState(
                muppets=muppets,
                active_deployments=active_deployments,
                terraform_versions=terraform_versions,
                last_updated=datetime.utcnow(),
            )

            logger.info(
                f"Loaded platform state: {len(muppets)} muppets, "
                f"{len(active_deployments)} active deployments"
            )

            return state

        except Exception as e:
            logger.exception("Failed to load platform state")
            raise PlatformException(
                message=f"Failed to load platform state: {str(e)}",
                error_type="STATE_LOADING_ERROR",
                status_code=500,
            )

    async def _get_terraform_versions(self) -> dict:
        """
        Get Terraform module versions from Parameter Store.

        Returns:
            Dictionary mapping module names to versions
        """
        try:
            # Get all Terraform module version parameters
            parameters = await self.parameter_store.get_parameters_by_path(
                "terraform/modules", recursive=True
            )

            # Parse module versions from parameter names
            versions = {}
            for param_name, param_value in parameters.items():
                # Extract module name from path like "terraform/modules/fargate-service/version"
                parts = param_name.split("/")
                if len(parts) >= 3 and parts[-1] == "version":
                    module_name = parts[-2]
                    versions[module_name] = param_value

            logger.debug(f"Retrieved {len(versions)} Terraform module versions")
            return versions

        except Exception as e:
            logger.error(f"Failed to get Terraform versions: {e}")
            return {}


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """
    Get the global state manager instance.

    Returns:
        StateManager singleton instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
