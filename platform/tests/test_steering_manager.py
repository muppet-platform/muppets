"""
Tests for the Steering Manager component.

Tests the centralized steering documentation management system.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.integrations.github import GitHubClient
from src.managers.steering_manager import (
    SteeringDocument,
    SteeringManager,
    SteeringVersion,
)
from src.models import Muppet


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client."""
    client = AsyncMock(spec=GitHubClient)
    return client


@pytest.fixture
def steering_manager(mock_github_client):
    """Create a steering manager with mocked dependencies."""
    return SteeringManager(mock_github_client)


@pytest.mark.asyncio
async def test_steering_manager_initialization(steering_manager):
    """Test steering manager initialization."""
    assert steering_manager.github_client is not None
    assert (
        steering_manager.steering_repo_url
        == "https://github.com/muppet-platform/steering-docs.git"
    )
    assert steering_manager.local_steering_path.name == "steering-docs"


@pytest.mark.asyncio
async def test_get_shared_steering_documents(steering_manager):
    """Test getting shared steering documents."""
    # Mock the file system
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
        patch("aiofiles.open") as mock_open,
    ):
        # Mock file paths
        mock_file = MagicMock()
        mock_file.stem = "http-responses"
        mock_file.stat.return_value.st_mtime = 1642680000
        mock_file.relative_to.return_value = "shared/http-responses.md"
        mock_glob.return_value = [mock_file]

        # Mock file content
        mock_open.return_value.__aenter__.return_value.read = AsyncMock(
            return_value="# HTTP Response Standards\n\nContent here..."
        )

        # Mock version method
        steering_manager._get_document_version = AsyncMock(return_value="v1.0.0")

        documents = await steering_manager.get_shared_steering_documents()

        assert len(documents) == 1
        assert documents[0].name == "http-responses"
        assert documents[0].category == "shared"
        assert documents[0].version == "v1.0.0"


@pytest.mark.asyncio
async def test_get_template_steering_documents(steering_manager):
    """Test getting template-specific steering documents."""
    template_type = "java-micronaut"

    # Mock the file system
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.glob") as mock_glob,
        patch("aiofiles.open") as mock_open,
    ):
        # Mock file paths
        mock_file = MagicMock()
        mock_file.stem = "micronaut-patterns"
        mock_file.stat.return_value.st_mtime = 1642680000
        mock_file.relative_to.return_value = (
            "templates/java-micronaut/micronaut-patterns.md"
        )
        mock_glob.return_value = [mock_file]

        # Mock file content
        mock_open.return_value.__aenter__.return_value.read = AsyncMock(
            return_value="# Micronaut Patterns\n\nContent here..."
        )

        # Mock version method
        steering_manager._get_document_version = AsyncMock(return_value="v1.0.0")

        documents = await steering_manager.get_template_steering_documents(
            template_type
        )

        assert len(documents) == 1
        assert documents[0].name == "micronaut-patterns"
        assert documents[0].category == "template-specific"
        assert documents[0].template_type == template_type


@pytest.mark.asyncio
async def test_distribute_steering_to_muppet(steering_manager):
    """Test distributing steering documents to a muppet."""
    muppet = Muppet(
        name="test-muppet",
        template="java-micronaut",
        status="creating",
        github_repo_url="https://github.com/muppet-platform/test-muppet",
        fargate_service_arn="arn:aws:ecs:us-east-1:123456789012:service/test-muppet",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        terraform_version="1.6.0",  # OpenTofu version
    )

    # Mock the steering document methods
    shared_docs = [
        SteeringDocument(
            name="http-responses",
            path="shared/http-responses.md",
            content="# HTTP Response Standards",
            version="v1.0.0",
            last_updated=datetime.utcnow(),
            category="shared",
        )
    ]

    template_docs = [
        SteeringDocument(
            name="micronaut-patterns",
            path="templates/java-micronaut/micronaut-patterns.md",
            content="# Micronaut Patterns",
            version="v1.0.0",
            last_updated=datetime.utcnow(),
            category="template-specific",
            template_type="java-micronaut",
        )
    ]

    steering_manager.get_shared_steering_documents = AsyncMock(return_value=shared_docs)
    steering_manager.get_template_steering_documents = AsyncMock(
        return_value=template_docs
    )
    steering_manager._create_muppet_steering_structure = AsyncMock()
    steering_manager._update_muppet_steering_version = AsyncMock()

    result = await steering_manager.distribute_steering_to_muppet(muppet)

    assert result is True
    steering_manager.get_shared_steering_documents.assert_called_once()
    steering_manager.get_template_steering_documents.assert_called_once_with(
        "java-micronaut"
    )
    steering_manager._create_muppet_steering_structure.assert_called_once()
    steering_manager._update_muppet_steering_version.assert_called_once()


