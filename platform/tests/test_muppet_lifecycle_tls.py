"""
Tests for Muppet Lifecycle Service TLS Integration

Tests the TLS-by-default functionality in the muppet lifecycle service.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.services.muppet_lifecycle_service import MuppetLifecycleService
from src.services.tls_auto_generator import TLSAutoGenerator


class TestMuppetLifecycleTLSIntegration:
    """Test TLS integration in Muppet Lifecycle Service."""

    @pytest.fixture
    def mock_tls_generator(self):
        """Mock TLS auto-generator."""
        mock_generator = Mock(spec=TLSAutoGenerator)
        mock_generator.generate_muppet_tls_config.return_value = {
            "enable_https": True,
            "certificate_arn": "arn:aws:acm:us-west-2:123456789012:certificate/test-cert",
            "domain_name": "test-muppet.s3u.dev",
            "zone_id": "Z1234567890ABC",
            "redirect_http_to_https": True,
            "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
            "create_dns_record": True,
        }
        return mock_generator

    @pytest.fixture
    def lifecycle_service(self, mock_tls_generator):
        """Create lifecycle service with mocked TLS generator."""
        # Create mock instances that can be used as constructor arguments
        mock_github_client = Mock()
        mock_steering_manager = Mock()
        mock_state_manager = Mock()

        with (
            patch.multiple(
                "src.services.muppet_lifecycle_service",
                TemplateManager=Mock,
                GitHubManager=Mock,
                InfrastructureManager=Mock,
                DeploymentService=Mock,
                get_state_manager=Mock(return_value=mock_state_manager),
                get_settings=Mock,
            ),
            patch(
                "src.services.muppet_lifecycle_service.GitHubClient",
                return_value=mock_github_client,
            ),
            patch(
                "src.services.muppet_lifecycle_service.SteeringManager",
                return_value=mock_steering_manager,
            ),
        ):
            service = MuppetLifecycleService(tls_generator=mock_tls_generator)
            # Manually set the state manager for test access
            service.state_manager = mock_state_manager
            return service

    def test_initialization_with_tls_generator(self, mock_tls_generator):
        """Test lifecycle service initialization with TLS generator."""
        # Create mock instances that can be used as constructor arguments
        mock_github_client = Mock()
        mock_steering_manager = Mock()
        mock_state_manager = Mock()

        with (
            patch.multiple(
                "src.services.muppet_lifecycle_service",
                TemplateManager=Mock,
                GitHubManager=Mock,
                InfrastructureManager=Mock,
                DeploymentService=Mock,
                get_state_manager=Mock(return_value=mock_state_manager),
                get_settings=Mock,
            ),
            patch(
                "src.services.muppet_lifecycle_service.GitHubClient",
                return_value=mock_github_client,
            ),
            patch(
                "src.services.muppet_lifecycle_service.SteeringManager",
                return_value=mock_steering_manager,
            ),
        ):
            service = MuppetLifecycleService(tls_generator=mock_tls_generator)
            assert service.tls_generator is mock_tls_generator

    def test_initialization_with_default_tls_generator(self):
        """Test lifecycle service initialization with default TLS generator."""
        # Create mock instances that can be used as constructor arguments
        mock_github_client = Mock()
        mock_steering_manager = Mock()
        mock_state_manager = Mock()

        with (
            patch(
                "src.services.muppet_lifecycle_service.TLSAutoGenerator"
            ) as mock_tls_generator,
            patch.multiple(
                "src.services.muppet_lifecycle_service",
                TemplateManager=Mock,
                GitHubManager=Mock,
                InfrastructureManager=Mock,
                DeploymentService=Mock,
                get_state_manager=Mock(return_value=mock_state_manager),
                get_settings=Mock,
            ),
            patch(
                "src.services.muppet_lifecycle_service.GitHubClient",
                return_value=mock_github_client,
            ),
            patch(
                "src.services.muppet_lifecycle_service.SteeringManager",
                return_value=mock_steering_manager,
            ),
        ):
            service = MuppetLifecycleService()
            assert service.tls_generator is not None
            mock_tls_generator.assert_called_once()

    def test_generate_muppet_tls_config(self, lifecycle_service, mock_tls_generator):
        """Test TLS configuration generation."""
        config = mock_tls_generator.generate_muppet_tls_config("test-muppet")

        assert config["enable_https"] is True
        assert config["domain_name"] == "test-muppet.s3u.dev"
        assert config["ssl_policy"] == "ELBSecurityPolicy-TLS13-1-2-2021-06"
        assert config["redirect_http_to_https"] is True

    @pytest.mark.asyncio
    async def test_migrate_existing_muppet_to_tls(
        self, lifecycle_service, mock_tls_generator
    ):
        """Test migrating existing muppet to TLS."""
        # Mock state manager to return a muppet
        mock_muppet = Mock()
        mock_muppet.name = "existing-muppet"
        lifecycle_service.state_manager.get_muppet = AsyncMock(return_value=mock_muppet)

        # Test migration
        result = await lifecycle_service.migrate_existing_muppet_to_tls(
            "existing-muppet"
        )

        # Verify result
        assert result["success"] is True
        assert result["muppet_name"] == "existing-muppet"
        assert result["https_endpoint"] == "https://existing-muppet.s3u.dev"
        assert "tls_config" in result
        assert "migration_instructions" in result

        # Verify TLS generator was called
        mock_tls_generator.generate_muppet_tls_config.assert_called_once_with(
            "existing-muppet"
        )

    @pytest.mark.asyncio
    async def test_migrate_nonexistent_muppet_to_tls(self, lifecycle_service):
        """Test migrating nonexistent muppet to TLS."""
        # Mock state manager to return None
        lifecycle_service.state_manager.get_muppet = AsyncMock(return_value=None)

        # Test migration should raise ValidationError
        from src.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Muppet 'nonexistent' not found"):
            await lifecycle_service.migrate_existing_muppet_to_tls("nonexistent")

    def test_generate_next_steps_with_tls(self, lifecycle_service):
        """Test next steps generation with TLS configuration."""
        mock_muppet = Mock()
        mock_muppet.name = "test-muppet"
        mock_muppet.github_repo_url = "https://github.com/org/test-muppet"

        tls_config = {
            "enable_https": True,
            "domain_name": "test-muppet.s3u.dev",
        }

        deployment_result = {
            "service_url": "http://alb-123.us-west-2.elb.amazonaws.com"
        }

        steps = lifecycle_service._generate_next_steps(
            muppet=mock_muppet,
            auto_deploy=True,
            deployment_result=deployment_result,
            tls_config=tls_config,
        )

        # Verify TLS-specific steps are included
        tls_steps = [step for step in steps if "https://" in step or "TLS" in step]
        assert len(tls_steps) >= 1
        assert any("https://test-muppet.s3u.dev" in step for step in steps)

    def test_generate_next_steps_without_tls(self, lifecycle_service):
        """Test next steps generation without TLS configuration."""
        mock_muppet = Mock()
        mock_muppet.name = "test-muppet"
        mock_muppet.github_repo_url = "https://github.com/org/test-muppet"

        deployment_result = {
            "service_url": "http://alb-123.us-west-2.elb.amazonaws.com"
        }

        steps = lifecycle_service._generate_next_steps(
            muppet=mock_muppet,
            auto_deploy=True,
            deployment_result=deployment_result,
            tls_config=None,
        )

        # Verify no TLS-specific steps are included (excluding git clone which uses https for GitHub)
        tls_steps = [
            step
            for step in steps
            if ("TLS" in step or "SSL" in step or "certificate" in step.lower())
        ]
        assert len(tls_steps) == 0

        # Verify the service URL is HTTP, not HTTPS
        service_url_steps = [
            step for step in steps if "alb-123.us-west-2.elb.amazonaws.com" in step
        ]
        assert len(service_url_steps) > 0
        assert all("http://" in step for step in service_url_steps)

    @pytest.mark.asyncio
    async def test_generate_tls_migration_instructions(self, lifecycle_service):
        """Test TLS migration instructions generation."""
        tls_config = {
            "enable_https": True,
            "certificate_arn": "arn:aws:acm:us-west-2:123456789012:certificate/test-cert",
            "domain_name": "test-muppet.s3u.dev",
            "zone_id": "Z1234567890ABC",
            "redirect_http_to_https": True,
            "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
            "create_dns_record": True,
        }

        instructions = await lifecycle_service._generate_tls_migration_instructions(
            "test-muppet", tls_config
        )

        # Verify instruction structure
        assert "overview" in instructions
        assert "steps" in instructions
        assert "automatic_features" in instructions
        assert "support" in instructions

        # Verify steps contain required information
        steps = instructions["steps"]
        assert len(steps) >= 4  # Should have at least 4 steps

        # Verify terraform variables are included
        terraform_step = next(
            (step for step in steps if "Terraform Variables" in step["title"]), None
        )
        assert terraform_step is not None
        assert "terraform_variables" in terraform_step
        assert terraform_step["terraform_variables"]["enable_https"] is True


class TestMuppetLifecycleTLSErrors:
    """Test error handling in TLS integration."""

    @pytest.fixture
    def mock_failing_tls_generator(self):
        """Mock TLS generator that fails."""
        mock_generator = Mock(spec=TLSAutoGenerator)
        mock_generator.generate_muppet_tls_config.side_effect = Exception(
            "TLS generation failed"
        )
        return mock_generator

    @pytest.fixture
    def lifecycle_service_with_failing_tls(self, mock_failing_tls_generator):
        """Create lifecycle service with failing TLS generator."""
        # Create mock instances that can be used as constructor arguments
        mock_github_client = Mock()
        mock_steering_manager = Mock()
        mock_state_manager = Mock()

        with (
            patch.multiple(
                "src.services.muppet_lifecycle_service",
                TemplateManager=Mock,
                GitHubManager=Mock,
                InfrastructureManager=Mock,
                DeploymentService=Mock,
                get_state_manager=Mock(return_value=mock_state_manager),
                get_settings=Mock,
            ),
            patch(
                "src.services.muppet_lifecycle_service.GitHubClient",
                return_value=mock_github_client,
            ),
            patch(
                "src.services.muppet_lifecycle_service.SteeringManager",
                return_value=mock_steering_manager,
            ),
        ):
            service = MuppetLifecycleService(tls_generator=mock_failing_tls_generator)
            # Manually set the state manager for test access
            service.state_manager = mock_state_manager
            return service

    @pytest.mark.asyncio
    async def test_migrate_muppet_tls_generation_failure(
        self, lifecycle_service_with_failing_tls
    ):
        """Test migration when TLS generation fails."""
        # Mock state manager to return a muppet
        mock_muppet = Mock()
        mock_muppet.name = "test-muppet"
        lifecycle_service_with_failing_tls.state_manager.get_muppet = AsyncMock(
            return_value=mock_muppet
        )

        # Test migration
        result = (
            await lifecycle_service_with_failing_tls.migrate_existing_muppet_to_tls(
                "test-muppet"
            )
        )

        # Verify failure is handled gracefully
        assert result["success"] is False
        assert "error" in result
        assert result["muppet_name"] == "test-muppet"
        assert "TLS generation failed" in result["error"]
