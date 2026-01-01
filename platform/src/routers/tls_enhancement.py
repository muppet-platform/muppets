"""
TLS Enhancement API Router

Provides endpoints for automatically enhancing existing muppets with TLS.
Implements the "Zero Breaking Changes" principle from the TLS-by-default design.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..logging_config import get_logger
from ..services.muppet_tls_enhancer import MuppetTLSEnhancer
from ..services.tls_auto_generator import TLSAutoGenerator

logger = get_logger(__name__)

router = APIRouter(prefix="/tls", tags=["TLS Enhancement"])


class TLSEnhancementRequest(BaseModel):
    """Request model for TLS enhancement."""

    muppet_name: str


class TLSEnhancementResponse(BaseModel):
    """Response model for TLS enhancement."""

    success: bool
    muppet_name: str
    https_endpoint: str | None = None
    http_endpoint: str | None = None
    error: str | None = None


@router.post("/enhance/{muppet_name}", response_model=TLSEnhancementResponse)
async def enhance_muppet_with_tls(muppet_name: str) -> TLSEnhancementResponse:
    """
    Enhance a specific muppet with TLS configuration.

    This endpoint automatically:
    1. Discovers the existing ALB for the muppet
    2. Checks if the muppet uses the new terraform module approach
    3. Adds HTTPS listener with wildcard certificate (if compatible)
    4. Creates DNS record pointing to the ALB
    5. Configures HTTP→HTTPS redirect

    For muppets using the old terraform approach, provides migration guidance.
    """
    try:
        logger.info(f"TLS enhancement requested for muppet: {muppet_name}")

        enhancer = MuppetTLSEnhancer()
        result = await enhancer.enhance_muppet_with_tls(muppet_name)

        if result["success"]:
            logger.info(f"TLS enhancement successful for muppet: {muppet_name}")
            return TLSEnhancementResponse(
                success=True,
                muppet_name=muppet_name,
                https_endpoint=result.get("https_endpoint"),
                http_endpoint=result.get("http_endpoint"),
            )
        else:
            # Check if this is a migration issue
            if result.get("migration_required"):
                logger.info(
                    f"Muppet {muppet_name} requires terraform migration for TLS support"
                )
                error_msg = f"Terraform migration required. {result.get('error', '')}"
            else:
                error_msg = result.get("error", "Unknown error")

            logger.error(
                f"TLS enhancement failed for muppet {muppet_name}: {error_msg}"
            )
            return TLSEnhancementResponse(
                success=False, muppet_name=muppet_name, error=error_msg
            )

    except Exception as e:
        logger.error(f"Unexpected error enhancing muppet {muppet_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance muppet with TLS: {str(e)}",
        )


@router.post("/enhance-all")
async def enhance_all_muppets() -> Dict[str, Any]:
    """
    Enhance all discovered muppets with TLS configuration.

    This endpoint automatically discovers all muppets and enhances them with TLS.
    Perfect for bulk migration to TLS-by-default.
    """
    try:
        logger.info("Bulk TLS enhancement requested for all muppets")

        enhancer = MuppetTLSEnhancer()
        result = await enhancer.enhance_all_muppets()

        logger.info(f"Bulk TLS enhancement completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Unexpected error during bulk TLS enhancement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance all muppets with TLS: {str(e)}",
        )


@router.get("/discover")
async def discover_muppets_needing_enhancement() -> Dict[str, Any]:
    """
    Discover all muppets that could benefit from TLS enhancement.

    Returns a list of muppets with their current TLS status.
    """
    try:
        logger.info("Discovering muppets needing TLS enhancement")

        enhancer = MuppetTLSEnhancer()
        muppets = await enhancer.list_muppets_needing_tls_enhancement()

        return {
            "success": True,
            "total_muppets": len(muppets),
            "muppets_needing_enhancement": sum(
                1 for m in muppets if m["needs_enhancement"]
            ),
            "muppets": muppets,
        }

    except Exception as e:
        logger.error(f"Error discovering muppets needing TLS enhancement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover muppets: {str(e)}",
        )


@router.get("/config")
async def get_tls_configuration() -> Dict[str, Any]:
    """
    Get the current TLS configuration summary.

    Returns information about the wildcard certificate and DNS configuration.
    """
    try:
        logger.info("TLS configuration summary requested")

        tls_generator = TLSAutoGenerator()
        config = tls_generator.get_tls_configuration_summary()

        return {"success": True, "config": config}

    except Exception as e:
        logger.error(f"Error getting TLS configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get TLS configuration: {str(e)}",
        )


@router.get("/migration-guidance/{muppet_name}")
async def get_migration_guidance(muppet_name: str) -> Dict[str, Any]:
    """
    Get detailed migration guidance for a specific muppet.

    Analyzes the muppet's current terraform approach and provides
    step-by-step instructions for migrating to TLS-by-default.
    """
    try:
        logger.info(f"Migration guidance requested for muppet: {muppet_name}")

        enhancer = MuppetTLSEnhancer()

        # Discover the muppet's current state
        alb_info = await enhancer._discover_muppet_alb(muppet_name)
        if not alb_info:
            return {
                "success": False,
                "error": f"No ALB found for muppet: {muppet_name}",
                "muppet_name": muppet_name,
            }

        # Detect terraform approach
        terraform_approach = await enhancer._detect_terraform_approach(alb_info)

        # Check current TLS status
        listeners = enhancer.elbv2_client.describe_listeners(
            LoadBalancerArn=alb_info["arn"]
        )

        has_https = any(
            listener["Protocol"] == "HTTPS"
            for listener in listeners.get("Listeners", [])
        )

        # Generate guidance based on current state
        if terraform_approach == "new" and has_https:
            guidance = {
                "status": "already_compliant",
                "message": "This muppet already uses the new terraform module approach with TLS enabled",
                "current_state": {
                    "terraform_approach": "new",
                    "has_https": True,
                    "https_endpoint": f"https://{muppet_name}.s3u.dev",
                },
                "next_steps": [
                    "No action required - muppet is already TLS-enabled",
                    "Verify HTTPS endpoint is accessible",
                    "Update documentation to reference HTTPS endpoint",
                ],
            }
        elif terraform_approach == "new" and not has_https:
            guidance = {
                "status": "needs_tls_enablement",
                "message": "This muppet uses the new terraform approach but TLS is not enabled",
                "current_state": {"terraform_approach": "new", "has_https": False},
                "next_steps": [
                    "Update terraform configuration to set enable_https = true",
                    "Set certificate_arn, domain_name, and zone_id variables",
                    "Re-run CD pipeline to apply TLS configuration",
                    "Verify HTTPS endpoint becomes accessible",
                ],
                "terraform_changes": {
                    "enable_https": True,
                    "certificate_arn": "arn:aws:acm:us-west-2:ACCOUNT:certificate/CERT-ID",
                    "domain_name": f"{muppet_name}.s3u.dev",
                    "zone_id": "Z1234567890ABC",
                    "create_dns_record": True,
                    "redirect_http_to_https": True,
                },
            }
        else:  # terraform_approach == "old"
            guidance = {
                "status": "needs_terraform_migration",
                "message": "This muppet uses the old terraform approach and needs migration",
                "current_state": {
                    "terraform_approach": "old",
                    "has_https": has_https,
                    "security_groups_compatible": False,
                },
                "migration_steps": [
                    "1. Update terraform configuration to use terraform-modules/muppet-java-micronaut",
                    "2. Replace direct resource definitions with module call",
                    "3. Configure TLS variables in module call",
                    "4. Plan and apply terraform changes",
                    "5. Verify HTTPS endpoint accessibility",
                    "6. Update CI/CD and documentation",
                ],
                "benefits": [
                    "Automatic TLS certificate management",
                    "Built-in HTTPS security group rules",
                    "HTTP→HTTPS redirect configuration",
                    "DNS record management",
                    "Future-proof infrastructure",
                    "Consistent with platform standards",
                ],
                "terraform_example": {
                    "old_approach": "Direct resource definitions in main.tf",
                    "new_approach": "Module call with TLS configuration",
                    "module_source": "git::https://github.com/muppet-platform/muppets.git//terraform-modules/muppet-java-micronaut?ref=main",
                },
            }

        return {"success": True, "muppet_name": muppet_name, "guidance": guidance}

    except Exception as e:
        logger.error(f"Error getting migration guidance for muppet {muppet_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get migration guidance: {str(e)}",
        )


@router.get("/auto-enhancement/status")
async def get_auto_enhancement_status() -> Dict[str, Any]:
    """
    Get the status of the automatic TLS enhancement service.

    Shows statistics about recent enhancement attempts and current service status.
    """
    try:
        from fastapi import Request

        from ..services.tls_auto_enhancement_service import TLSAutoEnhancementService

        # This is a bit of a hack to get the service instance
        # In a real implementation, you'd inject this properly
        enhancer = MuppetTLSEnhancer()

        # Get current muppets status
        muppets = await enhancer.list_muppets_needing_tls_enhancement()

        return {
            "service_status": "running",  # TODO: Get actual status from app.state
            "discovery": {
                "total_muppets": len(muppets),
                "needs_enhancement": sum(1 for m in muppets if m["needs_enhancement"]),
                "already_enhanced": sum(
                    1 for m in muppets if not m["needs_enhancement"]
                ),
            },
            "muppets_needing_enhancement": [
                {
                    "muppet_name": m["muppet_name"],
                    "alb_dns": m["alb_dns"],
                    "terraform_approach": m["terraform_approach"],
                }
                for m in muppets
                if m["needs_enhancement"]
            ],
        }

    except Exception as e:
        logger.error(f"Error getting auto-enhancement status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auto-enhancement status: {str(e)}",
        )


@router.get("/validate/{muppet_name}")
async def validate_muppet_tls(muppet_name: str) -> Dict[str, Any]:
    """
    Validate TLS configuration for a specific muppet.

    Tests HTTPS endpoint accessibility and HTTP→HTTPS redirect.
    """
    try:
        logger.info(f"TLS validation requested for muppet: {muppet_name}")

        tls_generator = TLSAutoGenerator()

        # Test HTTPS endpoint
        https_valid = await tls_generator.validate_tls_endpoint(muppet_name)

        # Test HTTP redirect
        redirect_valid = await tls_generator.validate_http_redirect(muppet_name)

        # Get certificate details
        cert_details = await tls_generator.validate_certificate_details(muppet_name)

        return {
            "success": True,
            "muppet_name": muppet_name,
            "https_endpoint_valid": https_valid,
            "http_redirect_valid": redirect_valid,
            "certificate_details": cert_details,
            "overall_status": "valid" if https_valid and redirect_valid else "invalid",
        }

    except Exception as e:
        logger.error(f"Error validating TLS for muppet {muppet_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate TLS for muppet: {str(e)}",
        )
