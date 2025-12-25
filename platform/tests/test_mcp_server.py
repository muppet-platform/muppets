"""
Tests for MCP server functionality.

This module tests the MCP server foundation, authentication,
and tool registry components.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import CallToolRequest, CallToolRequestParams

from src.platform_mcp.auth import MCPAuthenticator
from src.platform_mcp.server import MCPServer
from src.platform_mcp.tools import MCPToolRegistry


@pytest.fixture(autouse=True)
def enable_debug_mode():
    """Enable debug mode for all tests."""
    with patch.dict(os.environ, {"DEBUG": "true"}):
        # Clear the settings cache to pick up the new environment variable
        from src.config import get_settings

        get_settings.cache_clear()
        yield
        # Clear cache again after test
        get_settings.cache_clear()


class TestMCPServer:
    """Test cases for MCPServer class."""

    @pytest.fixture
    def mcp_server(self):
        """Create an MCP server instance for testing."""
        return MCPServer()

    def test_mcp_server_initialization(self, mcp_server):
        """Test MCP server initializes correctly."""
        assert mcp_server.server is not None
        assert mcp_server.authenticator is not None
        assert mcp_server.tool_registry is not None
        assert mcp_server.settings is not None


class TestMCPAuthenticator:
    """Test cases for MCPAuthenticator class."""

    @pytest.fixture
    def authenticator(self):
        """Create an authenticator instance for testing."""
        return MCPAuthenticator()

    @pytest.mark.asyncio
    async def test_authenticate_with_debug_token(self, authenticator):
        """Test authentication with debug token."""
        # Create a mock request with debug token
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="test_tool", arguments={"_auth_token": "dev-token"}
            )
        )

        # Should authenticate in debug mode
        result = await authenticator.authenticate(request)
        assert result is True

    @pytest.mark.asyncio
    async def test_authenticate_without_token(self, authenticator):
        """Test authentication without token in debug mode."""
        # Create a mock request without token
        request = CallToolRequest(
            params=CallToolRequestParams(name="test_tool", arguments={})
        )

        # Should still authenticate in debug mode
        result = await authenticator.authenticate(request)
        assert result is True  # Debug mode allows requests without tokens

    def test_extract_auth_token_from_arguments(self, authenticator):
        """Test extracting auth token from request arguments."""
        request = CallToolRequest(
            params=CallToolRequestParams(
                name="test_tool", arguments={"_auth_token": "test-token"}
            )
        )

        token = authenticator._extract_auth_token(request)
        assert token == "test-token"

    def test_extract_auth_token_debug_mode(self, authenticator):
        """Test extracting auth token in debug mode."""
        request = CallToolRequest(
            params=CallToolRequestParams(name="test_tool", arguments={})
        )

        token = authenticator._extract_auth_token(request)
        assert token == "dev-token"  # Debug mode returns dev-token

    @pytest.mark.asyncio
    async def test_validate_token_debug(self, authenticator):
        """Test token validation in debug mode."""
        result = await authenticator._validate_token("dev-token")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_token_minimum_length(self, authenticator):
        """Test token validation with minimum length requirement."""
        result = await authenticator._validate_token("12345678")
        assert result is True

        result = await authenticator._validate_token("1234567")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_role_debug(self, authenticator):
        """Test getting user role in debug mode."""
        role = await authenticator._get_user_role("dev-token")
        assert role == "admin"


class TestMCPToolRegistry:
    """Test cases for MCPToolRegistry class."""

    @pytest.fixture
    def mock_lifecycle_service(self):
        """Create a mock lifecycle service for testing."""
        mock_service = AsyncMock()

        # Mock create_muppet response
        mock_service.create_muppet.return_value = {
            "success": True,
            "message": "Muppet 'test-muppet' created successfully",
            "muppet": {
                "name": "test-muppet",
                "template": "java-micronaut",
                "status": "creating",
            },
            "repository": {
                "url": "https://github.com/muppet-platform/test-muppet",
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

        # Mock responses removed for delete_muppet - deletion is now manual

        # Mock get_muppet_status response
        mock_service.get_muppet_status.return_value = {
            "success": True,
            "muppet": {
                "name": "test-muppet",
                "template": "java-micronaut",
                "status": "running",
                "github_repo_url": "https://github.com/muppet-platform/test-muppet",
                "created_at": "2025-12-23T06:00:00Z",
                "deployed": True,
                "health": "healthy",
                "desired_tasks": 1,
                "running_tasks": 1,
            },
        }

        # Mock list_all_muppets response
        mock_service.list_all_muppets.return_value = {
            "muppets": [],  # Add the missing muppets key
            "summary": {
                "total_muppets": 1,
                "by_status": {"creating": 1, "running": 0, "error": 0, "deleting": 0},
                "deployed_muppets": 1,
                "healthy_muppets": 0,
            },
            "platform_health": {
                "total_muppets": 1,
                "health_score": 0.0,
                "active_deployments": 0,
            },
            "retrieved_at": "2025-12-23T06:00:00Z",
        }

        # Mock get_muppet_status response
        mock_service.get_muppet_status.return_value = {
            "muppet": {
                "name": "test-muppet",
                "status": "creating",
                "template": "java-micronaut",
                "github_repo_url": "https://github.com/muppet-platform/test-muppet",
                "created_at": "2025-12-23T06:00:00Z",
                "updated_at": "2025-12-23T06:00:00Z",
                "desired_tasks": 0,
                "running_tasks": 0,
            },
            "health": {"status": "unknown", "last_check": "2025-12-23T06:00:00Z"},
            "deployment": {"status": "pending", "service_url": None},
            "infrastructure": {"status": "provisioned", "workspace_exists": True},
            "github": {
                "repository_exists": True,
                "last_commit": "2025-12-23T06:00:00Z",
            },
            "metrics": {
                "cpu_utilization": 0.0,
                "memory_utilization": 0.0,
                "request_count": 0,
                "error_rate": 0.0,
            },
            "retrieved_at": "2025-12-23T06:00:00Z",
        }

        # Mock template manager
        mock_template_manager = MagicMock()

        # Create a mock template object with proper attributes
        mock_template = MagicMock()
        mock_template.name = "java-micronaut"
        mock_template.description = "Java Micronaut microservice template"
        mock_template.language = "java"
        mock_template.framework = "micronaut"
        mock_template.version = "1.0.0"
        mock_template.supported_features = ["health_checks", "metrics"]
        mock_template.port = 3000
        mock_template.terraform_modules = ["fargate-service", "monitoring"]
        mock_template.required_variables = ["muppet_name", "aws_region"]

        mock_template_manager.discover_templates.return_value = [mock_template]
        mock_service.template_manager = mock_template_manager

        return mock_service

    @pytest.fixture
    def mock_state_manager(self):
        """Create a mock state manager for testing."""
        mock_manager = AsyncMock()
        return mock_manager

    @pytest.fixture
    def mock_steering_manager(self):
        """Create a mock steering manager for testing."""
        mock_manager = AsyncMock()

        # Mock steering docs responses
        def mock_list_steering_documents(muppet_name=None):
            base_response = {
                "shared": [
                    {
                        "name": "http-responses",
                        "version": "v1.0.0",
                        "last_updated": "2025-12-23T06:00:00Z",
                        "path": ".kiro/steering/shared/http-responses.md",
                    }
                ],
                "template-specific": [],
                "muppet-specific": [],
            }

            # Add muppet-specific docs if muppet_name is provided
            if muppet_name:
                base_response["muppet-specific"] = [
                    {
                        "name": "README",
                        "version": "v1.0.0",
                        "last_updated": "2025-12-23T06:00:00Z",
                        "path": f".kiro/steering/muppets/{muppet_name}/README.md",
                    }
                ]

            return base_response

        mock_manager.list_steering_documents.side_effect = mock_list_steering_documents

        mock_manager.update_shared_steering_across_muppets.return_value = {
            "test-muppet": True
        }

        # Create mock objects that behave like the expected steering document objects
        mock_doc = MagicMock()
        mock_doc.name = "http-responses"
        mock_doc.version = "v1.0.0"
        mock_doc.last_updated.isoformat.return_value = "2025-12-23T06:00:00Z"

        mock_manager.get_shared_steering_documents.return_value = [mock_doc]

        return mock_manager

    @pytest.fixture
    def tool_registry(
        self, mock_lifecycle_service, mock_state_manager, mock_steering_manager
    ):
        """Create a tool registry instance for testing with mocked dependencies."""
        return MCPToolRegistry(
            steering_manager=mock_steering_manager,
            lifecycle_service=mock_lifecycle_service,
            state_manager=mock_state_manager,
        )

    @pytest.mark.asyncio
    async def test_get_tools(self, tool_registry):
        """Test getting list of available tools."""
        tools = await tool_registry.get_tools()

        # Should have all expected tools
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "create_muppet",
            "list_muppets",
            "list_templates",
            "get_muppet_status",
            "get_muppet_logs",
            "setup_muppet_dev",
            "update_shared_steering",
            "list_steering_docs",
            "update_muppet_pipelines",
            "list_workflow_versions",
            "rollback_muppet_pipelines",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_execute_create_muppet_tool(self, tool_registry):
        """Test executing create_muppet tool."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"name": "test-muppet", "template": "java-micronaut"}
        )

        # Should return JSON response
        import json

        response = json.loads(result)
        assert response["success"] is True
        assert "test-muppet" in response["message"]

    @pytest.mark.asyncio
    async def test_execute_create_muppet_invalid_name(self, tool_registry):
        """Test executing create_muppet tool with invalid name."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"name": "invalid name!", "template": "java-micronaut"}
        )

        # Should return error response
        import json

        response = json.loads(result)
        assert response["success"] is False
        # Pydantic validation error message
        assert "Invalid input" in response["error"]
        assert "validation error" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_create_muppet_invalid_template(self, tool_registry):
        """Test executing create_muppet tool with invalid template."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"name": "test-muppet", "template": "invalid-template"}
        )

        # Should return error response
        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Unknown template" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_list_templates_tool(self, tool_registry):
        """Test executing list_templates tool."""
        result = await tool_registry.execute_tool("list_templates", {})

        # Should return list of templates
        import json

        response = json.loads(result)
        assert "templates" in response
        assert len(response["templates"]) > 0

        # Check for expected templates
        template_names = [t["name"] for t in response["templates"]]
        assert "java-micronaut" in template_names

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, tool_registry):
        """Test executing unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await tool_registry.execute_tool("unknown_tool", {})

    # Comprehensive tests for delete_muppet tool
    @pytest.mark.asyncio
    # delete_muppet tests removed - deletion is now a manual operation for safety
    # Comprehensive tests for list_muppets tool
    @pytest.mark.asyncio
    async def test_execute_list_muppets_valid(self, tool_registry):
        """Test executing list_muppets tool."""
        result = await tool_registry.execute_tool("list_muppets", {})

        import json

        response = json.loads(result)
        assert "muppets" in response
        assert "total" in response
        assert "retrieved_at" in response
        assert isinstance(response["muppets"], list)
        assert isinstance(response["total"], int)

    # Comprehensive tests for get_muppet_status tool
    @pytest.mark.asyncio
    async def test_execute_get_muppet_status_valid(self, tool_registry):
        """Test executing get_muppet_status tool with valid input."""
        result = await tool_registry.execute_tool(
            "get_muppet_status", {"name": "test-muppet"}
        )

        import json

        response = json.loads(result)
        assert "muppet" in response
        assert response["muppet"]["name"] == "test-muppet"
        assert "status" in response["muppet"]
        assert "template" in response["muppet"]
        assert "github_repo" in response["muppet"]
        assert "metrics" in response["muppet"]

    @pytest.mark.asyncio
    async def test_execute_get_muppet_status_invalid_name(self, tool_registry):
        """Test executing get_muppet_status tool with invalid name."""
        result = await tool_registry.execute_tool(
            "get_muppet_status", {"name": "x"}  # Too short
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_get_muppet_status_missing_name(self, tool_registry):
        """Test executing get_muppet_status tool without name parameter."""
        result = await tool_registry.execute_tool("get_muppet_status", {})

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    # Comprehensive tests for get_muppet_logs tool
    @pytest.mark.asyncio
    async def test_execute_get_muppet_logs_valid_default_lines(self, tool_registry):
        """Test executing get_muppet_logs tool with default lines."""
        result = await tool_registry.execute_tool(
            "get_muppet_logs", {"name": "test-muppet"}
        )

        import json

        response = json.loads(result)
        assert response["muppet"] == "test-muppet"
        assert response["lines_requested"] == 100  # Default value
        assert "logs" in response
        assert isinstance(response["logs"], list)

    @pytest.mark.asyncio
    async def test_execute_get_muppet_logs_valid_custom_lines(self, tool_registry):
        """Test executing get_muppet_logs tool with custom lines."""
        result = await tool_registry.execute_tool(
            "get_muppet_logs", {"name": "test-muppet", "lines": 50}
        )

        import json

        response = json.loads(result)
        assert response["muppet"] == "test-muppet"
        assert response["lines_requested"] == 50
        assert "logs" in response

    @pytest.mark.asyncio
    async def test_execute_get_muppet_logs_invalid_lines_too_small(self, tool_registry):
        """Test executing get_muppet_logs tool with lines too small."""
        result = await tool_registry.execute_tool(
            "get_muppet_logs", {"name": "test-muppet", "lines": 0}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_get_muppet_logs_invalid_lines_too_large(self, tool_registry):
        """Test executing get_muppet_logs tool with lines too large."""
        result = await tool_registry.execute_tool(
            "get_muppet_logs", {"name": "test-muppet", "lines": 10001}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_get_muppet_logs_invalid_name(self, tool_registry):
        """Test executing get_muppet_logs tool with invalid name."""
        result = await tool_registry.execute_tool(
            "get_muppet_logs", {"name": "xy", "lines": 100}  # Name too short
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    # Comprehensive tests for setup_muppet_dev tool
    @pytest.mark.asyncio
    async def test_execute_setup_muppet_dev_valid(self, tool_registry):
        """Test executing setup_muppet_dev tool with valid input."""
        result = await tool_registry.execute_tool(
            "setup_muppet_dev", {"name": "test-muppet"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is True
        assert "test-muppet" in response["message"]
        assert "configuration" in response
        assert "next_steps" in response
        assert "kiro_config" in response["configuration"]
        assert "steering_docs" in response["configuration"]
        assert "development_scripts" in response["configuration"]

    @pytest.mark.asyncio
    async def test_execute_setup_muppet_dev_invalid_name(self, tool_registry):
        """Test executing setup_muppet_dev tool with invalid name."""
        result = await tool_registry.execute_tool(
            "setup_muppet_dev", {"name": "x"}  # Too short
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_setup_muppet_dev_missing_name(self, tool_registry):
        """Test executing setup_muppet_dev tool without name parameter."""
        result = await tool_registry.execute_tool("setup_muppet_dev", {})

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    # Comprehensive tests for update_shared_steering tool
    @pytest.mark.asyncio
    async def test_execute_update_shared_steering_valid(self, tool_registry):
        """Test executing update_shared_steering tool."""
        result = await tool_registry.execute_tool("update_shared_steering", {})

        import json

        response = json.loads(result)
        assert response["success"] is True
        assert "updated_muppets" in response
        assert "updated_files" in response
        assert "updated_at" in response
        assert isinstance(response["updated_muppets"], list)
        assert isinstance(response["updated_files"], list)

    # Comprehensive tests for list_steering_docs tool
    @pytest.mark.asyncio
    async def test_execute_list_steering_docs_no_muppet(self, tool_registry):
        """Test executing list_steering_docs tool without muppet name."""
        result = await tool_registry.execute_tool("list_steering_docs", {})

        import json

        response = json.loads(result)
        assert "shared_steering" in response
        assert "muppet_specific" in response
        assert response["muppet_name"] is None
        assert "total_shared" in response
        assert "total_muppet_specific" in response
        assert isinstance(response["shared_steering"], list)
        assert isinstance(response["muppet_specific"], list)
        assert len(response["shared_steering"]) > 0  # Should have shared docs
        assert (
            len(response["muppet_specific"]) == 0
        )  # No muppet-specific docs without muppet name

    @pytest.mark.asyncio
    async def test_execute_list_steering_docs_with_muppet(self, tool_registry):
        """Test executing list_steering_docs tool with muppet name."""
        result = await tool_registry.execute_tool(
            "list_steering_docs", {"muppet_name": "test-muppet"}
        )

        import json

        response = json.loads(result)
        assert "shared_steering" in response
        assert "muppet_specific" in response
        assert response["muppet_name"] == "test-muppet"
        assert len(response["shared_steering"]) > 0  # Should have shared docs
        # Should have muppet-specific docs
        assert len(response["muppet_specific"]) > 0

    @pytest.mark.asyncio
    async def test_execute_list_steering_docs_invalid_muppet_name(self, tool_registry):
        """Test executing list_steering_docs tool with invalid muppet name."""
        result = await tool_registry.execute_tool(
            "list_steering_docs", {"muppet_name": "x"}  # Too short
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    # Additional edge case tests for create_muppet tool
    @pytest.mark.asyncio
    async def test_execute_create_muppet_name_starts_with_hyphen(self, tool_registry):
        """Test executing create_muppet tool with name starting with hyphen."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"name": "-test-muppet", "template": "java-micronaut"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_create_muppet_name_ends_with_underscore(self, tool_registry):
        """Test executing create_muppet tool with name ending with underscore."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"name": "test-muppet_", "template": "java-micronaut"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_create_muppet_name_with_special_chars(self, tool_registry):
        """Test executing create_muppet tool with name containing special characters."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"name": "test@muppet", "template": "java-micronaut"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_create_muppet_missing_template(self, tool_registry):
        """Test executing create_muppet tool without template parameter."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"name": "test-muppet"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_create_muppet_missing_name(self, tool_registry):
        """Test executing create_muppet tool without name parameter."""
        result = await tool_registry.execute_tool(
            "create_muppet", {"template": "java-micronaut"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_create_muppet_all_valid_templates(self, tool_registry):
        """Test executing create_muppet tool with all valid templates."""
        valid_templates = ["java-micronaut"]

        for template in valid_templates:
            result = await tool_registry.execute_tool(
                "create_muppet",
                {"name": f"test-{template.replace('-', '')}", "template": template},
            )

            import json

            response = json.loads(result)
            assert response["success"] is True
            assert template in response["message"]

    # Test response format consistency
    @pytest.mark.asyncio
    async def test_response_format_consistency(self, tool_registry):
        """Test that all tools return consistent JSON response formats."""
        # Test successful responses have consistent structure
        success_tools = [
            ("create_muppet", {"name": "test-muppet", "template": "java-micronaut"}),
            ("list_muppets", {}),
            ("list_templates", {}),
            ("get_muppet_status", {"name": "test-muppet"}),
            ("get_muppet_logs", {"name": "test-muppet"}),
            ("setup_muppet_dev", {"name": "test-muppet"}),
            ("update_shared_steering", {}),
            ("list_steering_docs", {}),
        ]

        for tool_name, args in success_tools:
            result = await tool_registry.execute_tool(tool_name, args)

            # Should be valid JSON
            import json

            response = json.loads(result)

            # Should be a dictionary
            assert isinstance(response, dict)

            # Should have consistent timestamp format if present
            for key in response:
                if key.endswith("_at") and response[key]:
                    # Should be ISO format timestamp
                    assert "T" in response[key]
                    assert "Z" in response[key]

    @pytest.mark.asyncio
    async def test_error_response_format_consistency(self, tool_registry):
        """Test that all tools return consistent error response formats."""
        # Test error responses have consistent structure
        error_tools = [
            (
                "create_muppet",
                {"name": "x", "template": "java-micronaut"},
            ),  # Invalid name
            ("get_muppet_status", {"name": "x"}),  # Invalid name
            ("get_muppet_logs", {"name": "x"}),  # Invalid name
            ("setup_muppet_dev", {"name": "x"}),  # Invalid name
            ("list_steering_docs", {"muppet_name": "x"}),  # Invalid name
        ]

        for tool_name, args in error_tools:
            result = await tool_registry.execute_tool(tool_name, args)

            # Should be valid JSON
            import json

            response = json.loads(result)

            # Should be a dictionary
            assert isinstance(response, dict)

            # Should have success=False and error message
            assert response["success"] is False
            assert "error" in response
            assert isinstance(response["error"], str)
            assert len(response["error"]) > 0

    # Comprehensive tests for pipeline management tools
    @pytest.mark.asyncio
    async def test_execute_update_muppet_pipelines_valid(self, tool_registry):
        """Test executing update_muppet_pipelines tool with valid input."""
        result = await tool_registry.execute_tool(
            "update_muppet_pipelines",
            {"muppet_name": "test-muppet", "workflow_version": "java-micronaut-v1.2.3"},
        )

        import json

        response = json.loads(result)
        assert response["success"] is True
        assert "test-muppet" in response["message"]
        assert response["muppet_name"] == "test-muppet"
        assert response["workflow_version"] == "java-micronaut-v1.2.3"
        assert response["template_type"] == "java-micronaut"
        assert "updated_files" in response
        assert "updated_at" in response

    @pytest.mark.asyncio
    async def test_execute_update_muppet_pipelines_invalid_muppet_name(
        self, tool_registry
    ):
        """Test executing update_muppet_pipelines tool with invalid muppet name."""
        result = await tool_registry.execute_tool(
            "update_muppet_pipelines",
            {"muppet_name": "x", "workflow_version": "java-micronaut-v1.2.3"},
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_update_muppet_pipelines_invalid_workflow_version(
        self, tool_registry
    ):
        """Test executing update_muppet_pipelines tool with invalid workflow version."""
        result = await tool_registry.execute_tool(
            "update_muppet_pipelines",
            {"muppet_name": "test-muppet", "workflow_version": "invalid-version"},
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_update_muppet_pipelines_missing_parameters(
        self, tool_registry
    ):
        """Test executing update_muppet_pipelines tool with missing parameters."""
        # Missing workflow_version
        result = await tool_registry.execute_tool(
            "update_muppet_pipelines", {"muppet_name": "test-muppet"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

        # Missing muppet_name
        result = await tool_registry.execute_tool(
            "update_muppet_pipelines", {"workflow_version": "java-micronaut-v1.2.3"}
        )

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_list_workflow_versions_valid(self, tool_registry):
        """Test executing list_workflow_versions tool with valid input."""
        # Mock the GitHubClient to avoid real API calls
        with patch("src.platform_mcp.tools.GitHubClient") as mock_github_class:
            mock_github = AsyncMock()
            mock_github_class.return_value = mock_github

            # Mock the list_tags method to return test data
            mock_github.list_tags.return_value = [
                {
                    "name": "java-micronaut-v1.2.3",
                    "commit": {"sha": "abc123"},
                    "created_at": "2024-01-15T10:00:00Z",
                },
                {
                    "name": "java-micronaut-v1.2.2",
                    "commit": {"sha": "def456"},
                    "created_at": "2024-01-10T10:00:00Z",
                },
                {
                    "name": "java-micronaut-v1.2.1",
                    "commit": {"sha": "ghi789"},
                    "created_at": "2024-01-05T10:00:00Z",
                },
            ]

            # Mock get_file_content to return workflow manifest
            mock_github.get_file_content.return_value = (
                '{"workflows": {"ci": "v1.0.0"}, "requirements": {"java": "21"}}'
            )

            result = await tool_registry.execute_tool(
                "list_workflow_versions", {"template_type": "java-micronaut"}
            )

        import json

        response = json.loads(result)
        assert response["template_type"] == "java-micronaut"
        assert "versions" in response
        assert "total_versions" in response
        assert "latest_version" in response
        assert "workflows" in response
        assert "requirements" in response
        assert "retrieved_at" in response
        assert isinstance(response["versions"], list)
        assert isinstance(response["total_versions"], int)

        # Should have at least one version in mock data
        assert response["total_versions"] > 0
        assert response["latest_version"] is not None

    @pytest.mark.asyncio
    async def test_execute_list_workflow_versions_invalid_template(self, tool_registry):
        """Test executing list_workflow_versions tool with invalid template type."""
        result = await tool_registry.execute_tool(
            "list_workflow_versions", {"template_type": "invalid-template"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_list_workflow_versions_missing_template(self, tool_registry):
        """Test executing list_workflow_versions tool without template_type parameter."""
        result = await tool_registry.execute_tool("list_workflow_versions", {})

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_rollback_muppet_pipelines_valid(self, tool_registry):
        """Test executing rollback_muppet_pipelines tool with valid input."""
        result = await tool_registry.execute_tool(
            "rollback_muppet_pipelines",
            {"muppet_name": "test-muppet", "workflow_version": "java-micronaut-v1.2.2"},
        )

        import json

        response = json.loads(result)
        assert response["success"] is True
        assert "test-muppet" in response["message"]
        assert response["muppet_name"] == "test-muppet"
        assert response["workflow_version"] == "java-micronaut-v1.2.2"
        assert response["rollback"] is True
        assert "previous_version" in response
        assert "updated_files" in response
        assert "updated_at" in response

    @pytest.mark.asyncio
    async def test_execute_rollback_muppet_pipelines_invalid_muppet_name(
        self, tool_registry
    ):
        """Test executing rollback_muppet_pipelines tool with invalid muppet name."""
        result = await tool_registry.execute_tool(
            "rollback_muppet_pipelines",
            {"muppet_name": "x", "workflow_version": "java-micronaut-v1.2.2"},
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_rollback_muppet_pipelines_invalid_workflow_version(
        self, tool_registry
    ):
        """Test executing rollback_muppet_pipelines tool with invalid workflow version."""
        result = await tool_registry.execute_tool(
            "rollback_muppet_pipelines",
            {"muppet_name": "test-muppet", "workflow_version": "invalid-version"},
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_execute_rollback_muppet_pipelines_missing_parameters(
        self, tool_registry
    ):
        """Test executing rollback_muppet_pipelines tool with missing parameters."""
        # Missing workflow_version
        result = await tool_registry.execute_tool(
            "rollback_muppet_pipelines", {"muppet_name": "test-muppet"}
        )

        import json

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

        # Missing muppet_name
        result = await tool_registry.execute_tool(
            "rollback_muppet_pipelines", {"workflow_version": "java-micronaut-v1.2.2"}
        )

        response = json.loads(result)
        assert response["success"] is False
        assert "Invalid input" in response["error"]

    @pytest.mark.asyncio
    async def test_pipeline_tools_workflow_version_format_validation(
        self, tool_registry
    ):
        """Test that pipeline tools validate workflow version format correctly."""
        invalid_versions = [
            "v1.2.3",  # Missing template prefix
            "java-micronaut-1.2.3",  # Missing 'v' prefix
            "java-micronaut-v1.2",  # Missing patch version
            "java-micronaut-v1",  # Missing minor and patch versions
            "java-micronaut-va.b.c",  # Non-numeric version
            "",  # Empty string
            "java-micronaut-v1.2.3.4",  # Too many version parts
        ]

        for invalid_version in invalid_versions:
            # Test update_muppet_pipelines
            result = await tool_registry.execute_tool(
                "update_muppet_pipelines",
                {"muppet_name": "test-muppet", "workflow_version": invalid_version},
            )

            import json

            response = json.loads(result)
            assert (
                response["success"] is False
            ), f"Should reject invalid version: {invalid_version}"

            # Test rollback_muppet_pipelines
            result = await tool_registry.execute_tool(
                "rollback_muppet_pipelines",
                {"muppet_name": "test-muppet", "workflow_version": invalid_version},
            )

            response = json.loads(result)
            assert (
                response["success"] is False
            ), f"Should reject invalid version: {invalid_version}"

    @pytest.mark.asyncio
    async def test_pipeline_tools_valid_workflow_versions(self, tool_registry):
        """Test that pipeline tools accept valid workflow version formats."""
        valid_versions = [
            "java-micronaut-v1.0.0",
            "java-micronaut-v1.2.3",
            "java-micronaut-v10.20.30",
            "python-fastapi-v2.1.0",  # Different template type
            "go-gin-v3.4.5",  # Another template type
        ]

        for valid_version in valid_versions:
            # Test update_muppet_pipelines
            result = await tool_registry.execute_tool(
                "update_muppet_pipelines",
                {"muppet_name": "test-muppet", "workflow_version": valid_version},
            )

            import json

            response = json.loads(result)
            # Should not fail due to version format validation
            if response["success"] is False:
                assert (
                    "Invalid input" not in response["error"]
                ), f"Should accept valid version: {valid_version}"

    @pytest.mark.asyncio
    async def test_pipeline_tools_response_format_consistency(self, tool_registry):
        """Test that pipeline management tools return consistent response formats."""
        # Test update_muppet_pipelines response format
        result = await tool_registry.execute_tool(
            "update_muppet_pipelines",
            {"muppet_name": "test-muppet", "workflow_version": "java-micronaut-v1.2.3"},
        )

        import json

        response = json.loads(result)

        # Check required fields
        required_fields = [
            "success",
            "message",
            "muppet_name",
            "workflow_version",
            "template_type",
            "updated_files",
            "updated_at",
        ]
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

        # Check data types
        assert isinstance(response["success"], bool)
        assert isinstance(response["message"], str)
        assert isinstance(response["muppet_name"], str)
        assert isinstance(response["workflow_version"], str)
        assert isinstance(response["template_type"], str)
        assert isinstance(response["updated_files"], list)
        assert isinstance(response["updated_at"], str)

        # Test list_workflow_versions response format
        result = await tool_registry.execute_tool(
            "list_workflow_versions", {"template_type": "java-micronaut"}
        )

        response = json.loads(result)

        # Check required fields
        required_fields = [
            "template_type",
            "versions",
            "total_versions",
            "latest_version",
            "workflows",
            "requirements",
            "retrieved_at",
        ]
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

        # Check data types
        assert isinstance(response["template_type"], str)
        assert isinstance(response["versions"], list)
        assert isinstance(response["total_versions"], int)
        assert isinstance(response["workflows"], dict)
        assert isinstance(response["requirements"], dict)
        assert isinstance(response["retrieved_at"], str)

        # Test rollback_muppet_pipelines response format
        result = await tool_registry.execute_tool(
            "rollback_muppet_pipelines",
            {"muppet_name": "test-muppet", "workflow_version": "java-micronaut-v1.2.2"},
        )

        response = json.loads(result)

        # Check required fields (should have all update fields plus rollback-specific ones)
        required_fields = [
            "success",
            "message",
            "muppet_name",
            "workflow_version",
            "rollback",
            "previous_version",
            "updated_files",
            "updated_at",
        ]
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

        # Check rollback-specific fields
        assert isinstance(response["rollback"], bool)
        assert response["rollback"] is True
        assert isinstance(response["previous_version"], str)
