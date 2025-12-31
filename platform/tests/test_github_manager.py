"""
Tests for the GitHub Manager functionality.

This module tests the GitHubManager and its integration with
the GitHub API client for muppet repository management.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.exceptions import GitHubError, ValidationError
from src.managers.github_manager import GitHubManager
from src.models import Muppet, MuppetStatus


@pytest.fixture
def github_manager():
    """Create a GitHubManager instance for testing."""
    return GitHubManager()


@pytest.fixture
def mock_repo_data():
    """Mock repository data from GitHub API."""
    return {
        "name": "test-muppet",
        "full_name": "muppet-platform/test-muppet",
        "html_url": "https://github.com/muppet-platform/test-muppet",
        "description": "Test muppet repository",
        "private": True,
        "topics": ["template:java-micronaut", "status:creating", "muppet"],
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "default_branch": "main",
    }


@pytest.fixture
def mock_template_files():
    """Mock template files for code deployment."""
    return {
        "README.md": "# Test Muppet\n\nThis is a test muppet.",
        "src/main/java/Application.java": "public class Application { }",
        "build.gradle": "plugins { id 'java' }",
    }


@pytest.mark.asyncio
async def test_github_manager_initialization(github_manager):
    """Test that GitHubManager initializes correctly."""
    assert github_manager is not None
    assert github_manager.client is not None
    assert github_manager.settings is not None


@pytest.mark.asyncio
async def test_create_muppet_repository_success(
    github_manager, mock_repo_data, mock_template_files
):
    """Test successful muppet repository creation."""
    with (
        patch.object(github_manager.client, "create_repository") as mock_create,
        patch.object(
            github_manager.client, "setup_repository_permissions"
        ) as mock_permissions,
        patch.object(github_manager.client, "push_template_code") as mock_push,
        patch.object(github_manager, "_validate_repository_inputs") as mock_validate,
    ):
        # Setup mocks
        mock_create.return_value = mock_repo_data
        mock_permissions.return_value = True
        mock_push.return_value = True
        mock_validate.return_value = None

        # Create repository
        result = await github_manager.create_muppet_repository(
            muppet_name="test-muppet",
            template="java-micronaut",
            description="Test muppet",
            template_files=mock_template_files,
        )

        # Verify calls
        mock_validate.assert_called_once_with("test-muppet", "java-micronaut")
        mock_create.assert_called_once_with(
            name="test-muppet", template="java-micronaut", description="Test muppet"
        )
        mock_permissions.assert_called_once_with("test-muppet", None)
        mock_push.assert_called_once_with(
            "test-muppet", "java-micronaut", mock_template_files
        )

        # Verify result
        assert result["name"] == "test-muppet"
        assert result["url"] == "https://github.com/muppet-platform/test-muppet"
        assert result["template"] == "java-micronaut"
        assert result["configuration"]["workflows_configured"] is True
        assert result["configuration"]["branch_protection"] is True


@pytest.mark.asyncio
async def test_create_muppet_repository_without_template_files(
    github_manager, mock_repo_data
):
    """Test muppet repository creation without template files."""
    with (
        patch.object(github_manager.client, "create_repository") as mock_create,
        patch.object(
            github_manager.client, "setup_repository_permissions"
        ) as mock_permissions,
        patch.object(github_manager.client, "push_template_code") as mock_push,
        patch.object(github_manager, "_validate_repository_inputs") as mock_validate,
    ):
        # Setup mocks
        mock_create.return_value = mock_repo_data
        mock_permissions.return_value = True
        mock_validate.return_value = None

        # Create repository without template files
        result = await github_manager.create_muppet_repository(
            muppet_name="test-muppet", template="java-micronaut"
        )

        # Verify template code push was not called
        mock_push.assert_not_called()

        # Verify result
        assert result["name"] == "test-muppet"
        assert result["template"] == "java-micronaut"


@pytest.mark.asyncio
async def test_create_muppet_repository_validation_error(github_manager):
    """Test repository creation with validation error."""
    with patch.object(github_manager, "_validate_repository_inputs") as mock_validate:
        mock_validate.side_effect = ValidationError("Invalid muppet name")

        with pytest.raises(ValidationError, match="Invalid muppet name"):
            await github_manager.create_muppet_repository(
                muppet_name="", template="java-micronaut"
            )


@pytest.mark.asyncio
async def test_create_muppet_repository_github_error(github_manager):
    """Test repository creation with GitHub API error."""
    with (
        patch.object(github_manager.client, "create_repository") as mock_create,
        patch.object(github_manager, "_validate_repository_inputs") as mock_validate,
    ):
        mock_validate.return_value = None
        mock_create.side_effect = GitHubError("Repository already exists")

        with pytest.raises(GitHubError, match="Repository already exists"):
            await github_manager.create_muppet_repository(
                muppet_name="test-muppet", template="java-micronaut"
            )


# delete_muppet_repository tests removed - deletion is now a manual operation for safety


@pytest.mark.asyncio
async def test_update_muppet_status_success(github_manager):
    """Test successful muppet status update."""
    with patch.object(github_manager.client, "update_repository_status") as mock_update:
        mock_update.return_value = True

        result = await github_manager.update_muppet_status("test-muppet", "running")

        mock_update.assert_called_once_with("test-muppet", "running")
        assert result is True


@pytest.mark.asyncio
async def test_update_muppet_status_invalid_status(github_manager):
    """Test muppet status update with invalid status."""
    with pytest.raises(ValidationError, match="Invalid status 'invalid'"):
        await github_manager.update_muppet_status("test-muppet", "invalid")


@pytest.mark.asyncio
async def test_get_muppet_repositories(github_manager):
    """Test getting all muppet repositories."""
    mock_muppets = [
        Muppet(
            name="muppet1",
            template="java-micronaut",
            status=MuppetStatus.RUNNING,
            github_repo_url="https://github.com/muppet-platform/muppet1",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        ),
        Muppet(
            name="muppet2",
            template="java-micronaut",
            status=MuppetStatus.STOPPED,
            github_repo_url="https://github.com/muppet-platform/muppet2",
            created_at=datetime(2024, 1, 2, 9, 0, 0),
            updated_at=datetime(2024, 1, 2, 11, 30, 0),
        ),
    ]

    with patch.object(github_manager.client, "discover_muppets") as mock_discover:
        mock_discover.return_value = mock_muppets

        repositories = await github_manager.get_muppet_repositories()

        assert len(repositories) == 2
        assert repositories[0]["name"] == "muppet1"
        assert repositories[0]["template"] == "java-micronaut"
        assert repositories[0]["status"] == "running"
        assert repositories[1]["name"] == "muppet2"
        assert repositories[1]["template"] == "java-micronaut"
        assert repositories[1]["status"] == "stopped"


@pytest.mark.asyncio
async def test_get_repository_info_success(github_manager, mock_repo_data):
    """Test getting repository information."""
    mock_collaborators = [
        {"login": "admin", "permissions": {"admin": True, "push": True, "pull": True}},
        {"login": "dev1", "permissions": {"admin": False, "push": True, "pull": True}},
    ]

    with (
        patch.object(github_manager.client, "get_repository") as mock_get,
        patch.object(
            github_manager.client, "get_repository_collaborators"
        ) as mock_collab,
    ):
        mock_get.return_value = mock_repo_data
        mock_collab.return_value = mock_collaborators

        info = await github_manager.get_repository_info("test-muppet")

        assert info["name"] == "test-muppet"
        assert info["template"] == "java-micronaut"
        assert info["status"] == "creating"
        assert info["collaborators"] == 2
        assert info["private"] is True


@pytest.mark.asyncio
async def test_get_repository_info_not_found(github_manager):
    """Test getting repository information when repository doesn't exist."""
    with patch.object(github_manager.client, "get_repository") as mock_get:
        mock_get.return_value = None

        info = await github_manager.get_repository_info("nonexistent")

        assert info is None


