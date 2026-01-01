"""
TLS Auto-Enhancement Background Service

Periodically discovers and enhances muppets with TLS automatically.
Implements the "Zero Breaking Changes" principle by continuously monitoring
and enhancing muppets without requiring developer intervention.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..config import get_settings
from ..logging_config import get_logger
from .muppet_tls_enhancer import MuppetTLSEnhancer

logger = get_logger(__name__)


class TLSAutoEnhancementService:
    """Background service for automatic TLS enhancement of muppets."""

    def __init__(self):
        """Initialize the auto-enhancement service."""
        self.tls_enhancer = MuppetTLSEnhancer()
        self.settings = get_settings()
        self.running = False
        self.enhancement_history: List[Dict[str, Any]] = []
        logger.info("TLS auto-enhancement service initialized")

    async def start(self):
        """Start the background enhancement service."""
        if self.running:
            logger.warning("TLS auto-enhancement service is already running")
            return

        self.running = True
        logger.info("Starting TLS auto-enhancement background service")

        # Run the enhancement loop
        await self._enhancement_loop()

    async def stop(self):
        """Stop the background enhancement service."""
        self.running = False
        logger.info("Stopping TLS auto-enhancement background service")

    async def _enhancement_loop(self):
        """Main enhancement loop that runs periodically."""
        while self.running:
            try:
                logger.info("Running periodic TLS enhancement check...")

                # Discover muppets needing enhancement
                muppets = await self.tls_enhancer.list_muppets_needing_tls_enhancement()
                muppets_needing_enhancement = [
                    m for m in muppets if m["needs_enhancement"]
                ]

                if not muppets_needing_enhancement:
                    logger.info("No muppets need TLS enhancement")
                else:
                    logger.info(
                        f"Found {len(muppets_needing_enhancement)} muppets needing TLS enhancement"
                    )

                    # Enhance each muppet
                    for muppet in muppets_needing_enhancement:
                        if not self.running:  # Check if we should stop
                            break

                        await self._enhance_muppet_safely(muppet["muppet_name"])

                        # Small delay between enhancements to avoid overwhelming AWS APIs
                        await asyncio.sleep(5)

                # Wait before next check (configurable interval)
                enhancement_interval = getattr(
                    self.settings, "tls_enhancement_interval_minutes", 30
                )
                logger.info(
                    f"Waiting {enhancement_interval} minutes before next enhancement check"
                )

                # Wait in chunks so we can respond to stop requests
                for _ in range(enhancement_interval * 6):  # 10-second chunks
                    if not self.running:
                        break
                    await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error in TLS enhancement loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)

    async def _enhance_muppet_safely(self, muppet_name: str):
        """Safely enhance a muppet with error handling and history tracking."""
        try:
            logger.info(f"Auto-enhancing muppet: {muppet_name}")

            # Check if we've recently tried to enhance this muppet
            if self._recently_attempted(muppet_name):
                logger.info(f"Skipping {muppet_name} - recently attempted")
                return

            # Attempt enhancement
            result = await self.tls_enhancer.enhance_muppet_with_tls(muppet_name)

            # Record the attempt
            self._record_enhancement_attempt(muppet_name, result)

            if result["success"]:
                logger.info(f"Successfully auto-enhanced {muppet_name} with TLS")
                logger.info(f"HTTPS endpoint: {result.get('https_endpoint')}")

                # TODO: Send notification to muppet team
                await self._notify_enhancement_success(muppet_name, result)

            else:
                logger.warning(
                    f"Failed to auto-enhance {muppet_name}: {result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Error auto-enhancing muppet {muppet_name}: {e}")

            # Record the failed attempt
            self._record_enhancement_attempt(
                muppet_name,
                {"success": False, "error": str(e), "muppet_name": muppet_name},
            )

    def _recently_attempted(self, muppet_name: str) -> bool:
        """Check if we've recently attempted to enhance this muppet."""
        cutoff_time = datetime.now() - timedelta(hours=1)  # Don't retry within 1 hour

        for attempt in self.enhancement_history:
            if (
                attempt["muppet_name"] == muppet_name
                and attempt["timestamp"] > cutoff_time
            ):
                return True

        return False

    def _record_enhancement_attempt(self, muppet_name: str, result: Dict[str, Any]):
        """Record an enhancement attempt in history."""
        self.enhancement_history.append(
            {
                "muppet_name": muppet_name,
                "timestamp": datetime.now(),
                "success": result.get("success", False),
                "error": result.get("error"),
                "https_endpoint": result.get("https_endpoint"),
            }
        )

        # Keep only recent history (last 100 attempts)
        if len(self.enhancement_history) > 100:
            self.enhancement_history = self.enhancement_history[-100:]

    async def _notify_enhancement_success(
        self, muppet_name: str, result: Dict[str, Any]
    ):
        """Notify about successful TLS enhancement."""
        try:
            https_endpoint = result.get("https_endpoint")

            # Log the success
            logger.info(f"🔒 TLS Auto-Enhancement Success: {muppet_name}")
            logger.info(f"   HTTPS Endpoint: {https_endpoint}")
            logger.info(
                f"   Security Group Updated: {result.get('security_group_updated', False)}"
            )
            logger.info(
                f"   DNS Record Created: {result.get('dns_record_created', False)}"
            )
            logger.info(
                f"   HTTP Redirect Configured: {result.get('redirect_configured', False)}"
            )

            # TODO: Implement actual notifications
            # - GitHub issue comment
            # - Slack message
            # - Email notification
            # - Platform dashboard update

        except Exception as e:
            logger.warning(
                f"Failed to notify about enhancement success for {muppet_name}: {e}"
            )

    def get_enhancement_status(self) -> Dict[str, Any]:
        """Get the current status of the auto-enhancement service."""
        recent_attempts = [
            attempt
            for attempt in self.enhancement_history
            if attempt["timestamp"] > datetime.now() - timedelta(hours=24)
        ]

        successful_attempts = [a for a in recent_attempts if a["success"]]
        failed_attempts = [a for a in recent_attempts if not a["success"]]

        return {
            "running": self.running,
            "total_attempts_24h": len(recent_attempts),
            "successful_enhancements_24h": len(successful_attempts),
            "failed_attempts_24h": len(failed_attempts),
            "recent_successes": [
                {
                    "muppet_name": a["muppet_name"],
                    "timestamp": a["timestamp"].isoformat(),
                    "https_endpoint": a["https_endpoint"],
                }
                for a in successful_attempts[-5:]  # Last 5 successes
            ],
            "recent_failures": [
                {
                    "muppet_name": a["muppet_name"],
                    "timestamp": a["timestamp"].isoformat(),
                    "error": a["error"],
                }
                for a in failed_attempts[-5:]  # Last 5 failures
            ],
        }
