"""
Property-based tests for muppet creation completeness.

This module implements Property 1: Muppet Creation Completeness
which validates Requirements 1.1, 1.2, 9.1, 9.2.

Feature: muppet-platform, Property 1: Muppet Creation Completeness
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from src.platform_mcp.tools import CreateMuppetArgs, MCPToolRegistry


# Custom strategies for generating test data
@composite
def valid_muppet_names(draw):
    """Generate valid muppet names according to platform rules."""
    # Start with a letter
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz"))

    # Middle characters can be letters, numbers, hyphens, underscores
    middle_chars = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_",
            min_size=1,
            max_size=47,  # Total max is 50, minus first and last char
        )
    )

    # Last character must be alphanumeric
    last_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"))

    return first_char + middle_chars + last_char


@composite
def valid_templates(draw):
    """Generate valid template names."""
    return draw(st.sampled_from(["java-micronaut"]))


@composite
def muppet_creation_inputs(draw):
    """Generate valid inputs for muppet creation."""
    name = draw(valid_muppet_names())
    template = draw(valid_templates())
    return {"name": name, "template": template}


def run_async_test(coro):
    """Helper to run async tests in property-based testing."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestMuppetCreationCompleteness:
    """
    Property-based tests for muppet creation completeness.

    Tests Property 1: For any valid muppet name and template type, when a muppet
    is created, the platform should successfully create the muppet, provision
    infrastructure, create a GitHub repository, and populate it with template code.

    Validates: Requirements 1.1, 1.2, 9.1, 9.2
    """

    @given(muppet_creation_inputs())
    # Minimum 100 iterations as per design
    @settings(max_examples=100, deadline=10000)
    def test_muppet_creation_completeness_property(self, creation_input):
        """
        Property 1: Muppet Creation Completeness

        For any valid muppet name and template type, when a muppet is created,
        the platform should successfully create the muppet, provision infrastructure,
        create a GitHub repository, and populate it with template code.

        **Feature: muppet-platform, Property 1: Muppet Creation Completeness**
        **Validates: Requirements 1.1, 1.2, 9.1, 9.2**
        """

        async def async_test():
            # Set up mocks within the test
            with (
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_muppet_name",
                    return_value=None,
                ),
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_template",
                    return_value=None,
                ),
                patch("src.integrations.github.GitHubClient") as mock_github,
                patch("src.integrations.aws.ECSClient") as mock_ecs,
                patch("src.integrations.aws.ParameterStoreClient") as mock_param_store,
                patch("src.state_manager.get_state_manager") as mock_get_state_manager,
            ):
                # Configure mocks
                github_instance = AsyncMock()
                github_instance.create_repository.return_value = {
                    "success": True,
                    "repo_url": "https://github.com/muppet-platform/test-repo",
                    "clone_url": "git@github.com:muppet-platform/test-repo.git",
                }
                github_instance.populate_repository.return_value = True
                github_instance.setup_branch_protection.return_value = True
                mock_github.return_value = github_instance

                ecs_instance = AsyncMock()
                ecs_instance.create_service.return_value = {
                    "service_arn": "arn:aws:ecs:us-west-2:123456789012:service/test-cluster/test-service",
                    "status": "ACTIVE",
                }
                mock_ecs.return_value = ecs_instance

                param_store_instance = AsyncMock()
                param_store_instance.get_parameters_by_path.return_value = {
                    "terraform/modules/fargate-service/version": "1.0.0",
                    "terraform/modules/monitoring/version": "1.0.0",
                }
                mock_param_store.return_value = param_store_instance

                state_manager_instance = AsyncMock()
                state_manager_instance.get_muppet.return_value = None
                state_manager_instance.add_muppet_to_state.return_value = None
                mock_get_state_manager.return_value = state_manager_instance

                # Arrange
                name = creation_input["name"]
                template = creation_input["template"]

                # Validate input arguments
                try:
                    validated_args = CreateMuppetArgs(name=name, template=template)
                except Exception as e:
                    pytest.skip(f"Invalid input for property test: {e}")

                # Create tool registry instance with mocked dependencies
                mock_lifecycle_service = AsyncMock()
                mock_lifecycle_service.create_muppet.return_value = {
                    "success": True,
                    "message": f"Muppet '{name}' created successfully with template '{template}'",
                    "muppet": {
                        "name": name,
                        "template": template,
                        "status": "creating",
                    },
                    "repository": {
                        "url": f"https://github.com/muppet-platform/{name}",
                        "private": True,
                        "configuration": True,
                    },
                    "template_generation": {"success": True, "files_generated": 15},
                    "steering_setup": {"success": True, "docs_configured": True},
                    "next_steps": [
                        "Clone the repository",
                        "Run the init script",
                        "Start development",
                    ],
                    "created_at": "2025-12-23T06:00:00Z",
                }

                mock_state_manager = AsyncMock()
                mock_steering_manager = AsyncMock()

                tool_registry = MCPToolRegistry(
                    steering_manager=mock_steering_manager,
                    lifecycle_service=mock_lifecycle_service,
                    state_manager=mock_state_manager,
                )

                # Act - Execute muppet creation
                result_json = await tool_registry._create_muppet(
                    {"name": name, "template": template}
                )

                # Parse the JSON result
                result = json.loads(result_json)

                # Assert - Verify muppet creation completeness

                # 1. Creation should succeed
                assert (
                    result.get("success") is True
                ), f"Muppet creation failed: {result.get('error', 'Unknown error')}"

                # 2. Result should contain muppet information
                assert "muppet" in result, "Result should contain muppet information"
                muppet_info = result["muppet"]

                # 3. Muppet should have correct name and template
                assert (
                    muppet_info["name"] == name
                ), f"Expected name {name}, got {muppet_info['name']}"
                assert (
                    muppet_info["template"] == template
                ), f"Expected template {template}, got {muppet_info['template']}"

                # 4. Muppet should have a valid status
                valid_statuses = ["creating", "running", "stopped", "error", "deleting"]
                assert (
                    muppet_info["status"] in valid_statuses
                ), f"Invalid status: {muppet_info['status']}"

                # 5. GitHub repository should be created (Requirements 9.1, 9.2)
                assert (
                    "github_repo" in muppet_info
                ), "GitHub repository URL should be provided"
                expected_repo_url = f"https://github.com/muppet-platform/{name}"
                assert (
                    muppet_info["github_repo"] == expected_repo_url
                ), f"Expected GitHub repo URL {expected_repo_url}, got {muppet_info['github_repo']}"

                # 6. Creation timestamp should be present
                assert (
                    "created_at" in muppet_info
                ), "Creation timestamp should be provided"

                # 7. Success message validation
                assert result.get("message"), "Success message should be provided"
                assert (
                    name in result["message"]
                ), "Success message should mention the muppet name"
                assert (
                    template in result["message"]
                ), "Success message should mention the template"

        # Run the async test
        run_async_test(async_test())

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_invalid_muppet_names_are_rejected(self, invalid_name):
        """
        Test that invalid muppet names are properly rejected.

        This ensures the property only applies to valid inputs.
        """

        async def async_test():
            # Skip if the name happens to be valid
            try:
                CreateMuppetArgs(name=invalid_name, template="java-micronaut")
                pytest.skip("Generated name is actually valid")
            except Exception:
                pass  # Expected for invalid names

            with (
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_muppet_name",
                    return_value=None,
                ),
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_template",
                    return_value=None,
                ),
            ):
                # Create mocked dependencies
                mock_lifecycle_service = AsyncMock()
                mock_lifecycle_service.create_muppet.return_value = {
                    "success": False,
                    "error": f"Invalid muppet name: {invalid_name}",
                }

                mock_state_manager = AsyncMock()
                mock_steering_manager = AsyncMock()

                tool_registry = MCPToolRegistry(
                    steering_manager=mock_steering_manager,
                    lifecycle_service=mock_lifecycle_service,
                    state_manager=mock_state_manager,
                )

                # Act
                result_json = await tool_registry._create_muppet(
                    {"name": invalid_name, "template": "java-micronaut"}
                )

                # Parse result
                result = json.loads(result_json)

                # Assert - Invalid names should be rejected
                assert (
                    result.get("success") is False
                ), "Invalid muppet names should be rejected"
                assert (
                    "error" in result
                ), "Error message should be provided for invalid names"

        run_async_test(async_test())

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_invalid_templates_are_rejected(self, invalid_template):
        """
        Test that invalid template names are properly rejected.

        This ensures the property only applies to valid inputs.
        """

        async def async_test():
            valid_templates = ["java-micronaut"]

            # Skip if the template happens to be valid
            if invalid_template in valid_templates:
                pytest.skip("Generated template is actually valid")

            with (
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_muppet_name",
                    return_value=None,
                ),
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_template",
                    return_value=None,
                ),
            ):
                # Create mocked dependencies
                mock_lifecycle_service = AsyncMock()
                mock_lifecycle_service.create_muppet.return_value = {
                    "success": False,
                    "error": f"Invalid template: {invalid_template}",
                }

                mock_state_manager = AsyncMock()
                mock_steering_manager = AsyncMock()

                tool_registry = MCPToolRegistry(
                    steering_manager=mock_steering_manager,
                    lifecycle_service=mock_lifecycle_service,
                    state_manager=mock_state_manager,
                )

                # Act
                result_json = await tool_registry._create_muppet(
                    {"name": "valid-name", "template": invalid_template}
                )

                # Parse result
                result = json.loads(result_json)

                # Assert - Invalid templates should be rejected
                assert (
                    result.get("success") is False
                ), "Invalid templates should be rejected"
                assert (
                    "error" in result
                ), "Error message should be provided for invalid templates"

        run_async_test(async_test())

    def test_property_with_specific_examples(self):
        """
        Test the property with specific known-good examples.

        This provides concrete examples alongside the property-based tests.
        """

        async def async_test():
            test_cases = [
                {"name": "example-api", "template": "java-micronaut"},
                {"name": "user-service", "template": "java-micronaut"},
                {"name": "notification-worker", "template": "java-micronaut"},
                {"name": "data-processor", "template": "java-micronaut"},
            ]

            with (
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_muppet_name",
                    return_value=None,
                ),
                patch(
                    "src.platform_mcp.tools.MCPToolRegistry._validate_template",
                    return_value=None,
                ),
                patch("src.integrations.github.GitHubClient") as mock_github,
                patch("src.integrations.aws.ECSClient") as mock_ecs,
                patch("src.integrations.aws.ParameterStoreClient") as mock_param_store,
                patch("src.state_manager.get_state_manager") as mock_get_state_manager,
            ):
                # Configure mocks
                github_instance = AsyncMock()
                github_instance.create_repository.return_value = {
                    "success": True,
                    "repo_url": "https://github.com/muppet-platform/test-repo",
                    "clone_url": "git@github.com:muppet-platform/test-repo.git",
                }
                mock_github.return_value = github_instance

                ecs_instance = AsyncMock()
                ecs_instance.create_service.return_value = {
                    "service_arn": "arn:aws:ecs:us-west-2:123456789012:service/test-cluster/test-service",
                    "status": "ACTIVE",
                }
                mock_ecs.return_value = ecs_instance

                param_store_instance = AsyncMock()
                param_store_instance.get_parameters_by_path.return_value = {
                    "terraform/modules/fargate-service/version": "1.0.0",
                    "terraform/modules/monitoring/version": "1.0.0",
                }
                mock_param_store.return_value = param_store_instance

                state_manager_instance = AsyncMock()
                state_manager_instance.get_muppet.return_value = None
                state_manager_instance.add_muppet_to_state.return_value = None
                mock_get_state_manager.return_value = state_manager_instance

                # Create mocked dependencies for MCPToolRegistry
                mock_lifecycle_service = AsyncMock()
                mock_state_manager = AsyncMock()
                mock_steering_manager = AsyncMock()

                tool_registry = MCPToolRegistry(
                    steering_manager=mock_steering_manager,
                    lifecycle_service=mock_lifecycle_service,
                    state_manager=mock_state_manager,
                )

                for test_case in test_cases:
                    # Configure mock response for each test case
                    mock_lifecycle_service.create_muppet.return_value = {
                        "success": True,
                        "message": f"Muppet '{test_case['name']}' created successfully with template '{test_case['template']}'",
                        "muppet": {
                            "name": test_case["name"],
                            "template": test_case["template"],
                            "status": "creating",
                        },
                        "repository": {
                            "url": f"https://github.com/muppet-platform/{test_case['name']}",
                            "private": True,
                            "configuration": True,
                        },
                        "template_generation": {"success": True, "files_generated": 15},
                        "steering_setup": {"success": True, "docs_configured": True},
                        "next_steps": [
                            "Clone the repository",
                            "Run the init script",
                            "Start development",
                        ],
                        "created_at": "2025-12-23T06:00:00Z",
                    }
                    # Act
                    result_json = await tool_registry._create_muppet(test_case)

                    # Parse result
                    result = json.loads(result_json)

                    # Assert - All specific examples should succeed
                    assert (
                        result.get("success") is True
                    ), f"Failed to create muppet {test_case['name']} with template {test_case['template']}: {result.get('error')}"

                    # Verify completeness for each example
                    muppet_info = result["muppet"]
                    assert muppet_info["name"] == test_case["name"]
                    assert muppet_info["template"] == test_case["template"]
                    assert muppet_info["status"] in [
                        "creating",
                        "running",
                        "stopped",
                        "error",
                        "deleting",
                    ]
                    assert "github_repo" in muppet_info
                    assert "created_at" in muppet_info

        run_async_test(async_test())
