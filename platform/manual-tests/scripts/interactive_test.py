#!/usr/bin/env python3
"""
Interactive manual testing script for Muppet Platform.

This script provides an interactive interface for testing platform
functionality with real AWS and GitHub integrations via HTTP API calls.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class InteractiveTester:
    """Interactive testing interface for manual platform testing."""

    def __init__(self):
        self.platform_url = os.getenv("PLATFORM_URL", "http://localhost:8000")
        self.test_muppets = []
        self.session = None

    async def initialize(self):
        """Initialize the testing environment."""
        logger.info("🚀 Initializing Interactive Muppet Platform Tester")
        logger.info("=" * 50)

        # Check if we're in real integration mode
        integration_mode = os.getenv("INTEGRATION_MODE", "mock")
        logger.info(f"Integration Mode: {integration_mode}")
        logger.info(f"Platform URL: {self.platform_url}")

        if integration_mode != "real":
            logger.warning(
                "⚠️  Not in real integration mode. Set INTEGRATION_MODE=real for full testing."
            )

        # Create HTTP session with longer timeout for muppet operations
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
        self.session = aiohttp.ClientSession(timeout=timeout)

        # Verify platform connectivity
        await self._verify_platform_connectivity()

        # Verify external service connectivity
        await self._verify_external_connectivity()

    async def _verify_platform_connectivity(self):
        """Verify connectivity to the platform service."""
        logger.info("🔍 Verifying platform connectivity...")

        try:
            async with self.session.get(f"{self.platform_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(
                        f"✅ Platform service is running: {health_data.get('status', 'unknown')}"
                    )
                else:
                    raise Exception(
                        f"Health check failed with status {response.status}"
                    )
        except Exception as e:
            logger.error(f"❌ Cannot connect to platform service at {self.platform_url}")
            logger.error(f"   Error: {e}")
            logger.error("   Please start the platform service with:")
            logger.error(
                "   cd platform && python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
            )
            raise

    async def _verify_external_connectivity(self):
        """Verify connectivity to external services."""
        logger.info("🔍 Verifying external service connectivity...")

        # Test GitHub connectivity
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            logger.info("✅ GitHub token configured")
        else:
            logger.warning("⚠️  GitHub token not configured")

        # Test AWS connectivity
        aws_region = os.getenv("AWS_REGION", "us-west-2")
        logger.info(f"✅ AWS region: {aws_region}")

    async def _execute_mcp_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an MCP tool via HTTP API."""
        payload = {"tool": tool_name, "arguments": arguments}

        try:
            async with self.session.post(
                f"{self.platform_url}/mcp/tools/execute",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(
                    total=120
                ),  # 2 minute timeout for long operations
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"❌ Failed to execute tool {tool_name}: {e}")
            raise

    async def run_interactive_session(self):
        """Run the interactive testing session."""
        while True:
            print("\n" + "=" * 50)
            print("🎭 Muppet Platform Interactive Tester")
            print("=" * 50)
            print("1. List available templates")
            print("2. Create a test muppet")
            print("3. Get muppet status")
            print("4. List all muppets")
            print("5. Test pipeline management")
            print("6. Test steering documentation")
            print("7. Run cleanup (manual deletion instructions)")
            print("8. Exit")
            print("-" * 50)

            choice = input("Select an option (1-8): ").strip()

            try:
                if choice == "1":
                    await self._test_list_templates()
                elif choice == "2":
                    await self._test_create_muppet()
                elif choice == "3":
                    await self._test_get_muppet_status()
                elif choice == "4":
                    await self._test_list_muppets()
                elif choice == "5":
                    await self._test_pipeline_management()
                elif choice == "6":
                    await self._test_steering_docs()
                elif choice == "7":
                    await self._show_manual_deletion_instructions()
                elif choice == "8":
                    break
                else:
                    print("❌ Invalid choice. Please select 1-8.")
            except Exception as e:
                logger.error(f"❌ Test failed: {e}")
                print(f"Error: {e}")

    async def _test_list_templates(self):
        """Test listing available templates."""
        print("\n📋 Testing: List Templates")
        response = await self._execute_mcp_tool("list_templates", {})

        if "templates" in response:
            print(f"✅ Found {len(response['templates'])} templates:")
            for template in response["templates"]:
                print(f"   - {template['name']}: {template['description']}")
        else:
            print("❌ No templates found or error occurred")
            print(f"Response: {json.dumps(response, indent=2)}")

    async def _test_create_muppet(self):
        """Test creating a muppet."""
        print("\n🎭 Testing: Create Muppet")

        muppet_name = input(
            "Enter muppet name (or press Enter for 'test-manual-muppet'): "
        ).strip()
        if not muppet_name:
            muppet_name = "test-manual-muppet"

        template = input(
            "Enter template name (or press Enter for 'java-micronaut'): "
        ).strip()
        if not template:
            template = "java-micronaut"

        print(f"Creating muppet: {muppet_name} with template: {template}")

        response = await self._execute_mcp_tool(
            "create_muppet", {"name": muppet_name, "template": template}
        )

        if response.get("success"):
            print(f"✅ Muppet created successfully!")
            print(f"   Repository: {response.get('repository', {}).get('url', 'N/A')}")
            self.test_muppets.append(muppet_name)
        else:
            print(
                f"❌ Failed to create muppet: {response.get('error', 'Unknown error')}"
            )

    async def _test_get_muppet_status(self):
        """Test getting muppet status."""
        print("\n📊 Testing: Get Muppet Status")

        if self.test_muppets:
            print("Available test muppets:")
            for i, muppet in enumerate(self.test_muppets, 1):
                print(f"   {i}. {muppet}")

            choice = input("Select muppet number or enter custom name: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(self.test_muppets):
                muppet_name = self.test_muppets[int(choice) - 1]
            else:
                muppet_name = choice
        else:
            muppet_name = input("Enter muppet name: ").strip()

        if not muppet_name:
            print("❌ No muppet name provided")
            return

        response = await self._execute_mcp_tool(
            "get_muppet_status", {"name": muppet_name}
        )

        if response.get("success", True):  # Some tools don't return success field
            print(f"✅ Status for {muppet_name}:")
            if "muppet" in response:
                muppet_info = response["muppet"]
                print(f"   Status: {muppet_info.get('status', 'unknown')}")
                print(f"   Template: {muppet_info.get('template', 'unknown')}")
                print(f"   GitHub: {muppet_info.get('github_repo', 'N/A')}")
        else:
            print(f"❌ Failed to get status: {response.get('error', 'Unknown error')}")

    async def _test_list_muppets(self):
        """Test listing all muppets."""
        print("\n📝 Testing: List Muppets")

        response = await self._execute_mcp_tool("list_muppets", {})

        if "muppets" in response:
            muppets = response["muppets"]
            print(f"✅ Found {len(muppets)} muppets:")
            for muppet in muppets:
                print(
                    f"   - {muppet.get('name', 'unknown')} ({muppet.get('status', 'unknown')})"
                )
        else:
            print("❌ No muppets found or error occurred")
            print(f"Response: {json.dumps(response, indent=2)}")

    async def _show_manual_deletion_instructions(self):
        """Show instructions for manual muppet deletion."""
        print("\n🗑️  Manual Muppet Deletion Instructions")
        print("=" * 50)
        print("For safety, muppet deletion is now a manual operation.")
        print("To delete a muppet, follow these steps:")
        print()
        print("1. **Delete GitHub Repository:**")
        print("   gh repo delete muppet-platform/<muppet-name> --yes")
        print()
        print("2. **Clean up AWS Infrastructure (if deployed):**")
        print("   cd <muppet-directory>/terraform")
        print("   tofu destroy")
        print()
        print("3. **Remove local files (if any):**")
        print("   rm -rf <local-muppet-directory>")
        print()
        print("4. **Clean up AWS Parameter Store (if used):**")
        print(
            "   aws ssm delete-parameter --name /muppet-platform/<muppet-name>/config"
        )
        print()

        if self.test_muppets:
            print("Current test muppets that may need cleanup:")
            for muppet in self.test_muppets:
                print(f"   - {muppet}")
                print(f"     GitHub: https://github.com/muppet-platform/{muppet}")
            print()
            print("Example deletion commands for test muppets:")
            for muppet in self.test_muppets:
                print(f"   gh repo delete muppet-platform/{muppet} --yes")
        else:
            print("No test muppets tracked in this session.")

        print()
        print(
            "⚠️  **Important:** Always verify what you're deleting before running commands!"
        )
        input("Press Enter to continue...")

    async def _test_pipeline_management(self):
        """Test pipeline management tools."""
        print("\n🔧 Testing: Pipeline Management")
        print("1. List workflow versions")
        print("2. Update muppet pipelines")
        print("3. Rollback muppet pipelines")

        choice = input("Select pipeline test (1-3): ").strip()

        if choice == "1":
            template_type = input(
                "Enter template type (or press Enter for 'java-micronaut'): "
            ).strip()
            if not template_type:
                template_type = "java-micronaut"

            response = await self._execute_mcp_tool(
                "list_workflow_versions", {"template_type": template_type}
            )
            print(f"Workflow versions for {template_type}:")
            print(json.dumps(response, indent=2))

        elif choice in ["2", "3"]:
            muppet_name = input("Enter muppet name: ").strip()
            workflow_version = input(
                "Enter workflow version (e.g., 'java-micronaut-v1.2.3'): "
            ).strip()

            if not muppet_name or not workflow_version:
                print("❌ Both muppet name and workflow version are required")
                return

            tool_name = (
                "update_muppet_pipelines"
                if choice == "2"
                else "rollback_muppet_pipelines"
            )
            response = await self._execute_mcp_tool(
                tool_name,
                {"muppet_name": muppet_name, "workflow_version": workflow_version},
            )

            if response.get("success"):
                action = "updated" if choice == "2" else "rolled back"
                print(f"✅ Pipelines {action} successfully!")
            else:
                print(
                    f"❌ Pipeline operation failed: {response.get('error', 'Unknown error')}"
                )

    async def _test_steering_docs(self):
        """Test steering documentation tools."""
        print("\n📚 Testing: Steering Documentation")
        print("1. List steering docs")
        print("2. Update shared steering")

        choice = input("Select steering test (1-2): ").strip()

        if choice == "1":
            muppet_name = input("Enter muppet name (optional): ").strip()
            args = {"muppet_name": muppet_name} if muppet_name else {}

            response = await self._execute_mcp_tool("list_steering_docs", args)
            print("Steering documentation:")
            print(json.dumps(response, indent=2))

        elif choice == "2":
            response = await self._execute_mcp_tool("update_shared_steering", {})
            if response.get("success"):
                print("✅ Shared steering updated successfully!")
            else:
                print(
                    f"❌ Steering update failed: {response.get('error', 'Unknown error')}"
                )

    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()


async def main():
    """Main function for interactive testing."""
    tester = InteractiveTester()

    try:
        await tester.initialize()
        await tester.run_interactive_session()
    except KeyboardInterrupt:
        print("\n👋 Testing session interrupted by user")
    except Exception as e:
        logger.error(f"❌ Testing session failed: {e}")
        return 1
    finally:
        await tester.cleanup()

    print("👋 Testing session complete")
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
