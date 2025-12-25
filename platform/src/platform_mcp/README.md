# MCP Server for Muppet Platform

This directory contains the Model Context Protocol (MCP) server implementation for the Muppet Platform. The MCP server provides tools that allow Kiro to interact with the platform for muppet lifecycle management.

## Setup with UV (Recommended)

UV provides better Python version management and dependency isolation:

```bash
# Run the setup script
./setup-uv.sh

# Or manually:
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment with Python 3.10+
uv venv --python 3.10

# Activate environment
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"
```

## Running the MCP Server

```bash
# Using UV (recommended)
uv run mcp-server

# Or with activated environment
source .venv/bin/activate
mcp-server

# Or directly with Python
python -m src.platform_mcp.cli
```

## Available MCP Tools

The server provides the following tools for Kiro:

### Muppet Lifecycle Management
- `create_muppet` - Create a new muppet from a template
- `delete_muppet` - Delete a muppet and clean up resources
- `list_muppets` - List all active muppets

### Template Management
- `list_templates` - Show available muppet templates

### Monitoring and Status
- `get_muppet_status` - Get detailed muppet information
- `get_muppet_logs` - Retrieve muppet logs

### Development Tools
- `setup_muppet_dev` - Configure local Kiro environment for muppet development

### Steering Documentation
- `update_shared_steering` - Update shared steering docs across all muppets
- `list_steering_docs` - Show available steering documentation

## Authentication

The MCP server implements token-based authentication:

- **Development Mode**: Accepts `dev-token` or allows requests without tokens
- **Production Mode**: Requires valid authentication tokens with role-based access control

## Configuration

Configuration is managed through environment variables and the main platform settings:

```bash
# MCP Server settings
MCP_NAME=mcp-server
MCP_PORT=8001
MCP_PROTOCOL=stdio

# Platform settings
DEBUG=true
LOG_LEVEL=INFO
```

## Testing

```bash
# Run all tests
uv run pytest

# Run MCP-specific tests
uv run pytest tests/test_mcp_server.py

# Run with coverage
uv run pytest --cov=src.platform_mcp
```

## Development

The MCP server is organized into three main components:

- **server.py** - Main MCP server implementation using the official MCP SDK
- **auth.py** - Authentication and authorization handling
- **tools.py** - Tool registry and handler implementations

### Adding New Tools

1. Add the tool definition in `tools.py` in the `_register_tools()` method
2. Implement the handler method (e.g., `_handle_new_tool()`)
3. Add appropriate authentication rules in `auth.py`
4. Write tests in `tests/test_mcp_server.py`

## Integration with Kiro

The MCP server is designed to be used with Kiro through the Model Context Protocol. Kiro can discover and execute the available tools to manage muppets on the platform.

Example Kiro MCP configuration:
```json
{
  "mcpServers": {
    "muppet-platform": {
      "command": "uv",
      "args": ["run", "mcp-server"],
      "cwd": "/path/to/muppet-platform/platform"
    }
  }
}
```