"""
Authentication and authorization for MCP server.

This module provides authentication mechanisms for MCP tool requests,
ensuring only authorized users can perform muppet operations.
"""

import logging
from typing import Optional

from mcp.types import CallToolRequest

from ..config import get_settings


class MCPAuthenticator:
    """
    Authentication and authorization handler for MCP requests.

    Provides token-based authentication and role-based authorization
    for MCP tool access.
    """

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

    async def authenticate(self, request: CallToolRequest) -> bool:
        """
        Authenticate an MCP tool request.

        Args:
            request: The MCP tool call request

        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            # For now, implement basic authentication
            # In production, this would integrate with proper auth systems

            # Check for authentication headers or tokens in request metadata
            auth_token = self._extract_auth_token(request)

            if not auth_token:
                self.logger.warning("No authentication token provided")
                return False

            # Validate the token
            if not await self._validate_token(auth_token):
                self.logger.warning("Invalid authentication token")
                return False

            # Check authorization for the specific tool
            if not await self._authorize_tool_access(auth_token, request.params.name):
                self.logger.warning(
                    f"User not authorized for tool: {request.params.name}"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False

    def _extract_auth_token(self, request: CallToolRequest) -> Optional[str]:
        """
        Extract authentication token from request.

        Args:
            request: The MCP tool call request

        Returns:
            Optional[str]: The authentication token if found
        """
        # For now, we'll use a simple approach
        # In production, this would extract from proper request metadata

        # Check if token is provided in arguments (temporary approach)
        if hasattr(request.params, "arguments") and request.params.arguments:
            return request.params.arguments.get("_auth_token")

        # For development, allow requests without tokens
        if self.settings.debug:
            return "dev-token"

        return None

    async def _validate_token(self, token: str) -> bool:
        """
        Validate an authentication token.

        Args:
            token: The authentication token to validate

        Returns:
            bool: True if token is valid, False otherwise
        """
        # For development, accept dev-token
        if self.settings.debug and token == "dev-token":
            return True

        # In production, this would validate against:
        # - JWT tokens
        # - API keys stored in AWS Parameter Store
        # - Integration with identity providers (OAuth, SAML, etc.)

        # For now, implement basic token validation
        # This is a placeholder for proper authentication
        return len(token) >= 8  # Minimum token length

    async def _authorize_tool_access(self, token: str, tool_name: str) -> bool:
        """
        Check if the authenticated user is authorized to use a specific tool.

        Args:
            token: The validated authentication token
            tool_name: The name of the tool being accessed

        Returns:
            bool: True if authorized, False otherwise
        """
        # For development, allow all tools
        if self.settings.debug:
            return True

        # In production, this would implement role-based access control:
        # - Admin users: all tools
        # - Developer users: create, list, status tools
        # - Read-only users: list, status tools only

        # Get user role from token (placeholder)
        user_role = await self._get_user_role(token)

        # Define tool permissions
        tool_permissions = {
            "create_muppet": ["admin", "developer"],
            "delete_muppet": ["admin", "developer"],
            "list_muppets": ["admin", "developer", "readonly"],
            "list_templates": ["admin", "developer", "readonly"],
            "get_muppet_status": ["admin", "developer", "readonly"],
            "get_muppet_logs": ["admin", "developer", "readonly"],
            "setup_muppet_dev": ["admin", "developer"],
            "update_shared_steering": ["admin"],
            "list_steering_docs": ["admin", "developer", "readonly"],
        }

        allowed_roles = tool_permissions.get(tool_name, [])
        return user_role in allowed_roles

    async def _get_user_role(self, token: str) -> str:
        """
        Get user role from authentication token.

        Args:
            token: The validated authentication token

        Returns:
            str: The user role
        """
        # For development, return admin role
        if self.settings.debug:
            return "admin"

        # In production, this would:
        # - Decode JWT token to get user claims
        # - Query user database for role information
        # - Cache role information for performance

        # Placeholder implementation
        return "developer"