@pytest.mark.asyncio
async def test_add_collaborator_success(github_manager):
    """Test adding collaborator to repository."""
    with patch.object(github_manager.client, "add_repository_collaborator") as mock_add:
        mock_add.return_value = True

        result = await github_manager.add_collaborator("test-muppet", "newdev", "push")

        mock_add.assert_called_once_with("test-muppet", "newdev", "push")
        assert result is True


@pytest.mark.asyncio
async def test_add_collaborator_invalid_permission(github_manager):
    """Test adding collaborator with invalid permission."""
    with pytest.raises(ValidationError, match="Invalid permission 'invalid'"):
        await github_manager.add_collaborator("test-muppet", "newdev", "invalid")


@pytest.mark.asyncio
async def test_remove_collaborator_success(github_manager):
    """Test removing collaborator from repository."""
    with patch.object(
        github_manager.client, "remove_repository_collaborator"
    ) as mock_remove:
        mock_remove.return_value = True

        result = await github_manager.remove_collaborator("test-muppet", "olddev")

        mock_remove.assert_called_once_with("test-muppet", "olddev")
        assert result is True


@pytest.mark.asyncio
async def test_validate_repository_inputs_valid(github_manager):
    """Test repository input validation with valid inputs."""
    # Should not raise any exception
    github_manager._validate_repository_inputs("valid-muppet-name", "java-micronaut")


