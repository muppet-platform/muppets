"""
Webhook Router for GitHub Integration

Handles incoming webhooks from GitHub to automatically enhance muppets with TLS
when their CD workflows complete successfully.
"""

import hashlib
import hmac
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers

from ..config import get_settings
from ..logging_config import get_logger
from ..services.github_webhook_handler import GitHubWebhookHandler

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(request: Request) -> JSONResponse:
    """
    Handle GitHub webhook events for automatic TLS enhancement.

    This endpoint receives GitHub webhook events and automatically enhances
    muppets with TLS when their CD workflows complete successfully.
    """
    try:
        # Get the raw body and headers
        body = await request.body()
        headers = request.headers

        # Verify the webhook signature
        if not await _verify_github_signature(body, headers):
            logger.warning("Invalid GitHub webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        # Parse the JSON payload
        try:
            import json

            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload"
            )

        # Get the event type
        event_type = headers.get("x-github-event", "")

        logger.info(f"Received GitHub webhook: {event_type}")

        # Handle workflow_run events
        if event_type == "workflow_run":
            action = payload.get("action", "")

            if action == "completed":
                handler = GitHubWebhookHandler()
                result = await handler.handle_workflow_run_completed(payload)

                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "status": "processed",
                        "event_type": event_type,
                        "action": action,
                        "result": result,
                    },
                )
            else:
                logger.info(f"Ignoring workflow_run action: {action}")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "status": "ignored",
                        "event_type": event_type,
                        "action": action,
                        "reason": "Not a completed workflow",
                    },
                )
        else:
            logger.info(f"Ignoring GitHub event type: {event_type}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "ignored",
                    "event_type": event_type,
                    "reason": "Not a workflow_run event",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GitHub webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}",
        )


async def _verify_github_signature(body: bytes, headers: Headers) -> bool:
    """
    Verify the GitHub webhook signature.

    This ensures the webhook is actually from GitHub and hasn't been tampered with.
    """
    try:
        settings = get_settings()

        # Get the signature from headers
        signature_header = headers.get("x-hub-signature-256", "")
        if not signature_header.startswith("sha256="):
            logger.warning("Missing or invalid signature header")
            return False

        # Extract the signature
        signature = signature_header[7:]  # Remove "sha256=" prefix

        # Get the webhook secret
        webhook_secret = getattr(settings, "github_webhook_secret", None)
        if not webhook_secret:
            logger.warning(
                "GitHub webhook secret not configured - skipping signature verification"
            )
            return True  # Allow in development/testing

        # Calculate the expected signature
        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

        # Compare signatures
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("GitHub webhook signature mismatch")
            return False

        return True

    except Exception as e:
        logger.error(f"Error verifying GitHub webhook signature: {e}")
        return False


@router.get("/github/health")
async def github_webhook_health() -> Dict[str, Any]:
    """Health check endpoint for GitHub webhook integration."""
    return {
        "status": "healthy",
        "service": "github-webhook-handler",
        "features": [
            "workflow_run_completed",
            "automatic_tls_enhancement",
            "muppet_team_notifications",
        ],
    }
