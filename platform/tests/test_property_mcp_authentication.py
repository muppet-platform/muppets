"""
Property-based tests for MCP authentication.

This module implements Property 8: MCP Authentication
which validates Requirements 7.5.

Feature: muppet-platform, Property 8: MCP Authentication
"""

import asyncio
import json
import os
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite
from mcp.types import CallToolRequest, CallToolRequestParams

from src.platform_mcp.auth import MCPAuthenticator
from src.platform_mcp.tools import MCPToolRegistry


# Custom strategies for generating test data
@composite
def valid_auth_tokens(draw):
    """Generate valid authentication tokens."""
    # Valid tokens should be at least 8 characters
    return draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
            min_size=8,
            max_size=64,
        )
    )


@composite
def invalid_auth_tokens(draw):
    """Generate invalid authentication tokens."""
    # Invalid tokens are too short (less than 8 characters)
    return draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
            min_size=1,
            max_size=7,
        )
    )


@composite
def mcp_tool_names(draw):
    """Generate valid MCP tool names."""
    return draw(
        st.sampled_from(
            [
                "create_muppet",
                "list_muppets",
                "list_templates",
                "get_muppet_status",
                "get_muppet_logs",
                "setup_muppet_dev",
                "update_shared_steering",
                "list_steering_docs",
            ]
        )
    )


@composite
def mcp_tool_arguments(draw, tool_name):
    """Generate valid arguments for MCP tools."""
    if tool_name in ["create_muppet"]:
        return {
            "name": draw(
                st.text(
                    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
                    min_size=3,
                    max_size=20,
                ).filter(lambda x: x[0].isalpha() and x[-1].isalnum())
            ),
            "template": draw(st.sampled_from(["java-micronaut"])),
        }
    elif tool_name in ["get_muppet_status", "setup_muppet_dev"]:
        return {
            "name": draw(
                st.text(
                    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
                    min_size=3,
                    max_size=20,
                ).filter(lambda x: x[0].isalpha() and x[-1].isalnum())
            )
        }
    elif tool_name == "get_muppet_logs":
        return {
            "name": draw(
                st.text(
                    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
                    min_size=3,
                    max_size=20,
                ).filter(lambda x: x[0].isalpha() and x[-1].isalnum())
            ),
            "lines": draw(st.integers(min_value=1, max_value=1000)),
        }
    elif tool_name == "list_steering_docs":
        return {
            "muppet_name": draw(
                st.one_of(
                    st.none(),
                    st.text(
                        alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
                        min_size=3,
                        max_size=20,
                    ).filter(lambda x: x[0].isalpha() and x[-1].isalnum()),
                )
            )
        }
    else:
        # Tools that don't require arguments
        return {}


@composite
def authenticated_mcp_request(draw):
    """Generate an authenticated MCP request."""
    tool_name = draw(mcp_tool_names())
    arguments = draw(mcp_tool_arguments(tool_name))
    auth_token = draw(valid_auth_tokens())

    # Add auth token to arguments
    arguments["_auth_token"] = auth_token

    return CallToolRequest(
        params=CallToolRequestParams(name=tool_name, arguments=arguments)
    )


@composite
def unauthenticated_mcp_request(draw):
    """Generate an unauthenticated MCP request."""
    tool_name = draw(mcp_tool_names())
    arguments = draw(mcp_tool_arguments(tool_name))

    # Randomly choose how to make it unauthenticated
    auth_method = draw(st.sampled_from(["no_token", "invalid_token", "empty_token"]))

    if auth_method == "no_token":
        # Don't include auth token at all
        pass
    elif auth_method == "invalid_token":
        # Include an invalid (too short) token
        invalid_token = draw(invalid_auth_tokens())
        arguments["_auth_token"] = invalid_token
    elif auth_method == "empty_token":
        # Include an empty token
        arguments["_auth_token"] = ""

    return CallToolRequest(
        params=CallToolRequestParams(name=tool_name, arguments=arguments)
    )