@pytest.mark.asyncio
async def test_list_steering_documents(steering_manager):
    """Test listing steering documents."""
    # Mock the steering document methods
    shared_docs = [
        SteeringDocument(
            name="http-responses",
            path="shared/http-responses.md",
            content="# HTTP Response Standards",
            version="v1.0.0",
            last_updated=datetime.utcnow(),
            category="shared",
        )
    ]

    steering_manager.get_shared_steering_documents = AsyncMock(return_value=shared_docs)
    steering_manager.get_template_steering_documents = AsyncMock(return_value=[])

    result = await steering_manager.list_steering_documents()

    assert "shared" in result
    assert "template-specific" in result
    assert "muppet-specific" in result
    assert len(result["shared"]) == 1
    assert result["shared"][0]["name"] == "http-responses"


@pytest.mark.asyncio
async def test_update_shared_steering_across_muppets(steering_manager):
    """Test updating shared steering across muppets."""
    # Mock the steering document methods
    shared_docs = [
        SteeringDocument(
            name="http-responses",
            path="shared/http-responses.md",
            content="# HTTP Response Standards",
            version="v2.0.0",
            last_updated=datetime.utcnow(),
            category="shared",
        )
    ]

    steering_manager.get_shared_steering_documents = AsyncMock(return_value=shared_docs)
    steering_manager._refresh_steering_repo = AsyncMock()
    steering_manager._update_muppet_shared_steering = AsyncMock(return_value=True)

    # Mock version cache
    steering_manager._version_cache = {
        "test-muppet": SteeringVersion(
            muppet_name="test-muppet",
            shared_version="v1.0.0",
            last_updated=datetime.utcnow(),
        )
    }

    results = await steering_manager.update_shared_steering_across_muppets(
        ["test-muppet"]
    )

    assert results["test-muppet"] is True
    steering_manager._refresh_steering_repo.assert_called_once()
    steering_manager._update_muppet_shared_steering.assert_called_once()


@pytest.mark.asyncio
async def test_get_muppet_steering_status(steering_manager):
    """Test getting muppet steering status."""
    muppet_name = "test-muppet"

    # Mock version cache
    version_info = SteeringVersion(
        muppet_name=muppet_name, shared_version="v1.0.0", last_updated=datetime.utcnow()
    )
    steering_manager._version_cache[muppet_name] = version_info

    # Mock shared docs
    shared_docs = [
        SteeringDocument(
            name="http-responses",
            path="shared/http-responses.md",
            content="# HTTP Response Standards",
            version="v2.0.0",
            last_updated=datetime.utcnow(),
            category="shared",
        )
    ]
    steering_manager.get_shared_steering_documents = AsyncMock(return_value=shared_docs)

    status = await steering_manager.get_muppet_steering_status(muppet_name)

    assert status["muppet_name"] == muppet_name
    assert status["status"] == "updates_available"
    assert status["shared_version"] == "v1.0.0"
    assert status["latest_shared_version"] == "v2.0.0"
    assert status["updates_available"] is True


@pytest.mark.asyncio
async def test_get_muppet_steering_status_not_initialized(steering_manager):
    """Test getting steering status for uninitialized muppet."""
    muppet_name = "unknown-muppet"

    status = await steering_manager.get_muppet_steering_status(muppet_name)

    assert status["muppet_name"] == muppet_name
    assert status["status"] == "not_initialized"
    assert status["shared_version"] is None


@pytest.mark.asyncio
async def test_steering_manager_close(steering_manager):
    """Test steering manager cleanup."""
    await steering_manager.close()
    # Should not raise any exceptions
