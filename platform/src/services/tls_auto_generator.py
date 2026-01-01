"""
TLS Auto-Generator Service

Automatically configures TLS for all muppets using the s3u.dev wildcard certificate.
Implements the "Simple by Default, Extensible by Choice" principle for TLS configuration.
"""

from typing import Any, Dict, Optional

import boto3
import httpx
from botocore.exceptions import ClientError, NoCredentialsError

from ..config import get_settings
from ..logging_config import get_logger

logger = get_logger(__name__)


class TLSAutoGenerator:
    """Automatically configures TLS for all muppets."""

    def __init__(self):
        """Initialize TLS auto-generator with AWS clients."""
        try:
            settings = get_settings()
            self.route53_client = boto3.client(
                "route53", region_name=settings.aws.region
            )
            self.acm_client = boto3.client("acm", region_name=settings.aws.region)
            self._s3u_dev_zone_id = None
            self._wildcard_cert_arn = None
            logger.info("TLS auto-generator initialized successfully")
        except NoCredentialsError:
            logger.error(
                "AWS credentials not found. TLS auto-generator will not function."
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize TLS auto-generator: {e}")
            raise

    @property
    def s3u_dev_zone_id(self) -> str:
        """Get the s3u.dev hosted zone ID (cached)."""
        if self._s3u_dev_zone_id is None:
            self._s3u_dev_zone_id = self._discover_s3u_dev_zone_id()
        return self._s3u_dev_zone_id

    @property
    def wildcard_cert_arn(self) -> str:
        """Get the wildcard certificate ARN (cached)."""
        if self._wildcard_cert_arn is None:
            self._wildcard_cert_arn = self._discover_wildcard_certificate_arn()
        return self._wildcard_cert_arn

    def generate_muppet_tls_config(self, muppet_name: str) -> Dict[str, Any]:
        """
        Generate complete TLS configuration for a muppet.

        Args:
            muppet_name: Name of the muppet

        Returns:
            Dictionary containing TLS configuration
        """
        try:
            config = {
                "enable_https": True,
                "certificate_arn": self.wildcard_cert_arn,
                "domain_name": f"{muppet_name}.s3u.dev",
                "zone_id": self.s3u_dev_zone_id,
                "redirect_http_to_https": True,
                "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
                "create_dns_record": True,
            }

            logger.info(f"Generated TLS configuration for muppet: {muppet_name}")
            logger.debug(f"TLS config: {config}")

            return config

        except Exception as e:
            logger.error(f"Failed to generate TLS config for muppet {muppet_name}: {e}")
            raise

    def _discover_s3u_dev_zone_id(self) -> str:
        """Discover the s3u.dev hosted zone ID."""
        try:
            logger.info("Discovering s3u.dev hosted zone ID...")
            response = self.route53_client.list_hosted_zones_by_name(DNSName="s3u.dev")

            for zone in response.get("HostedZones", []):
                if zone["Name"] == "s3u.dev.":
                    zone_id = zone["Id"].split("/")[-1]
                    logger.info(f"Found s3u.dev hosted zone: {zone_id}")
                    return zone_id

            raise ValueError("s3u.dev hosted zone not found")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                logger.error(
                    "Access denied when discovering s3u.dev zone. Check IAM permissions."
                )
            else:
                logger.error(f"AWS error discovering s3u.dev zone: {error_code}")
            raise RuntimeError(f"Failed to discover s3u.dev zone ID: {e}")
        except Exception as e:
            logger.error(f"Unexpected error discovering s3u.dev zone: {e}")
            raise RuntimeError(f"Failed to discover s3u.dev zone ID: {e}")

    def _discover_wildcard_certificate_arn(self) -> str:
        """Discover the wildcard certificate ARN."""
        try:
            logger.info("Discovering *.s3u.dev wildcard certificate ARN...")
            response = self.acm_client.list_certificates(CertificateStatuses=["ISSUED"])

            for cert in response.get("CertificateSummaryList", []):
                if cert["DomainName"] == "*.s3u.dev":
                    cert_arn = cert["CertificateArn"]
                    logger.info(f"Found wildcard certificate: {cert_arn}")
                    return cert_arn

            raise ValueError("*.s3u.dev certificate not found or not issued")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDenied":
                logger.error(
                    "Access denied when discovering wildcard certificate. Check IAM permissions."
                )
            else:
                logger.error(
                    f"AWS error discovering wildcard certificate: {error_code}"
                )
            raise RuntimeError(f"Failed to discover wildcard certificate ARN: {e}")
        except Exception as e:
            logger.error(f"Unexpected error discovering wildcard certificate: {e}")
            raise RuntimeError(f"Failed to discover wildcard certificate ARN: {e}")

    async def validate_tls_endpoint(self, muppet_name: str, timeout: int = 10) -> bool:
        """
        Validate that a muppet's HTTPS endpoint is working.

        Args:
            muppet_name: Name of the muppet
            timeout: Request timeout in seconds

        Returns:
            True if HTTPS endpoint is accessible, False otherwise
        """
        endpoint = f"https://{muppet_name}.s3u.dev/health"

        try:
            logger.info(f"Validating TLS endpoint: {endpoint}")

            async with httpx.AsyncClient(verify=True, timeout=timeout) as client:
                response = await client.get(endpoint)
                is_valid = response.status_code == 200

                if is_valid:
                    logger.info(f"TLS endpoint validation successful: {endpoint}")
                else:
                    logger.warning(
                        f"TLS endpoint returned status {response.status_code}: {endpoint}"
                    )

                return is_valid

        except httpx.TimeoutException:
            logger.warning(f"TLS endpoint validation timed out: {endpoint}")
            return False
        except httpx.ConnectError:
            logger.warning(f"TLS endpoint connection failed: {endpoint}")
            return False
        except Exception as e:
            # Catch all SSL/TLS related errors
            if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                logger.error(f"TLS/SSL error validating endpoint {endpoint}: {e}")
            else:
                logger.error(
                    f"Unexpected error validating TLS endpoint {endpoint}: {e}"
                )
            return False

    async def validate_http_redirect(self, muppet_name: str, timeout: int = 10) -> bool:
        """
        Validate that HTTP traffic is redirected to HTTPS.

        Args:
            muppet_name: Name of the muppet
            timeout: Request timeout in seconds

        Returns:
            True if HTTP redirects to HTTPS, False otherwise
        """
        http_endpoint = f"http://{muppet_name}.s3u.dev/health"

        try:
            logger.info(f"Validating HTTP redirect: {http_endpoint}")

            async with httpx.AsyncClient(
                follow_redirects=False, timeout=timeout
            ) as client:
                response = await client.get(http_endpoint)

                # Check for redirect status codes
                is_redirect = response.status_code in [301, 302, 307, 308]

                if is_redirect:
                    location = response.headers.get("location", "")
                    is_https_redirect = location.startswith("https://")

                    if is_https_redirect:
                        logger.info(
                            f"HTTP redirect validation successful: {http_endpoint} -> {location}"
                        )
                        return True
                    else:
                        logger.warning(
                            f"HTTP redirect not to HTTPS: {http_endpoint} -> {location}"
                        )
                        return False
                else:
                    logger.warning(
                        f"HTTP endpoint did not redirect (status {response.status_code}): {http_endpoint}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.warning(f"HTTP redirect validation timed out: {http_endpoint}")
            return False
        except httpx.ConnectError:
            logger.warning(f"HTTP redirect connection failed: {http_endpoint}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error validating HTTP redirect {http_endpoint}: {e}"
            )
            return False

    async def validate_certificate_details(self, muppet_name: str) -> Dict[str, Any]:
        """
        Get detailed certificate information for a muppet endpoint.

        Args:
            muppet_name: Name of the muppet

        Returns:
            Dictionary with certificate details
        """
        endpoint = f"https://{muppet_name}.s3u.dev"

        try:
            logger.info(f"Getting certificate details for: {endpoint}")

            async with httpx.AsyncClient(verify=True, timeout=10) as client:
                response = await client.get(endpoint)

                # Extract certificate information from the response
                # Note: httpx doesn't expose certificate details directly
                # This is a simplified implementation
                return {
                    "endpoint": endpoint,
                    "tls_version": "TLS 1.3",  # Assumed based on SSL policy
                    "certificate_valid": True,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                }

        except Exception as e:
            logger.error(f"Failed to get certificate details for {endpoint}: {e}")
            return {"endpoint": endpoint, "certificate_valid": False, "error": str(e)}

    async def get_certificate_details(self, certificate_arn: str) -> Dict[str, Any]:
        """Get detailed information about a certificate."""
        try:
            response = self.acm_client.describe_certificate(
                CertificateArn=certificate_arn
            )
            cert = response["Certificate"]

            return {
                "status": cert.get("Status"),
                "domain_name": cert.get("DomainName"),
                "subject_alternative_names": cert.get("SubjectAlternativeNames", []),
                "issued_at": (
                    cert.get("IssuedAt").isoformat() if cert.get("IssuedAt") else None
                ),
                "expires_at": (
                    cert.get("NotAfter").isoformat() if cert.get("NotAfter") else None
                ),
                "issuer": cert.get("Issuer"),
                "key_algorithm": cert.get("KeyAlgorithm"),
                "signature_algorithm": cert.get("SignatureAlgorithm"),
            }
        except Exception as e:
            logger.error(
                f"Failed to get certificate details for {certificate_arn}: {e}"
            )
            raise RuntimeError(f"Failed to get certificate details: {e}")

    def get_tls_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current TLS configuration.

        Returns:
            Dictionary with TLS configuration summary
        """
        try:
            return {
                "wildcard_certificate_arn": self.wildcard_cert_arn,
                "s3u_dev_zone_id": self.s3u_dev_zone_id,
                "domain_pattern": "*.s3u.dev",
                "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
                "tls_enabled_by_default": True,
                "http_redirect_enabled": True,
            }
        except Exception as e:
            logger.error(f"Failed to get TLS configuration summary: {e}")
            return {"error": str(e), "tls_enabled_by_default": False}
