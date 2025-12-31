#!/usr/bin/env python3
"""
MCP HTTP Bridge Client

This script acts as a bridge between Kiro's MCP client and the Muppet Platform's HTTP API.
It translates MCP protocol calls to HTTP API requests.
"""

import asyncio
import json
import sys
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPHTTPBridge:
    """Bridge between MCP protocol and HTTP API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def list_tools(self):
        """List available tools from HTTP API."""
        try:
            response = await self.client.get(f"{self.base_url}/tools/list")
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])
        except Exception as e:
            print(f"Error listing tools: {e}", file=sys.stderr)
            return []
    
    async def execute_tool(self, tool_name: str, arguments: dict):
        """Execute a tool via HTTP API."""
        try:
            payload = {
                "tool": tool_name,
                "arguments": arguments
            }
            response = await self.client.post(
                f"{self.base_url}/tools/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}", file=sys.stderr)
            return {"error": str(e)}
    
    async def health_check(self):
        """Check if the HTTP API is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}", file=sys.stderr)
            return {"status": "unhealthy", "error": str(e)}


async def main():
    """Main bridge function."""
    if len(sys.argv) != 2:
        print("Usage: python mcp_http_bridge.py <base_url>", file=sys.stderr)
        sys.exit(1)
    
    base_url = sys.argv[1]
    bridge = MCPHTTPBridge(base_url)
    
    # Test connection
    health = await bridge.health_check()
    if health.get("status") != "healthy":
        print(f"MCP HTTP API is not healthy: {health}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Connected to Muppet Platform at {base_url}", file=sys.stderr)
    print(f"Available tools: {health.get('tools_available', 0)}", file=sys.stderr)
    
    # List available tools
    tools = await bridge.list_tools()
    print(f"Tools: {[tool['name'] for tool in tools]}", file=sys.stderr)
    
    # Simple interactive mode for testing
    while True:
        try:
            line = input().strip()
            if not line:
                continue
                
            if line == "quit":
                break
                
            # Parse JSON command
            try:
                command = json.loads(line)
                if command.get("method") == "tools/list":
                    result = {"tools": tools}
                elif command.get("method") == "tools/call":
                    params = command.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await bridge.execute_tool(tool_name, arguments)
                else:
                    result = {"error": f"Unknown method: {command.get('method')}"}
                
                print(json.dumps(result))
                
            except json.JSONDecodeError:
                print(json.dumps({"error": "Invalid JSON"}))
                
        except EOFError:
            break
        except KeyboardInterrupt:
            break
    
    await bridge.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())