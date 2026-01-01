"""
Tests for TLS Management API Router

Tests the TLS monitoring and validation endpoints.
Migration is handled automatically through terraform modules.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.services.tls_auto_generator import TLSAutoGenerator


class TestTLSRouter:
    """Test TLS monitoring and validation API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_tls_generator(self):
        """Mock TLS auto-generator."""
        mock = Mock(spec=TLSAutoGenerator)
        mock.wildcard_cert_arn = (
            "arn:aws:acm:us-west-2:123456789012:certificate/test-cert-id"
        )
        mock.s3u_dev_zone_id = "Z1234567890ABC"
        return mock

    @pytest.fixture
    def mock_github_manager(self):
        """Mock GitHub manager."""
        return AsyncMock()

    def test_get_certificate_status_success(self, client, mock_tls_generator):
        """Test successful certificate status retrieval."""
        mock_cert_details = {
            "status": "ISSUED",
            "domain_name": "*.s3u.dev",
            "issued_at": "2024-01-01T00:00:00",
            "expires_at": "2025-01-01T00:00:00",
            "subject_alternative_names": ["*.s3u.dev", "s3u.dev"],
        }
        mock_tls_generator.get_certificate_details.return_value = mock_cert_details

        with patch(
            "src.routers.tls_router.TLSAutoGenerator", return_value=mock_tls_generator
        ):
            response = client.get("/api/v1/tls/certificate/status")

        assert response.status_code == 200
        data = response.json()
        assert data["certificate_arn"] == mock_tls_generator.wildcard_cert_arn
        assert data["status"] == "ISSUED"
        assert data["domain"] == "*.s3u.dev"

    def test_get_certificate_status_failure(self, client):
        """Test certificate status retrieval failure."""
        with patch("src.routers.tls_router.TLSAutoGenerator") as mock_class:
            mock_class.side_effect = Exception("AWS error")
            response = client.get("/api/v1/tls/certificate/status")

        assert response.status_code == 500
        assert "Failed to get certificate status" in response.json()["message"]

    def test_validate_muppet_tls_success(self, client, mock_tls_generator):
        """Test successful muppet TLS validation."""
        mock_tls_generator.validate_tls_endpoint.return_value = True
        mock_tls_generator.validate_http_redirect.return_value = True
        mock_tls_generator.validate_certificate_details.return_value = {
            "endpoint": "https://test-muppet.s3u.dev",
            "certificate_valid": True,
            "tls_version": "TLS 1.3",
        }

        with patch(
            "src.routers.tls_router.TLSAutoGenerator", return_value=mock_tls_generator
        ):
            response = client.get("/api/v1/tls/muppet/test-muppet/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["muppet_name"] == "test-muppet"
        assert data["tls_valid"] is True
        assert data["redirect_valid"] is True
        assert "https://test-muppet.s3u.dev" in data["https_endpoint"]

    def test_validate_muppet_tls_invalid_name(self, client):
        """Test muppet TLS validation with invalid name."""
        response = client.get("/api/v1/tls/muppet/invalid@name/validate")

        assert response.status_code == 400
        assert "Invalid muppet name" in response.json()["message"]

    def test_validate_muppet_tls_failure(self, client, mock_tls_generator):
        """Test muppet TLS validation failure."""
        mock_tls_generator.validate_tls_endpoint.return_value = False
        mock_tls_generator.validate_http_redirect.return_value = False
        mock_tls_generator.validate_certificate_details.return_value = None

        with patch(
            "src.routers.tls_router.TLSAutoGenerator", return_value=mock_tls_generator
        ):
            response = client.get("/api/v1/tls/muppet/test-muppet/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["muppet_name"] == "test-muppet"
        assert data["tls_valid"] is False
        assert data["redirect_valid"] is None  # Not checked when TLS is invalid
        assert data["certificate_details"] is None

    def test_get_all_muppets_tls_status_success(
        self, client, mock_github_manager, mock_tls_generator
    ):
        """Test successful retrieval of all muppets TLS status."""
        mock_repositories = [{"name": "test-muppet-1"}, {"name": "test-muppet-2"}]
        mock_github_manager.get_muppet_repositories.return_value = mock_repositories
        mock_tls_generator.validate_tls_endpoint.side_effect = [True, False]

        with (
            patch(
                "src.routers.tls_router.GitHubManager", return_value=mock_github_manager
            ),
            patch(
                "src.routers.tls_router.TLSAutoGenerator",
                return_value=mock_tls_generator,
            ),
        ):
            response = client.get("/api/v1/tls/muppets/status")

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "muppets" in data
        assert data["summary"]["total_muppets"] == 2
        assert data["summary"]["tls_enabled"] == 2
        assert data["summary"]["tls_valid"] == 1

    def test_get_tls_configuration_summary_success(self, client, mock_tls_generator):
        """Test successful TLS configuration summary retrieval."""
        mock_summary = {
            "wildcard_certificate_arn": "arn:aws:acm:us-west-2:123456789012:certificate/test-cert-id",
            "s3u_dev_zone_id": "Z1234567890ABC",
            "domain_pattern": "*.s3u.dev",
            "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
            "tls_enabled_by_default": True,
        }
        mock_tls_generator.get_tls_configuration_summary.return_value = mock_summary

        with patch(
            "src.routers.tls_router.TLSAutoGenerator", return_value=mock_tls_generator
        ):
            response = client.get("/api/v1/tls/configuration/summary")

        assert response.status_code == 200
        data = response.json()
        assert "platform_tls_config" in data
        assert data["platform_tls_config"]["tls_enabled_by_default"] is True


class TestTLSRouterIntegration:
    """Integration tests for TLS router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    def test_tls_endpoints_are_registered(self, client):
        """Test that all TLS endpoints are properly registered."""
        # Test that endpoints exist (even if they fail due to missing AWS credentials)
        endpoints = [
            "/api/v1/tls/certificate/status",
            "/api/v1/tls/muppets/status",
            "/api/v1/tls/configuration/summary",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404

    def test_tls_validation_endpoints_exist(self, client):
        """Test that TLS validation endpoints exist."""
        # Test GET endpoints exist
        endpoints = [
            "/api/v1/tls/muppet/test/validate",
            "/api/v1/tls/certificate/status",
            "/api/v1/tls/muppets/status",
            "/api/v1/tls/configuration/summary",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code != 404


class TestTLSRouterErrorHandling:
    """Test error handling in TLS router."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)

    def test_invalid_muppet_names_rejected(self, client):
        """Test that invalid muppet names are properly rejected."""
        # Test names that will reach our validation logic
        test_cases = [
            ("invalid@name", "Invalid muppet name"),
            ("invalid.name", "Invalid muppet name"),
            ("a" * 100, "Muppet name too long"),  # Too long
            ("ab", "Muppet name too short"),  # Too short
        ]

        for invalid_name, expected_error in test_cases:
            # Test validation endpoint
            response = client.get(f"/api/v1/tls/muppet/{invalid_name}/validate")
            assert response.status_code == 400
            assert expected_error in response.json()["message"]

    def test_aws_service_errors_handled(self, client):
        """Test that AWS service errors are properly handled."""
        with patch("src.routers.tls_router.TLSAutoGenerator") as mock_class:
            mock_class.side_effect = Exception("AWS service unavailable")

            response = client.get("/api/v1/tls/certificate/status")
            assert response.status_code == 500
            assert "Failed to get certificate status" in response.json()["message"]
