"""
TLS Management API Router

Provides monitoring and validation endpoints for TLS configuration
across the Muppet Platform. TLS is enabled automatically through
terraform module defaults - no migration APIs needed.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import get_settings
from ..managers.github_manager import GitHubManager
from ..services.tls_auto_generator import TLSAutoGenerator
from ..state_manager import get_state_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tls", tags=["TLS Management"])


def validate_muppet_name(muppet_name: str) -> None:
    """Validate muppet name format and constraints."""
    if not muppet_name:
        raise HTTPException(status_code=400, detail="Muppet name cannot be empty")

    if len(muppet_name) > 50:
        raise HTTPException(
            status_code=400, detail="Muppet name too long (max 50 characters)"
        )

    if len(muppet_name) < 3:
        raise HTTPException(
            status_code=400, detail="Muppet name too short (min 3 characters)"
        )

    # Check for invalid characters (only allow alphanumeric, hyphens, and underscores)
    if not muppet_name.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail="Invalid muppet name (only alphanumeric, hyphens, and underscores allowed)",
        )


class TLSValidationResponse(BaseModel):
    """Response model for TLS validation."""

    muppet_name: str
    https_endpoint: str
    tls_valid: bool
    validated_at: str
    certificate_details: Optional[Dict[str, Any]] = None
    redirect_valid: Optional[bool] = None


class CertificateStatusResponse(BaseModel):
    """Response model for certificate status."""

    certificate_arn: str
    status: str
    domain: str
    issued_at: Optional[str] = None
    expires_at: Optional[str] = None
    subject_alternative_names: List[str] = []


class MuppetTLSStatusResponse(BaseModel):
    """Response model for individual muppet TLS status."""

    muppet_name: str
    tls_enabled: bool
    https_endpoint: Optional[str] = None
    tls_valid: Optional[bool] = None
    last_validated: Optional[str] = None


@router.get("/certificate/status", response_model=CertificateStatusResponse)
async def get_certificate_status():
    """Get wildcard certificate status and details."""
    try:
        tls_generator = TLSAutoGenerator()
        cert_arn = tls_generator.wildcard_cert_arn

        # Get certificate details from ACM
        cert_details = await tls_generator.get_certificate_details(cert_arn)

        return CertificateStatusResponse(
            certificate_arn=cert_arn,
            status=cert_details.get("status", "UNKNOWN"),
            domain=cert_details.get("domain_name", "*.s3u.dev"),
            issued_at=cert_details.get("issued_at"),
            expires_at=cert_details.get("expires_at"),
            subject_alternative_names=cert_details.get("subject_alternative_names", []),
        )
    except Exception as e:
        logger.error(f"Failed to get certificate status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get certificate status: {str(e)}"
        )


@router.get("/muppet/{muppet_name}/validate", response_model=TLSValidationResponse)
async def validate_muppet_tls(muppet_name: str):
    """Validate a muppet's TLS endpoint and configuration."""
    try:
        validate_muppet_name(muppet_name)

        tls_generator = TLSAutoGenerator()
        https_endpoint = f"https://{muppet_name}.s3u.dev"

        # Validate TLS endpoint
        is_valid = await tls_generator.validate_tls_endpoint(muppet_name)

        # Validate HTTP redirect
        redirect_valid = None
        certificate_details = None

        if is_valid:
            redirect_valid = await tls_generator.validate_http_redirect(muppet_name)
            certificate_details = await tls_generator.validate_certificate_details(
                muppet_name
            )

        return TLSValidationResponse(
            muppet_name=muppet_name,
            https_endpoint=https_endpoint,
            tls_valid=is_valid,
            validated_at=datetime.utcnow().isoformat(),
            certificate_details=certificate_details,
            redirect_valid=redirect_valid,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate TLS for muppet {muppet_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/muppets/status")
async def get_all_muppets_tls_status():
    """Get TLS status for all muppets in the organization."""
    try:
        settings = get_settings()
        github_manager = GitHubManager()
        tls_generator = TLSAutoGenerator()

        # Get all muppet repositories
        repositories = await github_manager.get_muppet_repositories()

        muppet_statuses = []

        for repo in repositories:
            muppet_name = repo["name"]

            try:
                # Check if muppet has TLS configuration
                # This is a simplified check - in reality, you might want to
                # check the muppet's terraform configuration or deployment status
                https_endpoint = f"https://{muppet_name}.s3u.dev"

                # Validate TLS endpoint
                tls_valid = await tls_generator.validate_tls_endpoint(muppet_name)

                status = MuppetTLSStatusResponse(
                    muppet_name=muppet_name,
                    tls_enabled=True,  # Assume TLS is enabled by default
                    https_endpoint=https_endpoint,
                    tls_valid=tls_valid,
                    last_validated=datetime.utcnow().isoformat(),
                )

            except Exception as e:
                logger.warning(f"Failed to check TLS status for {muppet_name}: {e}")
                status = MuppetTLSStatusResponse(
                    muppet_name=muppet_name,
                    tls_enabled=False,
                    tls_valid=False,
                    last_validated=datetime.utcnow().isoformat(),
                )

            muppet_statuses.append(status)

        # Generate summary statistics
        total_muppets = len(muppet_statuses)
        tls_enabled_count = sum(1 for status in muppet_statuses if status.tls_enabled)
        tls_valid_count = sum(1 for status in muppet_statuses if status.tls_valid)

        return {
            "summary": {
                "total_muppets": total_muppets,
                "tls_enabled": tls_enabled_count,
                "tls_valid": tls_valid_count,
                "tls_adoption_rate": (
                    f"{(tls_enabled_count / total_muppets * 100):.1f}%"
                    if total_muppets > 0
                    else "0%"
                ),
                "tls_success_rate": (
                    f"{(tls_valid_count / tls_enabled_count * 100):.1f}%"
                    if tls_enabled_count > 0
                    else "0%"
                ),
            },
            "muppets": [status.model_dump() for status in muppet_statuses],
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get TLS status for all muppets: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get TLS status: {str(e)}"
        )


@router.get("/configuration/summary")
async def get_tls_configuration_summary():
    """Get a summary of the TLS configuration for the platform."""
    try:
        tls_generator = TLSAutoGenerator()

        # Get TLS configuration summary
        summary = tls_generator.get_tls_configuration_summary()

        return {
            "platform_tls_config": summary,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get TLS configuration summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get configuration summary: {str(e)}"
        )
