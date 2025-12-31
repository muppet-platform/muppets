"""
Tests for the state management functionality.

This module tests the StateManager and its integration with
GitHub, Parameter Store, and ECS clients.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.exceptions import PlatformException
from src.models import Muppet, MuppetStatus, PlatformState
from src.state_manager import StateManager, get_state_manager


@pytest.fixture
def state_manager():
    """Create a StateManager instance for testing."""
    return StateManager()


@pytest.mark.asyncio
async def test_state_manager_initialization(state_manager):
    """Test that StateManager initializes correctly."""
    assert state_manager is not None
    assert state_manager.github_client is not None
    assert state_manager.parameter_store is not None
    assert state_manager.ecs_client is not None
    assert state_manager._state is None
    assert state_manager._initialized is False


@pytest.mark.asyncio
async def test_initialize_state_manager(state_manager):
    """Test state manager initialization."""
    # Mock the integration clients
    with (
        patch.object(state_manager.github_client, "discover_muppets") as mock_github,
        patch.object(
            state_manager.parameter_store, "get_parameters_by_path"
        ) as mock_params,
        patch.object(state_manager.ecs_client, "get_active_deployments") as mock_ecs,
    ):
        # Setup mock responses
        mock_muppets = [
            Muppet(
                name="test-muppet",
                template="java-micronaut",
                status=MuppetStatus.RUNNING,
                github_repo_url="https://github.com/muppet-platform/test-muppet",
                created_at=datetime.utcnow(),
            )
        ]
        mock_github.return_value = mock_muppets

        mock_params.return_value = {
            "terraform/modules/fargate-service/version": "1.2.0",
            "terraform/modules/monitoring/version": "1.1.0",
        }

        mock_ecs.return_value = {
            "test-muppet": "arn:aws:ecs:us-west-2:123456789012:service/cluster/test-muppet"
        }

        # Initialize state manager
        await state_manager.initialize()

        # Verify initialization
        assert state_manager._initialized is True
        assert state_manager._state is not None
        assert len(state_manager._state.muppets) == 1
        assert state_manager._state.muppets[0].name == "test-muppet"


@pytest.mark.asyncio
async def test_get_state_after_initialization(state_manager):
    """Test getting state after initialization."""
    # Mock the integration clients
    with (
        patch.object(state_manager.github_client, "discover_muppets") as mock_github,
        patch.object(
            state_manager.parameter_store, "get_parameters_by_path"
        ) as mock_params,
        patch.object(state_manager.ecs_client, "get_active_deployments") as mock_ecs,
    ):
        # Setup mock responses
        mock_muppets = [
            Muppet(
                name="test-muppet",
                template="java-micronaut",
                status=MuppetStatus.RUNNING,
                github_repo_url="https://github.com/muppet-platform/test-muppet",
                created_at=datetime.utcnow(),
            )
        ]
        mock_github.return_value = mock_muppets

        mock_params.return_value = {
            "terraform/modules/fargate-service/version": "1.2.0",
            "terraform/modules/monitoring/version": "1.1.0",
        }

        mock_ecs.return_value = {
            "test-muppet": "arn:aws:ecs:us-west-2:123456789012:service/cluster/test-muppet"
        }

        # Initialize and get state
        await state_manager.initialize()
        state = await state_manager.get_state()

        # Verify state
        assert isinstance(state, PlatformState)
        assert len(state.muppets) == 1
        assert state.muppets[0].name == "test-muppet"
        assert (
            state.muppets[0].fargate_service_arn
            == "arn:aws:ecs:us-west-2:123456789012:service/cluster/test-muppet"
        )
        assert len(state.terraform_versions) == 2
        assert state.terraform_versions["fargate-service"] == "1.2.0"
        assert len(state.active_deployments) == 1


@pytest.mark.asyncio
async def test_get_state_not_initialized(state_manager):
    """Test that get_state returns empty state when not initialized."""
    state = await state_manager.get_state()

    # Should return empty state instead of raising exception
    assert isinstance(state, PlatformState)
    assert len(state.muppets) == 0
    assert state.initialized is False
    assert len(state.active_deployments) == 0
    assert len(state.terraform_versions) == 0


@pytest.mark.asyncio
async def test_refresh_state(state_manager):
    """Test refreshing state from sources."""
    # Initialize first
    with patch.object(state_manager, "_load_state_from_sources") as mock_load:
        mock_state = PlatformState.empty()
        mock_load.return_value = mock_state

        await state_manager.initialize()
        assert mock_load.call_count == 1

        # Refresh should call load again
        await state_manager.refresh_state()
        assert mock_load.call_count == 2


@pytest.mark.asyncio
async def test_get_muppet(state_manager):
    """Test getting a specific muppet by name."""
    # Initialize state manager first
    with patch.object(state_manager, "_load_state_from_sources") as mock_load:
        mock_muppet = Muppet(
            name="test-muppet",
            template="java-micronaut",
            status=MuppetStatus.RUNNING,
            github_repo_url="https://github.com/muppet-platform/test-muppet",
        )
        mock_state = PlatformState(
            muppets=[mock_muppet],
            active_deployments={},
            terraform_versions={},
            last_updated=datetime.utcnow(),
        )
        mock_load.return_value = mock_state

        await state_manager.initialize()

        # Test finding existing muppet
        muppet = await state_manager.get_muppet("test-muppet")
        assert muppet is not None
        assert muppet.name == "test-muppet"

        # Test muppet not found
        muppet = await state_manager.get_muppet("nonexistent")
        assert muppet is None


@pytest.mark.asyncio
async def test_list_muppets(state_manager):
    """Test listing all muppets."""
    # Initialize state manager first
    with patch.object(state_manager, "_load_state_from_sources") as mock_load:
        mock_muppets = [
            Muppet(
                name="muppet1",
                template="java-micronaut",
                status=MuppetStatus.RUNNING,
                github_repo_url="https://github.com/muppet-platform/muppet1",
            ),
            Muppet(
                name="muppet2",
                template="java-micronaut",
                status=MuppetStatus.STOPPED,
                github_repo_url="https://github.com/muppet-platform/muppet2",
            ),
        ]
        mock_state = PlatformState(
            muppets=mock_muppets,
            active_deployments={},
            terraform_versions={},
            last_updated=datetime.utcnow(),
        )
        mock_load.return_value = mock_state

        await state_manager.initialize()

        muppets = await state_manager.list_muppets()
        assert len(muppets) == 2
        assert muppets[0].name == "muppet1"
        assert muppets[1].name == "muppet2"


@pytest.mark.asyncio
async def test_update_muppet_status(state_manager):
    """Test updating muppet status."""
    # Initialize state manager first
    with patch.object(state_manager, "_load_state_from_sources") as mock_load:
        mock_muppet = Muppet(
            name="test-muppet",
            template="java-micronaut",
            status=MuppetStatus.CREATING,
            github_repo_url="https://github.com/muppet-platform/test-muppet",
        )
        mock_state = PlatformState(
            muppets=[mock_muppet],
            active_deployments={},
            terraform_versions={},
            last_updated=datetime.utcnow(),
        )
        mock_load.return_value = mock_state

        await state_manager.initialize()

        with patch.object(
            state_manager.github_client, "update_repository_status"
        ) as mock_update:
            mock_update.return_value = True

            # Test successful status update
            result = await state_manager.update_muppet_status(
                "test-muppet", MuppetStatus.RUNNING
            )
            assert result is True
            mock_update.assert_called_once_with("test-muppet", "running")

            # Verify local state was updated
            muppet = await state_manager.get_muppet("test-muppet")
            assert muppet.status == MuppetStatus.RUNNING


@pytest.mark.asyncio
async def test_add_muppet_to_state(state_manager):
    """Test adding muppet to state."""
    # Initialize with empty state
    with patch.object(state_manager, "_load_state_from_sources") as mock_load:
        mock_load.return_value = PlatformState.empty()
        await state_manager.initialize()

    # Add muppet
    test_muppet = Muppet(
        name="new-muppet",
        template="java-micronaut",
        status=MuppetStatus.CREATING,
        github_repo_url="https://github.com/muppet-platform/new-muppet",
    )

    await state_manager.add_muppet_to_state(test_muppet)

    # Verify muppet was added to state
    muppets = await state_manager.list_muppets()
    assert len(muppets) == 1
    assert muppets[0].name == "new-muppet"


@pytest.mark.asyncio
async def test_remove_muppet_from_state(state_manager):
    """Test removing muppet from state."""
    # Initialize with a muppet
    test_muppet = Muppet(
        name="test-muppet",
        template="java-micronaut",
        status=MuppetStatus.RUNNING,
        github_repo_url="https://github.com/muppet-platform/test-muppet",
    )

    with patch.object(state_manager, "_load_state_from_sources") as mock_load:
        initial_state = PlatformState(
            muppets=[test_muppet],
            active_deployments={},
            terraform_versions={},
            last_updated=datetime.utcnow(),
        )
        mock_load.return_value = initial_state
        await state_manager.initialize()

    # Remove muppet
    await state_manager.remove_muppet_from_state("test-muppet")

    # Verify muppet was removed from state
    muppets = await state_manager.list_muppets()
    assert len(muppets) == 0


@pytest.mark.asyncio
async def test_get_platform_health(state_manager):
    """Test getting platform health metrics."""
    # Initialize with mock state
    with patch.object(state_manager, "_load_state_from_sources") as mock_load:
        # Create mock state with various muppet statuses
        mock_muppets = [
            Muppet(
                name="running-muppet",
                template="java-micronaut",
                status=MuppetStatus.RUNNING,
                github_repo_url="https://github.com/muppet-platform/running-muppet",
            ),
            Muppet(
                name="error-muppet",
                template="java-micronaut",
                status=MuppetStatus.ERROR,
                github_repo_url="https://github.com/muppet-platform/error-muppet",
            ),
        ]
        mock_state = PlatformState(
            muppets=mock_muppets,
            active_deployments={
                "running-muppet": "arn:aws:ecs:us-west-2:123456789012:service/cluster/running-muppet"
            },
            terraform_versions={"fargate-service": "1.2.0"},
            last_updated=datetime.utcnow(),
        )
        mock_load.return_value = mock_state

        await state_manager.initialize()

        # Get health metrics
        health = await state_manager.get_platform_health()

        # Verify health metrics
        assert health["total_muppets"] == 2
        assert health["status_counts"]["running"] == 1
        assert health["status_counts"]["error"] == 1
        assert health["active_deployments"] == 1
        assert health["terraform_modules"] == 1
        assert (
            health["health_score"] == 0.25
        )  # 1 running, 1 error = (1/2) * (1 - 1/2) = 0.25
        assert "last_updated" in health
        assert health["initialized"] is True


def test_get_state_manager_singleton():
    """Test that get_state_manager returns a singleton."""
    manager1 = get_state_manager()
    manager2 = get_state_manager()

    assert manager1 is manager2
    assert isinstance(manager1, StateManager)
