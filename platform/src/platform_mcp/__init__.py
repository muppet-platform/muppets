"""
MCP (Model Context Protocol) server implementation for the Muppet Platform.

This package provides the MCP server interface that allows Kiro to interact
with the Muppet Platform through standardized tools.
"""

from .auth import MCPAuthenticator
from .server import MCPServer
from .tools import MCPToolRegistry

__all__ = ["MCPServer", "MCPAuthenticator", "MCPToolRegistry"]
