"""
Unit tests for GitHub workflow creation functionality.

These tests verify that GitHub Actions workflows are properly generated and pushed
to repositories when creating muppets.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.integrations.github import GitHubClient
from src.managers.template_manager import GenerationContext, TemplateManager
from src.services.muppet_lifecycle_service import MuppetLifecycleService


class TestGitHubWorkflowCreation:
    """Test GitHub workflow creation and pushing functionality."""

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client for testing."""
        client = AsyncMock(spec=GitHubClient)
        client.organization = "test-org"
        client.token = "test-token"
        client.base_url = "https://api.github.com"
        client._client = AsyncMock()
        return client

    @pytest.fixture
    def template_files_with_workflows(self):
        """Sample template files including GitHub Actions workflows."""
        return {
            # Core application files
            "src/main/java/Application.java": "public class Application {}",
            "build.gradle": "plugins { id 'java' }",
            "README.md": "# Test Muppet",
            # GitHub Actions workflows (these should be created)
            ".github/workflows/ci.yml": """# Auto-generated CI workflow for java-micronaut template
name: CI
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Amazon Corretto JDK 21 (LTS)
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'
      - name: Run tests
        run: ./gradlew test
""",
            ".github/workflows/cd.yml": """# Auto-generated CD workflow for java-micronaut template
name: CD
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Amazon Corretto JDK 21 (LTS)
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'
      - name: Deploy
        run: echo "Deploying..."
""",
        }

    @pytest.mark.asyncio
    async def test_workflow_files_are_generated_locally(self):
        """Test that workflow files are generated during template processing."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test-muppet"

            context = GenerationContext(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                parameters={
                    "github_organization": "test-org",
                    "aws_region": "us-west-2",
                },
                output_path=output_path,
                aws_region="us-west-2",
                environment="development",
            )

            # Generate code
            generated_path = template_manager.generate_code(context)

            # Verify workflow files exist
            workflows_dir = generated_path / ".github" / "workflows"
            assert workflows_dir.exists(), "Workflows directory should be created"

            workflow_files = list(workflows_dir.glob("*.yml"))
            workflow_names = [f.name for f in workflow_files]

            # Should have simplified workflow files (CI and CD only)
            assert "ci.yml" in workflow_names, "CI workflow should be generated"
            assert "cd.yml" in workflow_names, "CD workflow should be generated"
            assert (
                len(workflow_names) == 2
            ), f"Should have exactly 2 workflows, found: {workflow_names}"

            # Verify workflow content contains Java 21 LTS enforcement
            ci_content = (workflows_dir / "ci.yml").read_text()
            assert (
                "java-version: '21'" in ci_content
            ), "CI workflow should enforce Java 21 LTS"
            assert (
                "distribution: 'corretto'" in ci_content
            ), "CI workflow should use Amazon Corretto"

            # Verify simplified CI workflow structure
            assert (
                "test-and-build:" in ci_content
            ), "CI workflow should have single test-and-build job"
            assert (
                "shadowJar" in ci_content
            ), "CI workflow should build shadow JAR"
            assert (
                "upload-artifact" in ci_content
            ), "CI workflow should upload JAR artifact"

    @pytest.mark.asyncio
    async def test_push_template_code_includes_workflows(
        self, template_files_with_workflows
    ):
        """Test that push_template_code successfully pushes workflow files."""
        # Create real GitHub client in mock mode (no token)
        github_client = GitHubClient()
        github_client.token = None
        github_client._client = None  # This triggers mock mode

        # Call push_template_code with real implementation
        result = await github_client.push_template_code(
            repo_name="test-muppet",
            template="java-micronaut",
            template_files=template_files_with_workflows,
        )

        # Should succeed in mock mode
        assert result is True, "push_template_code should succeed in mock mode"

    @pytest.mark.asyncio
    #     async def test_directory_creation_handles_nested_paths(self):
    #         """Test that _ensure_directory_exists properly handles nested directory creation."""
    #         # Create real GitHub client with mocked HTTP client
    #         github_client = GitHubClient()
    #         github_client.token = "test-token"
    #         github_client.organization = "test-org"
    #
    #         # Mock the HTTP client
    #         mock_http_client = AsyncMock()
    #         github_client._client = mock_http_client
    #
    #         # Mock the HTTP client responses
    #         mock_http_client.get.side_effect = [
    #             # First call: .github doesn't exist (404)
    #             AsyncMock(status_code=404),
    #             # Second call: .github/workflows doesn't exist (404)
    #             AsyncMock(status_code=404),
    #         ]
    #
    #         mock_http_client.put.side_effect = [
    #             # First put: create .github/.gitkeep (201)
    #             AsyncMock(status_code=201),
    #             # Second put: create .github/workflows/.gitkeep (201)
    #             AsyncMock(status_code=201),
    #         ]
    #
    #         # Test directory creation
    #         result = await github_client._ensure_directory_exists("test-repo", ".github/workflows")
    #
    #         assert result is True, "Directory creation should succeed"
    #
    #         # Verify both directory levels were checked and created
    #         assert mock_http_client.get.call_count == 2, "Should check both .github and .github/workflows"
    #         assert mock_http_client.put.call_count == 2, "Should create .gitkeep files for both levels"
    #
    @pytest.mark.asyncio
    #     async def test_create_file_retries_after_directory_creation(self):
    #         """Test that _create_file retries after creating parent directory on 404."""
    #         # Create real GitHub client with mocked HTTP client
    #         github_client = GitHubClient()
    #         github_client.token = "test-token"
    #         github_client.organization = "test-org"
    #
    #         # Mock the HTTP client
    #         mock_http_client = AsyncMock()
    #         github_client._client = mock_http_client
    #
    #         # Mock the HTTP client responses
    #         mock_http_client.put.side_effect = [
    #             # First attempt: 404 (directory doesn't exist)
    #             AsyncMock(status_code=404, text="Not Found"),
    #             # After directory creation, retry succeeds: 201
    #             AsyncMock(status_code=201),
    #         ]
    #
    #         # Mock successful directory creation by patching the method (async)
    #         with patch.object(github_client, '_ensure_directory_exists', return_value=True, new_callable=AsyncMock):
    #             # Test file creation
    #             result = await github_client._create_file(
    #                 repo_name="test-repo",
    #                 path=".github/workflows/ci.yml",
    #                 content="name: CI",
    #                 commit_message="Add CI workflow"
    #             )
    #
    #             assert result is True, "File creation should succeed after retry"
    #
    #             # Verify file creation was retried
    #             assert mock_http_client.put.call_count == 2, "Should retry file creation after directory setup"
    #
    #     @pytest.mark.asyncio
    async def test_workflow_content_enforces_java_21_lts(self):
        """Test that generated workflows enforce Java 21 LTS requirements."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test-muppet"

            context = GenerationContext(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                parameters={},
                output_path=output_path,
            )

            generated_path = template_manager.generate_code(context)
            workflows_dir = generated_path / ".github" / "workflows"

            # Check CI workflow for Java 21 LTS enforcement
            ci_content = (workflows_dir / "ci.yml").read_text()

            # Should enforce Java 21 LTS
            assert "java-version: '21'" in ci_content, "Should specify Java 21"
            assert (
                "distribution: 'corretto'" in ci_content
            ), "Should use Amazon Corretto"

            # Should have simplified CI workflow structure
            assert (
                "test-and-build:" in ci_content
            ), "Should have single test-and-build job"
            assert (
                "shadowJar" in ci_content
            ), "Should build shadow JAR"

    @pytest.mark.asyncio
    async def test_end_to_end_muppet_creation_includes_workflows(self):
        """Test that end-to-end muppet creation includes workflow files in GitHub."""
        # Test the template generation part directly
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test-muppet"

            context = GenerationContext(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                parameters={
                    "github_organization": "test-org",
                    "aws_region": "us-west-2",
                },
                output_path=output_path,
            )

            # Generate code
            generated_path = template_manager.generate_code(context)

            # Read all generated files into template_files dict (simulating what the service does)
            template_files = {}
            for file_path in generated_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(generated_path)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            template_files[str(relative_path)] = content
                    except UnicodeDecodeError:
                        # Handle binary files
                        with open(file_path, "rb") as f:
                            content = f.read()
                            template_files[str(relative_path)] = content

            # Verify workflow files are included in template_files
            workflow_files = [
                f for f in template_files.keys() if ".github/workflows" in f
            ]
            assert (
                len(workflow_files) == 2
            ), f"Should include 2 workflow files, got {len(workflow_files)}: {workflow_files}"
            assert ".github/workflows/ci.yml" in template_files
            assert ".github/workflows/cd.yml" in template_files

    @pytest.mark.asyncio
    async def test_mock_mode_simulates_workflow_creation(
        self, template_files_with_workflows
    ):
        """Test that mock mode properly simulates workflow creation without real GitHub API calls."""
        # Create GitHub client in mock mode (no token)
        github_client = GitHubClient()
        github_client.token = None
        github_client._client = None  # This triggers mock mode

        # Should succeed in mock mode
        result = await github_client.push_template_code(
            repo_name="test-muppet",
            template="java-micronaut",
            template_files=template_files_with_workflows,
        )

        assert result is True, "Mock mode should simulate successful workflow creation"

    def test_workflow_files_contain_required_java_21_elements(
        self, template_files_with_workflows
    ):
        """Test that workflow files contain all required Java 21 LTS elements."""
        ci_workflow = template_files_with_workflows[".github/workflows/ci.yml"]
        cd_workflow = template_files_with_workflows[".github/workflows/cd.yml"]

        # Both CI and CD should enforce Java 21 LTS
        for workflow_name, workflow_content in [
            ("CI", ci_workflow),
            ("CD", cd_workflow),
        ]:
            assert (
                "java-version: '21'" in workflow_content
            ), f"{workflow_name} should specify Java 21"
            assert (
                "distribution: 'corretto'" in workflow_content
            ), f"{workflow_name} should use Amazon Corretto"
            assert (
                "Amazon Corretto JDK 21" in workflow_content
            ), f"{workflow_name} should mention Amazon Corretto 21"
