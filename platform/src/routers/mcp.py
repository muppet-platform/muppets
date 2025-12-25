"""
MCP Tools HTTP API Router.

This module provides HTTP endpoints for executing MCP tools,
allowing external clients to interact with the platform's MCP functionality.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..config import get_settings


logger = logging.getLogger(__name__)

router = APIRouter()


class MCPToolRequest(BaseModel):
    """Request model for MCP tool execution."""

    tool: str
    arguments: Dict[str, Any] = {}


class MCPToolResponse(BaseModel):
    """Response model for MCP tool execution."""

    success: bool
    result: Dict[str, Any]
    error: str = None


def get_mcp_tool_registry():
    """Dependency to get MCP tool registry instance."""
    # Import here to avoid circular import issues
    from ..platform_mcp.tools import MCPToolRegistry

    return MCPToolRegistry()


@router.post("/tools/execute", response_model=Dict[str, Any])
async def execute_mcp_tool(request: MCPToolRequest) -> Dict[str, Any]:
    """
    Execute an MCP tool with the provided arguments.

    Args:
        request: The tool execution request containing tool name and arguments

    Returns:
        The tool execution result as JSON

    Raises:
        HTTPException: If tool execution fails
    """
    try:
        logger.info(
            f"Executing MCP tool: {request.tool} with args: {request.arguments}"
        )

        # Create tool registry instance
        tool_registry = get_mcp_tool_registry()

        # Execute the tool
        result_json = await tool_registry.execute_tool(request.tool, request.arguments)

        # Parse the JSON result
        import json

        result = json.loads(result_json)

        logger.info(f"MCP tool {request.tool} executed successfully")
        return result

    except ValueError as e:
        # Tool not found or validation error
        logger.error(f"MCP tool validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # General execution error
        logger.error(f"MCP tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


@router.get("/tools/list")
async def list_mcp_tools() -> Dict[str, Any]:
    """
    List all available MCP tools.

    Returns:
        List of available tools with their descriptions
    """
    try:
        logger.info("Listing available MCP tools")

        # Create tool registry instance
        tool_registry = get_mcp_tool_registry()
        tools = await tool_registry.get_tools()

        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema if tool.inputSchema else {},
                }
                for tool in tools
            ],
            "total": len(tools),
        }

    except Exception as e:
        logger.error(f"Failed to list MCP tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@router.get("/health")
async def mcp_health() -> Dict[str, Any]:
    """
    Check MCP service health.

    Returns:
        Health status of the MCP service
    """
    try:
        # Try to create a tool registry to verify MCP is working
        tool_registry = get_mcp_tool_registry()
        tools = await tool_registry.get_tools()

        return {
            "status": "healthy",
            "tools_available": len(tools),
            "timestamp": "2024-01-15T10:00:00Z",
        }

    except Exception as e:
        logger.error(f"MCP health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"MCP service unhealthy: {str(e)}")
