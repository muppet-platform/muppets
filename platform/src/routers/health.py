"""
Health check endpoints for the Muppet Platform.

This module provides health and readiness endpoints for monitoring
and load balancer health checks.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status, Request
from pydantic import BaseModel

from ..config import get_settings
from ..logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    service: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    status: str
    timestamp: datetime
    version: str
    service: str
    dependencies: Dict[str, str]


class PlatformHealthResponse(BaseModel):
    """Platform health response model."""

    status: str
    timestamp: datetime
    version: str
    service: str
    platform_metrics: Dict[str, Any]


@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Basic health check endpoint for load balancers",
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.

    Returns basic service information to indicate the service is running.
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version,
        service=settings.name,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Detailed readiness check including dependency status",
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint with dependency validation.

    Checks if the service is ready to handle requests by validating
    connections to external dependencies.
    """
    settings = get_settings()

    # TODO: Add actual dependency checks in future tasks
    # For now, return basic readiness status
    dependencies = {
        "github_api": "not_checked",
        "aws_services": "not_checked",
        "parameter_store": "not_checked",
    }

    logger.debug("Readiness check performed", extra={"dependencies": dependencies})

    return ReadinessResponse(
        status="ready",
        timestamp=datetime.utcnow(),
        version=settings.version,
        service=settings.name,
        dependencies=dependencies,
    )


@router.get(
    "/platform",
    response_model=PlatformHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Platform health check",
    description="Detailed platform health including muppet metrics",
)
async def platform_health_check(request: Request) -> PlatformHealthResponse:
    """
    Platform health check endpoint with muppet metrics.

    Returns detailed platform health information including muppet counts,
    status distribution, and overall platform health score.
    """
    settings = get_settings()

    try:
        # Get state manager from app state
        state_manager = request.app.state.state_manager

        # Get platform health metrics
        platform_metrics = await state_manager.get_platform_health()

        return PlatformHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version=settings.version,
            service=settings.name,
            platform_metrics=platform_metrics,
        )

    except Exception as e:
        logger.error(f"Platform health check failed: {e}")

        # Return degraded status if health check fails
        return PlatformHealthResponse(
            status="degraded",
            timestamp=datetime.utcnow(),
            version=settings.version,
            service=settings.name,
            platform_metrics={
                "error": str(e),
                "total_muppets": 0,
                "initialized": False,
            },
        )