@pytest.mark.asyncio
async def test_validate_repository_inputs_invalid_name(github_manager):
    """Test repository input validation with invalid muppet name."""
    # Empty name
    with pytest.raises(ValidationError, match="Muppet name must be a non-empty string"):
        github_manager._validate_repository_inputs("", "java-micronaut")

    # Too long name
    long_name = "a" * 101
    with pytest.raises(
        ValidationError, match="Muppet name must be 100 characters or less"
    ):
        github_manager._validate_repository_inputs(long_name, "java-micronaut")

    # Invalid characters
    with pytest.raises(
        ValidationError, match="can only contain alphanumeric characters"
    ):
        github_manager._validate_repository_inputs("invalid@name", "java-micronaut")


@pytest.mark.asyncio
async def test_validate_repository_inputs_invalid_template(github_manager):
    """Test repository input validation with invalid template."""
    # Empty template
    with pytest.raises(ValidationError, match="Template must be a non-empty string"):
        github_manager._validate_repository_inputs("valid-name", "")

    # None template
    with pytest.raises(ValidationError, match="Template must be a non-empty string"):
        github_manager._validate_repository_inputs("valid-name", None)


@pytest.mark.asyncio
async def test_close(github_manager):
    """Test closing the GitHub manager."""
    with patch.object(github_manager.client, "close") as mock_close:
        await github_manager.close()
        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_create_muppet_repository_with_custom_permissions(
    github_manager, mock_repo_data
):
    """Test repository creation with custom team permissions."""
    custom_permissions = {"custom-team": "admin", "dev-team": "push"}

    with (
        patch.object(github_manager.client, "create_repository") as mock_create,
        patch.object(
            github_manager.client, "setup_repository_permissions"
        ) as mock_permissions,
        patch.object(github_manager, "_validate_repository_inputs") as mock_validate,
    ):
        mock_create.return_value = mock_repo_data
        mock_permissions.return_value = True
        mock_validate.return_value = None

        result = await github_manager.create_muppet_repository(
            muppet_name="test-muppet",
            template="java-micronaut",
            team_permissions=custom_permissions,
        )

        mock_permissions.assert_called_once_with("test-muppet", custom_permissions)
        assert result["configuration"]["permissions_configured"] is True


@pytest.mark.asyncio
async def test_error_handling_in_create_repository(github_manager):
    """Test error handling during repository creation."""
    with (
        patch.object(github_manager.client, "create_repository") as mock_create,
        patch.object(github_manager, "_validate_repository_inputs") as mock_validate,
    ):
        mock_validate.return_value = None
        mock_create.side_effect = Exception("Unexpected error")

        with pytest.raises(GitHubError, match="Failed to create muppet repository"):
            await github_manager.create_muppet_repository(
                muppet_name="test-muppet", template="java-micronaut"
            )


@pytest.mark.asyncio
async def test_error_handling_in_get_repositories(github_manager):
    """Test error handling when getting repositories."""
    with patch.object(github_manager.client, "discover_muppets") as mock_discover:
        mock_discover.side_effect = Exception("API error")

        with pytest.raises(GitHubError, match="Failed to get muppet repositories"):
            await github_manager.get_muppet_repositories()
