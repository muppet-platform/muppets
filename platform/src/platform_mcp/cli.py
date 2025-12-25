"""
CLI entry point for the MCP server.

This module provides command-line interface for running the MCP server
as a standalone process or integrating with the main platform service.
"""

import asyncio
import logging
import sys

import click

from ..config import get_settings
from ..logging_config import setup_logging
from .server import MCPServer


@click.command()
@click.option(
    "--protocol",
    type=click.Choice(["stdio", "http", "websocket"]),
    default="stdio",
    help="MCP protocol to use",
)
@click.option(
    "--port", type=int, default=8001, help="Port for HTTP/WebSocket protocols"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Logging level",
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def run_mcp_server(protocol: str, port: int, log_level: str, debug: bool):
    """Run the MCP server for the Muppet Platform."""

    # Set up logging
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    # Override settings with CLI options
    settings = get_settings()
    settings.mcp.protocol = protocol
    settings.mcp.port = port
    settings.debug = debug
    settings.log_level = log_level

    logger.info(f"Starting MCP server with protocol: {protocol}")

    try:
        # Create and run the MCP server
        server = MCPServer()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"MCP server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_mcp_server()
