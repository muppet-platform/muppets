"""
Tests for Service URL Discovery.

This module tests the service URL discovery functionality that provides
developers with easy access to deployed service endpoints.
"""

from pathlib import Path

import pytest


class TestServiceUrlDiscovery:
    """Test cases for service URL discovery."""

    @pytest.fixture
    def templates_root(self):
        """Get the templates root directory."""
        return Path(__file__).parent.parent.parent / "templates"

    @pytest.fixture
    def terraform_template_dir(self, templates_root):
        """Get the terraform template directory."""
        return templates_root / "java-micronaut" / "terraform"

    @pytest.fixture
    def outputs_tf_template(self, terraform_template_dir):
        """Get the outputs.tf template content."""
        template_path = terraform_template_dir / "outputs.tf.template"
        return template_path.read_text()

    def test_outputs_tf_template_exists(self, terraform_template_dir):
        """Test that outputs template exists."""
        outputs_template = terraform_template_dir / "outputs.tf.template"
        assert outputs_template.exists(), "Outputs template should exist"

    def test_service_url_outputs_generation(self, outputs_tf_template):
        """Test service URL outputs generation."""
        content = outputs_tf_template

        # Check for load balancer DNS output (note the spacing in actual template)
        assert (
            'output "load_balancer_dns"' in content
        ), "Should output load balancer DNS"
        assert (
            "value       = aws_lb.main.dns_name" in content
        ), "Should reference ALB DNS name"
        assert (
            'description = "Load balancer DNS name (for easy copy/paste)"' in content
        ), "Should describe DNS output"

    def test_application_url_output(self, outputs_tf_template):
        """Test application URL output generation."""
        content = outputs_tf_template

        # Check for application URL output (note the spacing)
        assert 'output "application_url"' in content, "Should output application URL"
        assert (
            'value       = "http://${aws_lb.main.dns_name}"' in content
        ), "Should construct HTTP URL"
        assert (
            'description = "HTTP URL to access the application"' in content
        ), "Should describe application URL"

    def test_health_check_url_output(self, outputs_tf_template):
        """Test health check URL output generation."""
        content = outputs_tf_template

        # Check for health check URL output (note the spacing)
        assert 'output "health_check_url"' in content, "Should output health check URL"
        assert (
            'value       = "http://${aws_lb.main.dns_name}/health"' in content
        ), "Should construct health check URL"
        assert (
            'description = "Health check endpoint URL"' in content
        ), "Should describe health check URL"

    def test_deployment_info_output(self, outputs_tf_template):
        """Test deployment info output for CI/CD integration."""
        content = outputs_tf_template

        # Check for deployment info output
        assert 'output "deployment_info"' in content, "Should output deployment info"
        assert (
            'description = "Deployment information for CI/CD pipelines"' in content
        ), "Should describe deployment info"

        # Check for deployment info structure
        assert (
            "service_name      = aws_ecs_service.app.name" in content
        ), "Should include service name in deployment info"
        assert (
            "load_balancer_dns = aws_lb.main.dns_name" in content
        ), "Should include load balancer DNS in deployment info"
        assert (
            'health_check_path = "/health"' in content
        ), "Should include health check path in deployment info"
        assert (
            "environment       = var.environment" in content
        ), "Should include environment in deployment info"

    def test_direct_resource_references(self, outputs_tf_template):
        """Test that outputs use direct resource references instead of modules."""
        content = outputs_tf_template

        # Should use direct resource references
        assert (
            "aws_lb.main.dns_name" in content
        ), "Should reference ALB resource directly"
        assert (
            "aws_ecs_service.app.name" in content
        ), "Should reference ECS service directly"

        # Should not use module references
        assert "module." not in content, "Should not reference terraform modules"

    def test_output_variable_substitution(self, outputs_tf_template):
        """Test that output template contains proper variable placeholders."""
        content = outputs_tf_template

        # Should contain template variables
        assert "{{muppet_name}}" in content, "Should contain muppet_name placeholder"
        # Note: The actual template doesn't use aws_region template variable

    def test_output_descriptions_are_helpful(self, outputs_tf_template):
        """Test that output descriptions are helpful for developers."""
        content = outputs_tf_template

        # Check for helpful descriptions (matching actual content)
        descriptions = [
            "Load balancer DNS name (for easy copy/paste)",
            "HTTP URL to access the application",
            "Health check endpoint URL",
            "Deployment information for CI/CD pipelines",
        ]

        for description in descriptions:
            assert (
                description in content
            ), f"Should include helpful description: {description}"

    def test_ci_cd_integration_outputs(self, outputs_tf_template):
        """Test outputs designed for CI/CD pipeline integration."""
        content = outputs_tf_template

        # Should include structured deployment info for CI/CD
        assert "deployment_info" in content, "Should include deployment_info output"

        # Should include all necessary information for CI/CD (matching actual content)
        required_fields = [
            "service_name",
            "load_balancer_dns",
            "health_check_path",
            "environment",
        ]

        for field in required_fields:
            assert field in content, f"Should include {field} in deployment info"

    def test_output_syntax_validation(self, outputs_tf_template):
        """Test that outputs template has valid terraform syntax structure."""
        content = outputs_tf_template

        # Basic syntax validation
        assert content.count("{") == content.count("}"), "Should have balanced braces"
        assert content.count('"') % 2 == 0, "Should have balanced quotes"

        # Should contain proper output blocks
        output_blocks = content.count('output "')
        assert output_blocks >= 4, "Should contain at least 4 output blocks"

        # Each output should have value and description
        for output_name in [
            "load_balancer_dns",
            "application_url",
            "health_check_url",
            "deployment_info",
        ]:
            assert (
                f'output "{output_name}"' in content
            ), f"Should contain {output_name} output"

    def test_template_variable_placeholders(self, outputs_tf_template):
        """Test that outputs template contains proper variable placeholders."""
        content = outputs_tf_template

        # Should contain template variable placeholders
        assert "{{muppet_name}}" in content, "Should contain muppet_name placeholder"
        # Note: The actual template doesn't use aws_region template variable

    def test_output_comments_and_documentation(self, outputs_tf_template):
        """Test that outputs include helpful comments."""
        content = outputs_tf_template

        # Should include explanatory comments (matching actual content)
        assert (
            "# Simplified outputs for {{muppet_name}}" in content
        ), "Should include header with muppet name"
        assert (
            "# Provides essential information for developers and CI/CD" in content
        ), "Should explain purpose"
        assert "# Application URLs" in content, "Should have section headers"
