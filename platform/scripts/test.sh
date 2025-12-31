#!/bin/bash

# Test script for Muppet Platform

set -e

echo "Running Muppet Platform tests..."

# Check if LocalStack is running (for local development)
if curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
    echo "✅ LocalStack detected - running tests with AWS simulation"
    export AWS_ENDPOINT_URL=http://localhost:4566
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-west-2
else
    echo "ℹ️  LocalStack not detected - running tests without AWS simulation"
fi

# Configure Hypothesis based on environment
mkdir -p .hypothesis
if [ -n "$CI" ]; then
    echo "🔧 Configuring Hypothesis for CI (fast property tests - 25% of examples)..."
    cat > .hypothesis/settings.json << EOF
{
  "ci": {
    "max_examples": 25,
    "deadline": 5000,
    "suppress_health_check": ["too_slow"]
  }
}
EOF
    export HYPOTHESIS_PROFILE=ci
else
    echo "🔧 Configuring Hypothesis for local development (full property tests)..."
    cat > .hypothesis/settings.json << EOF
{
  "local": {
    "max_examples": 100,
    "deadline": 10000,
    "suppress_health_check": ["too_slow"]
  }
}
EOF
    export HYPOTHESIS_PROFILE=local
fi

# Run all tests (including property tests)
echo "🧪 Running platform tests..."
uv run python -m pytest tests/ -v

# Run MCP-specific tests if LocalStack is available
if [ -n "$AWS_ENDPOINT_URL" ]; then
    echo "🔍 Testing MCP server functionality..."
    
    # Test MCP server startup
    echo "  - Testing MCP server startup..."
    timeout 30 uv run python -m src.platform_mcp.cli &
    MCP_PID=$!
    sleep 5
    kill $MCP_PID || true
    
    # Run MCP-specific tests
    echo "  - Running MCP-specific tests..."
    uv run python -m pytest tests/test_mcp_*.py -v --tb=short
    
    # Test MCP tool discovery
    echo "  - Testing MCP tool discovery..."
    uv run python -c "
import asyncio
from src.platform_mcp.tools import MCPToolRegistry

async def test_tool_discovery():
    registry = MCPToolRegistry()
    tools = await registry.get_tools()
    expected_tools = ['create_muppet', 'list_muppets', 'get_muppet_status', 'get_muppet_logs', 'list_templates', 'setup_muppet_dev', 'update_shared_steering', 'list_steering_docs', 'update_muppet_pipelines', 'list_workflow_versions', 'rollback_muppet_pipelines']
    missing = set(expected_tools) - set(tool.name for tool in tools)
    if missing:
        print(f'Missing MCP tools: {missing}')
        exit(1)
    print(f'✅ All {len(tools)} MCP tools discovered successfully')

asyncio.run(test_tool_discovery())
"
    
    # Validate MCP tool schemas
    echo "  - Validating MCP tool schemas..."
    uv run python -c "
import asyncio
from src.platform_mcp.tools import MCPToolRegistry

async def test_tool_schemas():
    registry = MCPToolRegistry()
    tools = await registry.get_tools()
    
    for tool in tools:
        try:
            assert hasattr(tool, 'name'), f'Tool {tool} missing name'
            assert hasattr(tool, 'description'), f'Tool {tool.name} missing description'
            assert hasattr(tool, 'inputSchema'), f'Tool {tool.name} missing inputSchema'
            
            schema = tool.inputSchema
            assert 'type' in schema, f'Tool {tool.name} schema missing type'
            assert 'properties' in schema, f'Tool {tool.name} schema missing properties'
            
            print(f'✅ Tool {tool.name} schema valid')
        except Exception as e:
            print(f'❌ Tool {tool.name} schema invalid: {e}')
            exit(1)
    
    print('✅ All MCP tool schemas are valid')

asyncio.run(test_tool_schemas())
"
    
    echo "✅ MCP validation complete"
else
    echo "⚠️  Skipping MCP tests (LocalStack not available)"
fi

echo "✅ Tests complete!"
