# Kiro Configuration for verify-java-micronaut-1766638048

This directory contains Kiro-specific configuration for your muppet.

## MCP Server Configuration

The `settings/mcp.json` file configures the Muppet Platform MCP server, which provides tools for managing your muppet's lifecycle directly from Kiro.

### Available Tools

The platform MCP server provides these tools:

#### Muppet Management
- `get_muppet_status` - Get detailed status and metrics for this muppet
- `list_muppets` - List all muppets in the platform
- `delete_muppet` - Delete this muppet and clean up resources

#### Template Management  
- `list_templates` - Show available muppet templates
- `create_muppet` - Create new muppets from templates

#### Development Tools
- `get_muppet_logs` - Retrieve logs from this muppet
- `setup_muppet_dev` - Configure local development environment

#### Steering Documentation
- `update_shared_steering` - Update shared steering docs
- `list_steering_docs` - Show available steering documentation

### Auto-Approved Tools

The following tools are auto-approved and won't require confirmation:
- `get_muppet_status` - Safe read-only status checks
- `list_muppets` - Safe read-only listing
- `list_templates` - Safe read-only template information
- `get_muppet_logs` - Safe read-only log access

### Usage

Once configured, you can use these tools in Kiro by mentioning muppet-related tasks:

```
"Show me the status of this muppet"
"Get the logs for my muppet"
"List all available templates"
"Create a new muppet called 'user-service'"
```

### Configuration Details

The MCP server configuration includes:
- **Command**: Uses `uv run mcp-server` to start the platform MCP server
- **Working Directory**: Points to the platform directory
- **Environment**: Sets `INTEGRATION_MODE=real` for live platform access
- **Auto-Approval**: Pre-approves safe read-only operations

### Troubleshooting

If the MCP server isn't working:

1. **Check Platform Path**: Ensure the `cwd` in `mcp.json` points to the correct platform directory
2. **Check Dependencies**: Ensure `uv` is installed and the platform dependencies are available
3. **Check Logs**: Look at Kiro's MCP logs for connection errors
4. **Test Manually**: Try running `uv run mcp-server` from the platform directory

### Security

The MCP server uses token-based authentication:
- **Development Mode**: Accepts `dev-token` for local development
- **Production Mode**: Requires proper authentication tokens

For local development, the server runs in development mode by default.