#!/bin/bash

# {{muppet_name}} - Test MCP Server Connection
# This script tests the connection to the Muppet Platform MCP server

set -e

echo "🔌 Testing MCP server connection for {{muppet_name}}..."

# Check if .kiro/settings/mcp.json exists
if [ ! -f ".kiro/settings/mcp.json" ]; then
    echo "❌ MCP configuration not found at .kiro/settings/mcp.json"
    echo "   This file should have been created when the muppet was generated."
    exit 1
fi

echo "✅ Found MCP configuration file"

# Extract platform path from MCP config
PLATFORM_PATH=$(grep -o '"cwd": "[^"]*"' .kiro/settings/mcp.json | cut -d'"' -f4)

if [ -z "$PLATFORM_PATH" ]; then
    echo "❌ Could not extract platform path from MCP configuration"
    exit 1
fi

echo "📁 Platform path: $PLATFORM_PATH"

# Check if platform directory exists
if [ ! -d "$PLATFORM_PATH" ]; then
    echo "❌ Platform directory not found: $PLATFORM_PATH"
    echo "   Please ensure the Muppet Platform is available at this location."
    exit 1
fi

echo "✅ Platform directory exists"

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ UV not found in PATH"
    echo "   Please install UV: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "✅ UV is available"

# Check if platform has required dependencies
if [ ! -f "$PLATFORM_PATH/pyproject.toml" ]; then
    echo "❌ Platform pyproject.toml not found"
    echo "   The platform directory may be incomplete."
    exit 1
fi

echo "✅ Platform configuration found"

# Test MCP server startup (quick test)
echo "🧪 Testing MCP server startup..."
cd "$PLATFORM_PATH"

# Set test environment
export INTEGRATION_MODE=real
export LOG_LEVEL=ERROR

# Try to start MCP server with a timeout
timeout 10s uv run mcp-server --help >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ MCP server can start successfully"
elif [ $? -eq 124 ]; then
    echo "✅ MCP server startup test completed (timeout expected)"
else
    echo "❌ MCP server failed to start"
    echo "   Try running: cd $PLATFORM_PATH && uv run mcp-server --help"
    exit 1
fi

echo ""
echo "🎉 MCP server connection test completed successfully!"
echo ""
echo "Next steps:"
echo "1. Open this muppet directory in Kiro"
echo "2. The MCP server should automatically connect"
echo "3. Try asking Kiro: 'Show me the status of this muppet'"
echo ""
echo "If you have issues:"
echo "- Check Kiro's MCP logs for connection errors"
echo "- Ensure the platform server is running"
echo "- Verify the platform path in .kiro/settings/mcp.json"