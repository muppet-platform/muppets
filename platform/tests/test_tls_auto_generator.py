"""
Tests for TLS Auto-Generator Service

Tests the TLS configuration generation and validation functionality
with proper mocking of AWS services.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from src.services.tls_auto_generator import TLSAutoGenerator


class TestTLSAutoGenerator:
    """Test TLS Auto-Generator functionality."""

    @pytest.fixture
    def mock_route53_client(self):
        """Mock Route 53 client."""
        mock_client = Mock()
        mock_client.list_hosted_zones_by_name.return_value = {
            "HostedZones": [
                {
                    "Id": "/hostedzone/Z1234567890ABC",
                    "Name": "s3u.dev.",
                    "Config": {"PrivateZone": False},
                }
            ]
        }
        return mock_client

    @pytest.fixture
    def mock_acm_client(self):
        """Mock ACM client."""
        mock_client = Mock()
        mock_client.list_certificates.return_value = {
            "CertificateSummaryList": [
                {
                    "CertificateArn": "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012",
                    "DomainName": "*.s3u.dev",
                    "Status": "ISSUED",
                }
            ]
        }
        return mock_client

    @pytest.fixture
    def tls_generator(self, mock_route53_client, mock_acm_client):
        """Create TLS generator with mocked AWS clients."""
        with patch("boto3.client") as mock_boto3:

            def mock_client(service, **kwargs):
                if service == "route53":
                    return mock_route53_client
                elif service == "acm":
                    return mock_acm_client
                return Mock()

            mock_boto3.side_effect = mock_client
            return TLSAutoGenerator()

    def test_initialization_success(self, tls_generator):
        """Test successful TLS generator initialization."""
        assert tls_generator is not None
        assert tls_generator._s3u_dev_zone_id is None
        assert tls_generator._wildcard_cert_arn is None

    def test_initialization_no_credentials(self):
        """Test TLS generator initialization with no AWS credentials."""
        with patch("boto3.client", side_effect=NoCredentialsError()):
            with pytest.raises(NoCredentialsError):
                TLSAutoGenerator()

    def test_s3u_dev_zone_id_discovery(self, tls_generator):
        """Test s3u.dev zone ID discovery."""
        zone_id = tls_generator.s3u_dev_zone_id
        assert zone_id == "Z1234567890ABC"

        # Test caching - should not call AWS again
        zone_id_cached = tls_generator.s3u_dev_zone_id
        assert zone_id_cached == "Z1234567890ABC"
        assert tls_generator.route53_client.list_hosted_zones_by_name.call_count == 1

    def test_s3u_dev_zone_id_not_found(self, tls_generator):
        """Test s3u.dev zone ID discovery when zone not found."""
        tls_generator.route53_client.list_hosted_zones_by_name.return_value = {
            "HostedZones": []
        }

        with pytest.raises(RuntimeError, match="Failed to discover s3u.dev zone ID"):
            _ = tls_generator.s3u_dev_zone_id

    def test_s3u_dev_zone_id_access_denied(self, tls_generator):
        """Test s3u.dev zone ID discovery with access denied."""
        error = ClientError(
            error_response={
                "Error": {"Code": "AccessDenied", "Message": "Access denied"}
            },
            operation_name="ListHostedZonesByName",
        )
        tls_generator.route53_client.list_hosted_zones_by_name.side_effect = error

        with pytest.raises(RuntimeError, match="Failed to discover s3u.dev zone ID"):
            _ = tls_generator.s3u_dev_zone_id

    def test_wildcard_certificate_discovery(self, tls_generator):
        """Test wildcard certificate ARN discovery."""
        cert_arn = tls_generator.wildcard_cert_arn
        expected_arn = "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
        assert cert_arn == expected_arn

        # Test caching - should not call AWS again
        cert_arn_cached = tls_generator.wildcard_cert_arn
        assert cert_arn_cached == expected_arn
        assert tls_generator.acm_client.list_certificates.call_count == 1

    def test_wildcard_certificate_not_found(self, tls_generator):
        """Test wildcard certificate discovery when certificate not found."""
        tls_generator.acm_client.list_certificates.return_value = {
            "CertificateSummaryList": []
        }

        with pytest.raises(
            RuntimeError, match="Failed to discover wildcard certificate ARN"
        ):
            _ = tls_generator.wildcard_cert_arn

    def test_wildcard_certificate_access_denied(self, tls_generator):
        """Test wildcard certificate discovery with access denied."""
        error = ClientError(
            error_response={
                "Error": {"Code": "AccessDenied", "Message": "Access denied"}
            },
            operation_name="ListCertificates",
        )
        tls_generator.acm_client.list_certificates.side_effect = error

        with pytest.raises(
            RuntimeError, match="Failed to discover wildcard certificate ARN"
        ):
            _ = tls_generator.wildcard_cert_arn

    def test_generate_muppet_tls_config(self, tls_generator):
        """Test TLS configuration generation for a muppet."""
        config = tls_generator.generate_muppet_tls_config("test-muppet")

        expected_config = {
            "enable_https": True,
            "certificate_arn": "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012",
            "domain_name": "test-muppet.s3u.dev",
            "zone_id": "Z1234567890ABC",
            "redirect_http_to_https": True,
            "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
            "create_dns_record": True,
        }

        assert config == expected_config

    def test_generate_muppet_tls_config_with_special_characters(self, tls_generator):
        """Test TLS configuration generation with special characters in muppet name."""
        config = tls_generator.generate_muppet_tls_config("my-test-muppet-123")

        assert config["domain_name"] == "my-test-muppet-123.s3u.dev"
        assert config["enable_https"] is True

    @pytest.mark.asyncio
    async def test_validate_tls_endpoint_success(self, tls_generator):
        """Test successful TLS endpoint validation."""
        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await tls_generator.validate_tls_endpoint("test-muppet")
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_tls_endpoint_failure(self, tls_generator):
        """Test TLS endpoint validation failure."""
        mock_response = Mock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await tls_generator.validate_tls_endpoint("test-muppet")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_tls_endpoint_timeout(self, tls_generator):
        """Test TLS endpoint validation timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )

            result = await tls_generator.validate_tls_endpoint("test-muppet")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_tls_endpoint_ssl_error(self, tls_generator):
        """Test TLS endpoint validation SSL error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("SSL certificate verification failed")
            )

            result = await tls_generator.validate_tls_endpoint("test-muppet")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_http_redirect_success(self, tls_generator):
        """Test successful HTTP redirect validation."""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_response.headers = {"location": "https://test-muppet.s3u.dev/health"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await tls_generator.validate_http_redirect("test-muppet")
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_http_redirect_no_redirect(self, tls_generator):
        """Test HTTP redirect validation when no redirect occurs."""
        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await tls_generator.validate_http_redirect("test-muppet")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_http_redirect_wrong_protocol(self, tls_generator):
        """Test HTTP redirect validation when redirecting to wrong protocol."""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_response.headers = {"location": "http://test-muppet.s3u.dev/health"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await tls_generator.validate_http_redirect("test-muppet")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_certificate_details_success(self, tls_generator):
        """Test certificate details validation success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await tls_generator.validate_certificate_details("test-muppet")

            assert result["endpoint"] == "https://test-muppet.s3u.dev"
            assert result["certificate_valid"] is True
            assert result["status_code"] == 200
            assert result["response_time_ms"] == 500.0

    @pytest.mark.asyncio
    async def test_validate_certificate_details_failure(self, tls_generator):
        """Test certificate details validation failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Certificate verification failed")
            )

            result = await tls_generator.validate_certificate_details("test-muppet")

            assert result["endpoint"] == "https://test-muppet.s3u.dev"
            assert result["certificate_valid"] is False
            assert "error" in result

    def test_get_tls_configuration_summary(self, tls_generator):
        """Test TLS configuration summary."""
        summary = tls_generator.get_tls_configuration_summary()

        expected_summary = {
            "wildcard_certificate_arn": "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012",
            "s3u_dev_zone_id": "Z1234567890ABC",
            "domain_pattern": "*.s3u.dev",
            "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
            "tls_enabled_by_default": True,
            "http_redirect_enabled": True,
        }

        assert summary == expected_summary

    def test_get_tls_configuration_summary_error(self, tls_generator):
        """Test TLS configuration summary with error."""
        # Force an error by making zone discovery fail
        tls_generator.route53_client.list_hosted_zones_by_name.side_effect = Exception(
            "AWS error"
        )

        summary = tls_generator.get_tls_configuration_summary()

        assert "error" in summary
        assert summary["tls_enabled_by_default"] is False


class TestTLSAutoGeneratorIntegration:
    """Integration tests for TLS Auto-Generator."""

    @pytest.fixture
    def tls_generator_with_real_clients(self):
        """Create TLS generator with real AWS clients (mocked at boto3 level)."""
        with patch("boto3.client") as mock_boto3:
            # Mock both clients to return the same mock
            mock_client = Mock()
            mock_boto3.return_value = mock_client

            # Set up Route 53 responses
            mock_client.list_hosted_zones_by_name.return_value = {
                "HostedZones": [
                    {
                        "Id": "/hostedzone/Z1234567890ABC",
                        "Name": "s3u.dev.",
                        "Config": {"PrivateZone": False},
                    }
                ]
            }

            # Set up ACM responses
            mock_client.list_certificates.return_value = {
                "CertificateSummaryList": [
                    {
                        "CertificateArn": "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012",
                        "DomainName": "*.s3u.dev",
                        "Status": "ISSUED",
                    }
                ]
            }

            return TLSAutoGenerator()

    def test_end_to_end_tls_config_generation(self, tls_generator_with_real_clients):
        """Test end-to-end TLS configuration generation."""
        generator = tls_generator_with_real_clients

        # Generate configuration
        config = generator.generate_muppet_tls_config("integration-test-muppet")

        # Verify all required fields are present
        required_fields = [
            "enable_https",
            "certificate_arn",
            "domain_name",
            "zone_id",
            "redirect_http_to_https",
            "ssl_policy",
            "create_dns_record",
        ]

        for field in required_fields:
            assert field in config

        # Verify values are correct
        assert config["enable_https"] is True
        assert config["domain_name"] == "integration-test-muppet.s3u.dev"
        assert config["ssl_policy"] == "ELBSecurityPolicy-TLS13-1-2-2021-06"
        assert config["redirect_http_to_https"] is True
        assert config["create_dns_record"] is True

    @pytest.mark.asyncio
    async def test_full_tls_validation_workflow(self, tls_generator_with_real_clients):
        """Test full TLS validation workflow."""
        generator = tls_generator_with_real_clients
        muppet_name = "validation-test-muppet"

        # Mock HTTP responses for validation
        mock_https_response = Mock()
        mock_https_response.status_code = 200
        mock_https_response.elapsed.total_seconds.return_value = 0.3

        mock_http_response = Mock()
        mock_http_response.status_code = 301
        mock_http_response.headers = {
            "location": f"https://{muppet_name}.s3u.dev/health"
        }

        with patch("httpx.AsyncClient") as mock_client:
            async_client = mock_client.return_value.__aenter__.return_value

            # Set up different responses for different URLs
            async def mock_get(url, **kwargs):
                if url.startswith("https://"):
                    return mock_https_response
                else:
                    return mock_http_response

            async_client.get = mock_get

            # Test HTTPS endpoint validation
            https_valid = await generator.validate_tls_endpoint(muppet_name)
            assert https_valid is True

            # Test HTTP redirect validation
            redirect_valid = await generator.validate_http_redirect(muppet_name)
            assert redirect_valid is True

            # Test certificate details
            cert_details = await generator.validate_certificate_details(muppet_name)
            assert cert_details["certificate_valid"] is True
            assert cert_details["status_code"] == 200
