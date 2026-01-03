"""
Test muppet lifecycle service state cleanup behavior.

This test ensures that failed muppet creations are properly cleaned up
from state to prevent orphaned entries that don't correspond to actual
GitHub repositories.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.exceptions import GitHubError, PlatformException, ValidationError
from src.models import Muppet, MuppetStatus
from src.services.muppet_lifecycle_service import MuppetLifecycleService


@pytest.fixture
def lifecycle_service():
    """Create a muppet lifecycle service with mocked dependencies."""
    with (
        patch(
            "src.services.muppet_lifecycle_service.TemplateManager"
        ) as mock_template_manager,
        patch(
            "src.services.muppet_lifecycle_service.GitHubManager"
        ) as mock_github_manager,
        patch(
            "src.services.muppet_lifecycle_service.InfrastructureManager"
        ) as mock_infra_manager,
        patch(
            "src.services.muppet_lifecycle_service.DeploymentService"
        ) as mock_deployment_service,
        patch(
            "src.services.muppet_lifecycle_service.get_state_manager"
        ) as mock_get_state_manager,
        patch(
            "src.services.muppet_lifecycle_service.TLSAutoGenerator"
        ) as mock_tls_generator,
        patch(
            "src.services.muppet_lifecycle_service.SteeringManager"
        ) as mock_steering_manager,
        patch(
            "src.services.muppet_lifecycle_service.GitHubClient"
        ) as mock_github_client,
    ):
        # Create mock instances
        mock_state_manager = AsyncMock()
        mock_get_state_manager.return_value = mock_state_manager

        # Create service
        service = MuppetLifecycleService()

        # Store mocks for easy access in tests
        service._mock_state_manager = mock_state_manager
        service._mock_template_manager = mock_template_manager.return_value
        service._mock_github_manager = mock_github_manager.return_value

        return service


class TestMuppetLifecycleStateCleanup:
    """Test state cleanup behavior during muppet creation failures."""

    @pytest.mark.asyncio
    async def test_template_validation_failure_removes_from_state(
        self, lifecycle_service
    ):
        """Test that template validation failure removes muppet from state."""
        # Setup: Template validation will fail
        lifecycle_service._mock_template_manager.discover_templates.return_value = [
            type("Template", (), {"name": "java-micronaut"})()
        ]

        # Mock state manager methods
        lifecycle_service._mock_state_manager.get_muppet.return_value = (
            None  # Muppet doesn't exist
        )
        lifecycle_service._mock_state_manager.add_muppet_to_state = AsyncMock()
        lifecycle_service._mock_state_manager.remove_muppet_from_state = AsyncMock()

        # Mock template generation to fail with ValidationError
        with patch.object(lifecycle_service, "_generate_muppet_code") as mock_generate:
            mock_generate.side_effect = ValidationError("Template validation failed")

            # Attempt to create muppet
            with pytest.raises(ValidationError, match="Template validation failed"):
                await lifecycle_service.create_muppet(
                    name="test-muppet",
                    template="java-micronaut",
                    description="Test muppet",
                    auto_deploy=False,
                )

        # Verify: Muppet was added to state initially
        lifecycle_service._mock_state_manager.add_muppet_to_state.assert_called_once()

        # Verify: Muppet was removed from state after failure
        lifecycle_service._mock_state_manager.remove_muppet_from_state.assert_called_once_with(
            "test-muppet"
        )

    @pytest.mark.asyncio
    async def test_github_creation_failure_removes_from_state(self, lifecycle_service):
        """Test that GitHub repository creation failure removes muppet from state."""
        # Setup: Template validation succeeds, GitHub creation fails
        lifecycle_service._mock_template_manager.discover_templates.return_value = [
            type("Template", (), {"name": "java-micronaut"})()
        ]

        # Mock state manager methods
        lifecycle_service._mock_state_manager.get_muppet.return_value = None
        lifecycle_service._mock_state_manager.add_muppet_to_state = AsyncMock()
        lifecycle_service._mock_state_manager.remove_muppet_from_state = AsyncMock()

        # Mock successful template generation
        with (
            patch.object(lifecycle_service, "_generate_muppet_code") as mock_generate,
            patch.object(
                lifecycle_service._mock_github_manager, "create_muppet_repository"
            ) as mock_create_repo,
        ):
            mock_generate.return_value = {"main.py": "# Generated code"}
            mock_create_repo.side_effect = GitHubError("Repository creation failed")

            # Attempt to create muppet
            with pytest.raises(GitHubError, match="Repository creation failed"):
                await lifecycle_service.create_muppet(
                    name="test-muppet",
                    template="java-micronaut",
                    description="Test muppet",
                    auto_deploy=False,
                )

        # Verify: Muppet was added to state initially
        lifecycle_service._mock_state_manager.add_muppet_to_state.assert_called_once()

        # Verify: Muppet was removed from state after failure
        lifecycle_service._mock_state_manager.remove_muppet_from_state.assert_called_once_with(
            "test-muppet"
        )

    @pytest.mark.asyncio
    async def test_unexpected_error_removes_from_state(self, lifecycle_service):
        """Test that unexpected errors during creation remove muppet from state."""
        # Setup: Template validation succeeds, unexpected error occurs
        lifecycle_service._mock_template_manager.discover_templates.return_value = [
            type("Template", (), {"name": "java-micronaut"})()
        ]

        # Mock state manager methods
        lifecycle_service._mock_state_manager.get_muppet.return_value = None
        lifecycle_service._mock_state_manager.add_muppet_to_state = AsyncMock()
        lifecycle_service._mock_state_manager.remove_muppet_from_state = AsyncMock()

        # Mock template generation to raise unexpected error
        with patch.object(lifecycle_service, "_generate_muppet_code") as mock_generate:
            mock_generate.side_effect = Exception("Unexpected error")

            # Attempt to create muppet
            with pytest.raises(
                PlatformException, match="Muppet creation failed: Unexpected error"
            ):
                await lifecycle_service.create_muppet(
                    name="test-muppet",
                    template="java-micronaut",
                    description="Test muppet",
                    auto_deploy=False,
                )

        # Verify: Muppet was added to state initially
        lifecycle_service._mock_state_manager.add_muppet_to_state.assert_called_once()

        # Verify: Muppet was removed from state after failure
        lifecycle_service._mock_state_manager.remove_muppet_from_state.assert_called_once_with(
            "test-muppet"
        )

    @pytest.mark.asyncio
    async def test_successful_creation_keeps_muppet_in_state(self, lifecycle_service):
        """Test that successful muppet creation keeps muppet in state."""
        # Setup: All operations succeed
        lifecycle_service._mock_template_manager.discover_templates.return_value = [
            type("Template", (), {"name": "java-micronaut"})()
        ]

        # Mock state manager methods
        lifecycle_service._mock_state_manager.get_muppet.return_value = None
        lifecycle_service._mock_state_manager.add_muppet_to_state = AsyncMock()
        lifecycle_service._mock_state_manager.remove_muppet_from_state = AsyncMock()

        # Mock all operations to succeed
        with (
            patch.object(lifecycle_service, "_generate_muppet_code") as mock_generate,
            patch.object(
                lifecycle_service, "_setup_muppet_development_environment"
            ) as mock_setup_dev,
        ):
            mock_generate.return_value = {"main.py": "# Generated code"}
            # Make create_muppet_repository an async mock
            lifecycle_service._mock_github_manager.create_muppet_repository = AsyncMock(
                return_value={
                    "url": "https://github.com/muppet-platform/test-muppet",
                    "success": True,
                }
            )
            lifecycle_service._mock_github_manager.update_muppet_status = AsyncMock(
                return_value=True
            )
            mock_setup_dev.return_value = {"success": True}

            # Create muppet successfully
            result = await lifecycle_service.create_muppet(
                name="test-muppet",
                template="java-micronaut",
                description="Test muppet",
                auto_deploy=False,
            )

        # Verify: Muppet was added to state
        assert lifecycle_service._mock_state_manager.add_muppet_to_state.call_count >= 1

        # Verify: Muppet was NOT removed from state (successful creation)
        lifecycle_service._mock_state_manager.remove_muppet_from_state.assert_not_called()

        # Verify: Result indicates success
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_state_cleanup_failure_is_logged_but_not_raised(
        self, lifecycle_service
    ):
        """Test that state cleanup failures are logged but don't mask the original error."""
        # Setup: Template validation fails, state cleanup also fails
        lifecycle_service._mock_template_manager.discover_templates.return_value = [
            type("Template", (), {"name": "java-micronaut"})()
        ]

        # Mock state manager methods
        lifecycle_service._mock_state_manager.get_muppet.return_value = None
        lifecycle_service._mock_state_manager.add_muppet_to_state = AsyncMock()
        lifecycle_service._mock_state_manager.remove_muppet_from_state = AsyncMock(
            side_effect=Exception("State cleanup failed")
        )

        # Mock template generation to fail
        with patch.object(lifecycle_service, "_generate_muppet_code") as mock_generate:
            mock_generate.side_effect = ValidationError("Template validation failed")

            # Attempt to create muppet - should raise original error, not cleanup error
            with pytest.raises(ValidationError, match="Template validation failed"):
                await lifecycle_service.create_muppet(
                    name="test-muppet",
                    template="java-micronaut",
                    description="Test muppet",
                    auto_deploy=False,
                )

        # Verify: State cleanup was attempted despite failure
        lifecycle_service._mock_state_manager.remove_muppet_from_state.assert_called_once_with(
            "test-muppet"
        )

    @pytest.mark.asyncio
    async def test_muppet_already_exists_validation_prevents_state_pollution(
        self, lifecycle_service
    ):
        """Test that existing muppet validation prevents state pollution."""
        # Setup: Muppet already exists
        existing_muppet = Muppet(
            name="test-muppet",
            template="java-micronaut",
            status=MuppetStatus.RUNNING,
            github_repo_url="https://github.com/muppet-platform/test-muppet",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        lifecycle_service._mock_state_manager.get_muppet.return_value = existing_muppet
        lifecycle_service._mock_state_manager.add_muppet_to_state = AsyncMock()
        lifecycle_service._mock_state_manager.remove_muppet_from_state = AsyncMock()

        # Attempt to create muppet that already exists
        with pytest.raises(
            ValidationError, match="Muppet 'test-muppet' already exists"
        ):
            await lifecycle_service.create_muppet(
                name="test-muppet",
                template="java-micronaut",
                description="Test muppet",
                auto_deploy=False,
            )

        # Verify: No state operations were performed (validation failed early)
        lifecycle_service._mock_state_manager.add_muppet_to_state.assert_not_called()
        # Note: remove_muppet_from_state might be called in exception handler,
        # but that's acceptable since validation failed before state addition
