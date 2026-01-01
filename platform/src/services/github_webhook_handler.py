"""
GitHub Webhook Handler for TLS Auto-Enhancement

Monitors GitHub Actions workflow completions and automatically enhances
muppets with TLS when their CD workflows complete successfully.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from ..config import get_settings
from ..logging_config import get_logger
from .muppet_tls_enhancer import MuppetTLSEnhancer

logger = get_logger(__name__)


class GitHubWebhookHandler:
    """Handles GitHub webhooks for automatic TLS enhancement."""

    def __init__(self):
        """Initialize the webhook handler."""
        self.tls_enhancer = MuppetTLSEnhancer()
        self.settings = get_settings()
        logger.info("GitHub webhook handler initialized")

    async def handle_workflow_run_completed(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle workflow_run completed events.

        Automatically enhances muppets with TLS when their CD workflow completes successfully.
        """
        try:
            workflow_run = payload.get("workflow_run", {})
            repository = payload.get("repository", {})

            # Extract key information
            workflow_name = workflow_run.get("name", "")
            workflow_conclusion = workflow_run.get("conclusion", "")
            repo_name = repository.get("name", "")
            repo_full_name = repository.get("full_name", "")

            logger.info(
                f"Received workflow completion: {repo_full_name} - {workflow_name} - {workflow_conclusion}"
            )

            # Only process CD workflows that completed successfully
            if workflow_name.lower() != "cd" or workflow_conclusion != "success":
                logger.info(
                    f"Skipping non-CD or failed workflow: {workflow_name} ({workflow_conclusion})"
                )
                return {"processed": False, "reason": "Not a successful CD workflow"}

            # Check if this is a muppet repository
            if not await self._is_muppet_repository(repo_full_name):
                logger.info(f"Skipping non-muppet repository: {repo_full_name}")
                return {"processed": False, "reason": "Not a muppet repository"}

            # Extract muppet name from repository name
            muppet_name = repo_name

            logger.info(f"Processing CD completion for muppet: {muppet_name}")

            # Wait a bit for infrastructure to be ready
            await asyncio.sleep(30)  # Give AWS resources time to be available

            # Automatically enhance with TLS
            enhancement_result = await self.tls_enhancer.enhance_muppet_with_tls(
                muppet_name
            )

            if enhancement_result["success"]:
                logger.info(f"Successfully auto-enhanced muppet {muppet_name} with TLS")

                # TODO: Notify the muppet team (Slack, email, GitHub comment)
                await self._notify_muppet_team(
                    muppet_name, enhancement_result, repo_full_name
                )

                return {
                    "processed": True,
                    "muppet_name": muppet_name,
                    "https_endpoint": enhancement_result.get("https_endpoint"),
                    "enhancement_result": enhancement_result,
                }
            else:
                logger.warning(
                    f"Failed to auto-enhance muppet {muppet_name}: {enhancement_result.get('error')}"
                )
                return {
                    "processed": True,
                    "muppet_name": muppet_name,
                    "success": False,
                    "error": enhancement_result.get("error"),
                }

        except Exception as e:
            logger.error(f"Error handling workflow completion webhook: {e}")
            return {"processed": False, "error": str(e)}

    async def _is_muppet_repository(self, repo_full_name: str) -> bool:
        """Check if a repository is a muppet repository."""
        try:
            # Check if it's in the muppet-platform organization
            if not repo_full_name.startswith("muppet-platform/"):
                return False

            # Exclude the main platform repositories
            excluded_repos = [
                "muppet-platform/muppets",  # Main platform repo
                "muppet-platform/docs",  # Documentation
                "muppet-platform/templates",  # Templates
            ]

            if repo_full_name in excluded_repos:
                return False

            # If it has a CD workflow, it's likely a muppet
            return True

        except Exception as e:
            logger.warning(
                f"Error checking if {repo_full_name} is a muppet repository: {e}"
            )
            return False

    async def _notify_muppet_team(
        self, muppet_name: str, enhancement_result: Dict[str, Any], repo_full_name: str
    ):
        """Notify the muppet team that TLS has been automatically enabled."""
        try:
            https_endpoint = enhancement_result.get("https_endpoint")

            # Create a GitHub issue comment or PR comment
            notification_message = f"""
🔒 **TLS Automatically Enabled!**

Your muppet `{muppet_name}` has been automatically enhanced with TLS following your successful deployment.

**New HTTPS Endpoint:** {https_endpoint}

**What happened:**
- ✅ HTTPS listener added to your load balancer
- ✅ Security group updated to allow HTTPS traffic
- ✅ DNS record created: `{muppet_name}.s3u.dev`
- ✅ HTTP→HTTPS redirect configured

**No action required** - your service is now available over HTTPS with zero configuration changes!

---
*This enhancement was performed automatically by the Muppet Platform following the "Zero Breaking Changes" principle.*
"""

            # TODO: Implement actual notification (GitHub API, Slack, etc.)
            logger.info(f"Notification for {muppet_name}: {notification_message}")

        except Exception as e:
            logger.warning(f"Failed to notify team for muppet {muppet_name}: {e}")
