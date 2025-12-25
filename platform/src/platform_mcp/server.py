"""
MCP Server implementation for the Muppet Platform.

This module implements the Model Context Protocol server that provides
tools for muppet lifecycle management through Kiro.
"""

import asyncio
import logging

from mcp import McpError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_REQUEST,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
)

from ..config import get_settings
from ..integrations.github import GitHubClient
from ..managers.steering_manager import SteeringManager
from .auth import MCPAuthenticator
from .tools import MCPToolRegistry


class MCPServer:
    """
    MCP Server for the Muppet Platform.

    Provides tools for muppet lifecycle management, template operations,
    and platform monitoring through the Model Context Protocol.
    """

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.server = Server(self.settings.mcp.name)
        self.authenticator = MCPAuthenticator()

        # Initialize steering manager
        self.github_client = GitHubClient()
        self.steering_manager = SteeringManager(self.github_client)

        # Initialize tool registry with steering manager
        self.tool_registry = MCPToolRegistry(steering_manager=self.steering_manager)

        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List all available MCP tools."""
            try:
                self.logger.info("Listing available MCP tools")
                tools = await self.tool_registry.get_tools()
                return ListToolsResult(tools=tools)
            except Exception as e:
                self.logger.error(f"Error listing tools: {e}")
                raise McpError(code=INTERNAL_ERROR, message="Failed to list tools")

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Execute an MCP tool."""
            try:
                # Authenticate the request
                if not await self.authenticator.authenticate(request):
                    raise McpError(
                        code=INVALID_REQUEST, message="Authentication failed"
                    )

                self.logger.info(f"Executing tool: {request.params.name}")

                # Execute the tool
                result = await self.tool_registry.execute_tool(
                    request.params.name, request.params.arguments or {}
                )

                return CallToolResult(content=[TextContent(type="text", text=result)])

            except McpError:
                raise
            except Exception as e:
                self.logger.error(f"Error executing tool {request.params.name}: {e}")
                raise McpError(
                    code=INTERNAL_ERROR, message=f"Tool execution failed: {str(e)}"
                )

    async def start(self):
        """Start the MCP server."""
        try:
            self.logger.info(
                f"Starting MCP server on protocol: {self.settings.mcp.protocol}"
            )

            # Initialize steering manager
            await self.steering_manager.initialize()

            if self.settings.mcp.protocol == "stdio":
                async with stdio_server() as (read_stream, write_stream):
                    await self.server.run(
                        read_stream,
                        write_stream,
                        self.server.create_initialization_options(),
                    )
            else:
                raise ValueError(
                    f"Unsupported MCP protocol: {self.settings.mcp.protocol}"
                )

        except Exception as e:
            self.logger.error(f"MCP server error: {e}")
            raise

    async def stop(self):
        """Stop the MCP server."""
        self.logger.info("Stopping MCP server")

        # Clean up steering manager
        if self.steering_manager:
            await self.steering_manager.close()

        # Clean up GitHub client
        if self.github_client:
            await self.github_client.close()

        # Server cleanup will be handled by context managers


async def run_mcp_server():
    """Run the MCP server as a standalone process."""
    server = MCPServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
