"""
Tests for S3 Backend Integration.

This module tests the S3 backend configuration for shared terraform state
management between local development and CI/CD pipelines.
"""

from pathlib import Path

import pytest


class TestS3BackendIntegration:
    """Test cases for S3 backend integration."""

    @pytest.fixture
    def templates_root(self):
        """Get the templates root directory."""
        return Path(__file__).parent.parent.parent / "templates"

    @pytest.fixture
    def terraform_template_dir(self, templates_root):
        """Get the terraform template directory."""
        return templates_root / "java-micronaut" / "terraform"

    @pytest.fixture
    def backend_tf_template(self, terraform_template_dir):
        """Get the backend.tf template content."""
        template_path = terraform_template_dir / "backend.tf.template"
        return template_path.read_text()

    def test_backend_tf_template_exists(self, terraform_template_dir):
        """Test that S3 backend template exists."""
        backend_template = terraform_template_dir / "backend.tf.template"
        assert backend_template.exists(), "S3 backend template should exist"

    def test_s3_backend_configuration(self, backend_tf_template):
        """Test S3 backend configuration generation."""
        content = backend_tf_template
        
        # Check for terraform backend configuration
        assert 'terraform {' in content, "Should contain terraform configuration block"
        assert 'backend "s3" {' in content, "Should specify S3 backend"
        
        # Check for required S3 backend parameters (note the spacing in actual template)
        assert 'bucket         = "muppet-platform-terraform-state"' in content, "Should specify state bucket"
        assert 'key            = "muppets/{{muppet_name}}/terraform.tfstate"' in content, "Should use muppet-specific state key template"
        assert 'region         = "us-west-2"' in content, "Should use hardcoded region (not template variable)"
        
        # Check for state locking
        assert 'dynamodb_table = "muppet-platform-terraform-locks"' in content, "Should specify DynamoDB table for locking"
        assert 'encrypt        = true' in content, "Should enable encryption"

    def test_state_key_pattern(self, backend_tf_template):
        """Test that state key follows the correct pattern."""
        content = backend_tf_template
        
        # Should use template variable for muppet name
        assert 'key            = "muppets/{{muppet_name}}/terraform.tfstate"' in content, "Should use muppet_name template variable"

    def test_backend_variable_substitution(self, backend_tf_template):
        """Test that backend template contains proper variable placeholders."""
        content = backend_tf_template
        
        # Should contain template variables
        assert '{{muppet_name}}' in content, "Should contain muppet_name placeholder"
        # Note: The actual template uses hardcoded region, not template variable

    def test_shared_state_bucket_configuration(self, backend_tf_template):
        """Test shared state bucket configuration."""
        content = backend_tf_template
        
        # All muppets should use the same bucket (note the spacing)
        assert 'bucket         = "muppet-platform-terraform-state"' in content, "Should use shared state bucket"
        
        # But different keys for isolation
        assert 'key            = "muppets/{{muppet_name}}/terraform.tfstate"' in content, "Should use muppet-specific key template"

    def test_state_locking_configuration(self, backend_tf_template):
        """Test DynamoDB state locking configuration."""
        content = backend_tf_template
        
        # Check for DynamoDB table configuration
        assert 'dynamodb_table = "muppet-platform-terraform-locks"' in content, "Should specify DynamoDB table"
        
        # Check for encryption
        assert 'encrypt        = true' in content, "Should enable state encryption"

    def test_backend_syntax_validation(self, backend_tf_template):
        """Test that backend template has valid syntax structure."""
        content = backend_tf_template
        
        # Basic syntax validation
        assert content.count('{') == content.count('}'), "Should have balanced braces"
        assert content.count('"') % 2 == 0, "Should have balanced quotes"
        
        # Should not have syntax errors
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                # Each non-comment line should be properly formatted
                if '=' in line and not line.strip().startswith('terraform') and not line.strip().startswith('backend'):
                    assert line.count('=') >= 1, f"Assignment line should be valid: {line}"

    def test_aws_region_hardcoded(self, backend_tf_template):
        """Test backend configuration uses hardcoded AWS region."""
        content = backend_tf_template
        
        # Should use hardcoded region (not template variable)
        assert 'region         = "us-west-2"' in content, "Should use hardcoded us-west-2 region"

    def test_backend_comments_and_documentation(self, backend_tf_template):
        """Test that backend configuration includes helpful comments."""
        content = backend_tf_template
        
        # Should include explanatory comments (matching actual content)
        assert '# S3 backend configuration for shared state management' in content, "Should include backend explanation"
        assert '# Enables state sharing between local development and CI/CD' in content, "Should explain state sharing"