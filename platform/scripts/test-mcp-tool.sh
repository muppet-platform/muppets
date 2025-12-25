#!/bin/bash
set -e

# Quick MCP tool testing script
# Usage: ./test-mcp-tool.sh <tool_name> [arguments_json]

TOOL_NAME="$1"
ARGUMENTS="${2:-{}}"
PLATFORM_URL="${PLATFORM_URL:-http://localhost:8000}"

if [[ -z "$TOOL_NAME" ]]; then
    echo "Usage: $0 <tool_name> [arguments_json]"
    echo ""
    echo "Available tools:"
    echo "  list_templates"
    echo "  create_muppet"
    echo "  delete_muppet"
    echo "  list_muppets"
    echo "  get_muppet_status"
    echo "  get_muppet_logs"
    echo "  setup_muppet_dev"
    echo "  update_shared_steering"
    echo "  list_steering_docs"
    echo "  update_muppet_pipelines"
    echo "  list_workflow_versions"
    echo "  rollback_muppet_pipelines"
    echo ""
    echo "Examples:"
    echo "  $0 list_templates"
    echo "  $0 create_muppet '{\"name\": \"test-muppet\", \"template\": \"java-micronaut\"}'"
    echo "  $0 get_muppet_status '{\"name\": \"test-muppet\"}'"
    exit 1
fi

echo "🔧 Testing MCP Tool: $TOOL_NAME"
echo "Arguments: $ARGUMENTS"
echo "Platform URL: $PLATFORM_URL"
echo ""

# Check if platform is running
if ! curl -s "$PLATFORM_URL/health" > /dev/null; then
    echo "❌ Platform service is not running at $PLATFORM_URL"
    echo "   Please start it with:"
    echo "   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Platform service is running"
echo ""

# Execute the MCP tool
echo "📡 Executing MCP tool..."
RESPONSE=$(curl -s -X POST "$PLATFORM_URL/mcp/tools/execute" \
  -H "Content-Type: application/json" \
  -d "{\"tool\": \"$TOOL_NAME\", \"arguments\": $ARGUMENTS}")

# Check if the response is valid JSON
if echo "$RESPONSE" | jq . > /dev/null 2>&1; then
    echo "✅ Tool executed successfully"
    echo ""
    echo "📋 Response:"
    echo "$RESPONSE" | jq .
else
    echo "❌ Tool execution failed or returned invalid JSON"
    echo ""
    echo "📋 Raw Response:"
    echo "$RESPONSE"
    exit 1
fi