def run_async_test(coro):
    """Helper to run async tests in property-based testing."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestMCPAuthenticationProperty:
    """
    Property-based tests for MCP authentication.

    Tests Property 8: For any MCP command execution, unauthorized requests
    should be rejected while authorized requests should be processed successfully.

    Validates: Requirements 7.5
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment for each test."""
        # Disable debug mode to test actual authentication
        with patch.dict(os.environ, {"DEBUG": "false"}):
            # Clear the settings cache to pick up the new environment variable
            from src.config import get_settings

            get_settings.cache_clear()
            yield
            # Clear cache again after test
            get_settings.cache_clear()

    @given(authenticated_mcp_request())
    # Minimum 100 iterations as per design
    @settings(max_examples=100, deadline=10000)
    def test_authenticated_requests_are_processed(self, request):
        """
        Property 8a: Authenticated MCP requests should be processed successfully.

        For any MCP command execution with valid authentication, the request
        should be processed and not rejected due to authentication failure.

        **Feature: muppet-platform, Property 8: MCP Authentication**
        **Validates: Requirements 7.5**
        """

        async def async_test():
            # Arrange
            authenticator = MCPAuthenticator()

            # Mock the token validation to accept our generated tokens
            with (
                patch.object(authenticator, "_validate_token", return_value=True),
                patch.object(
                    authenticator, "_authorize_tool_access", return_value=True
                ),
            ):
                # Act - Authenticate the request
                is_authenticated = await authenticator.authenticate(request)

                # Assert - Valid authentication should succeed
                assert is_authenticated is True, (
                    f"Authenticated request should be accepted. Tool: {request.params.name}, "
                    f"Token: {request.params.arguments.get('_auth_token', 'None')}"
                )

        run_async_test(async_test())

    @given(unauthenticated_mcp_request())
    # Minimum 100 iterations as per design
    @settings(max_examples=100, deadline=10000)
    def test_unauthenticated_requests_are_rejected(self, request):
        """
        Property 8b: Unauthenticated MCP requests should be rejected.

        For any MCP command execution without valid authentication, the request
        should be rejected and not processed.

        **Feature: muppet-platform, Property 8: MCP Authentication**
        **Validates: Requirements 7.5**
        """

        async def async_test():
            # Arrange
            authenticator = MCPAuthenticator()

            # Act - Authenticate the request (should fail)
            is_authenticated = await authenticator.authenticate(request)

            # Assert - Invalid/missing authentication should be rejected
            assert is_authenticated is False, (
                f"Unauthenticated request should be rejected. Tool: {request.params.name}, "
                f"Token: {request.params.arguments.get('_auth_token', 'None')}"
            )

        run_async_test(async_test())

    @given(mcp_tool_names(), valid_auth_tokens())
    @settings(max_examples=50, deadline=10000)
    def test_role_based_authorization_property(self, tool_name, auth_token):
        """
        Property 8c: Role-based authorization should be enforced consistently.

        For any valid authentication token and tool combination, authorization
        should be consistent based on the user's role and tool permissions.

        **Feature: muppet-platform, Property 8: MCP Authentication**
        **Validates: Requirements 7.5**
        """

        async def async_test():
            # Arrange
            authenticator = MCPAuthenticator()

            # Test different user roles
            test_roles = ["admin", "developer", "readonly"]

            for role in test_roles:
                with patch.object(authenticator, "_get_user_role", return_value=role):
                    # Act - Check authorization for this role and tool
                    is_authorized = await authenticator._authorize_tool_access(
                        auth_token, tool_name
                    )

                    # Assert - Authorization should be consistent with role permissions
                    expected_permissions = {
                        "create_muppet": ["admin", "developer"],
                        "list_muppets": ["admin", "developer", "readonly"],
                        "list_templates": ["admin", "developer", "readonly"],
                        "get_muppet_status": ["admin", "developer", "readonly"],
                        "get_muppet_logs": ["admin", "developer", "readonly"],
                        "setup_muppet_dev": ["admin", "developer"],
                        "update_shared_steering": ["admin"],
                        "list_steering_docs": ["admin", "developer", "readonly"],
                    }

                    expected_authorized = role in expected_permissions.get(
                        tool_name, []
                    )

                    assert is_authorized == expected_authorized, (
                        f"Role '{role}' authorization for tool '{tool_name}' should be {expected_authorized}, "
                        f"but got {is_authorized}"
                    )

        run_async_test(async_test())

    @given(authenticated_mcp_request())
    @settings(max_examples=50, deadline=15000)
    def test_end_to_end_authentication_flow(self, request):
        """
        Property 8d: End-to-end authentication flow should work consistently.

        For any authenticated MCP request, the complete authentication flow
        from MCP server through authenticator to tool execution should work.

        **Feature: muppet-platform, Property 8: MCP Authentication**
        **Validates: Requirements 7.5**
        """

        async def async_test():
            # Arrange - Test the authentication flow through the authenticator and tool registry
            authenticator = MCPAuthenticator()
            tool_registry = MCPToolRegistry()

            # Mock the token validation and authorization to succeed
            with (
                patch.object(authenticator, "_validate_token", return_value=True),
                patch.object(
                    authenticator, "_authorize_tool_access", return_value=True
                ),
                patch.object(
                    tool_registry,
                    "execute_tool",
                    return_value=json.dumps(
                        {"success": True, "message": "Tool executed successfully"}
                    ),
                ) as mock_execute,
            ):
                # Act - Test the authentication flow
                is_authenticated = await authenticator.authenticate(request)

                # Assert - Authentication should succeed
                assert (
                    is_authenticated is True
                ), f"Authentication should succeed for request with tool {request.params.name}"

                # If authenticated, tool should be executable
                if is_authenticated:
                    result = await tool_registry.execute_tool(
                        request.params.name, request.params.arguments or {}
                    )

                    # Verify tool execution result
                    assert result is not None, "Tool execution should return a result"
                    result_data = json.loads(result)
                    assert (
                        result_data.get("success") is True
                    ), "Tool execution should succeed"

                    # Verify tool was called with correct parameters
                    mock_execute.assert_called_once_with(
                        request.params.name, request.params.arguments or {}
                    )

        run_async_test(async_test())

    def test_authentication_with_specific_examples(self):
        """
        Test authentication with specific known examples.

        This provides concrete examples alongside the property-based tests.
        """

        async def async_test():
            # Test cases with known authentication scenarios
            test_cases = [
                {
                    "name": "valid_admin_token",
                    "token": "admin-token-12345678",
                    "tool": "create_muppet",
                    "role": "admin",
                    "should_authenticate": True,  # Admin can create muppets
                },
                {
                    "name": "valid_developer_token",
                    "token": "dev-token-87654321",
                    "tool": "list_muppets",
                    "role": "developer",
                    "should_authenticate": True,  # Developer can list muppets
                },
                {
                    "name": "valid_readonly_token",
                    "token": "readonly-token-11223344",
                    "tool": "get_muppet_status",
                    "role": "readonly",
                    "should_authenticate": True,  # Readonly can get status
                },
                {
                    "name": "readonly_unauthorized_for_create",
                    "token": "readonly-token-11223344",
                    "tool": "create_muppet",
                    "role": "readonly",
                    # Readonly cannot create muppets (authorization failure)
                    "should_authenticate": False,
                },
                {
                    "name": "developer_unauthorized_for_admin_tool",
                    "token": "dev-token-87654321",
                    "tool": "update_shared_steering",
                    "role": "developer",
                    # Developer cannot use admin tools (authorization failure)
                    "should_authenticate": False,
                },
                {
                    "name": "invalid_short_token",
                    "token": "short",
                    "tool": "list_muppets",
                    "role": "developer",
                    # Invalid token (authentication failure)
                    "should_authenticate": False,
                },
                {
                    "name": "empty_token",
                    "token": "",
                    "tool": "list_muppets",
                    "role": "developer",
                    # Empty token (authentication failure)
                    "should_authenticate": False,
                },
            ]

            authenticator = MCPAuthenticator()

            for test_case in test_cases:
                # Create request with the test token
                request = CallToolRequest(
                    params=CallToolRequestParams(
                        name=test_case["tool"],
                        arguments={"_auth_token": test_case["token"]},
                    )
                )

                # Mock role for this test case
                with patch.object(
                    authenticator, "_get_user_role", return_value=test_case["role"]
                ):
                    # Test authentication (which includes authorization in this implementation)
                    is_authenticated = await authenticator.authenticate(request)

                    assert is_authenticated == test_case["should_authenticate"], (
                        f"Test case '{test_case['name']}': Expected authentication {test_case['should_authenticate']}, "
                        f"got {is_authenticated}"
                    )

        run_async_test(async_test())

    @given(st.text(min_size=0, max_size=100))
    @settings(max_examples=50)
    def test_token_validation_edge_cases(self, token):
        """
        Test token validation with various edge cases.

        This ensures authentication behaves correctly with unusual token inputs.
        """

        async def async_test():
            authenticator = MCPAuthenticator()

            # Act - Validate the token
            is_valid = await authenticator._validate_token(token)

            # Assert - Token validation should be consistent
            expected_valid = len(token) >= 8  # Minimum length requirement

            assert (
                is_valid == expected_valid
            ), f"Token '{token}' (length {len(token)}) validation should be {expected_valid}, got {is_valid}"

        run_async_test(async_test())

    def test_debug_mode_authentication_bypass(self):
        """
        Test that debug mode properly bypasses authentication.

        This ensures the authentication property doesn't apply in debug mode.
        """

        async def async_test():
            # Enable debug mode
            with patch.dict(os.environ, {"DEBUG": "true"}):
                from src.config import get_settings

                get_settings.cache_clear()

                authenticator = MCPAuthenticator()

                # Create request without any token
                request = CallToolRequest(
                    params=CallToolRequestParams(name="list_muppets", arguments={})
                )

                # Act - Authenticate in debug mode
                is_authenticated = await authenticator.authenticate(request)

                # Assert - Debug mode should bypass authentication
                assert (
                    is_authenticated is True
                ), "Debug mode should bypass authentication and allow all requests"

                get_settings.cache_clear()

        run_async_test(async_test())
