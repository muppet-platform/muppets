"""
Tests for the Template Manager component.

This module tests template discovery, validation, and code generation
functionality of the TemplateManager class.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.managers.template_manager import (
    GenerationContext,
    TemplateManager,
    TemplateMetadata,
    TemplateNotFoundError,
    TemplateValidationError,
)
from src.models import Template


class TestTemplateManager:
    """Test cases for TemplateManager class."""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create a temporary templates directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_root = Path(temp_dir)

            # Create a sample template
            java_template_dir = templates_root / "java-micronaut"
            java_template_dir.mkdir()

            # Create template.yaml
            template_config = {
                "name": "java-micronaut",
                "version": "1.0.0",
                "description": "Java Micronaut template",
                "language": "java",
                "framework": "micronaut",
                "port": 3000,
                "terraform_modules": ["fargate-service", "monitoring"],
                "required_variables": ["muppet_name", "aws_region"],
                "supported_features": ["health_checks", "metrics"],
                "template_files": [
                    "src/",
                    "Dockerfile.template",
                    "build.gradle.template",
                ],
            }

            with open(java_template_dir / "template.yaml", "w") as f:
                yaml.dump(template_config, f)

            # Create some template files
            src_dir = java_template_dir / "src"
            src_dir.mkdir()
            (src_dir / "Application.java").write_text(
                "public class {{muppet_name}}Application {}"
            )

            (java_template_dir / "Dockerfile.template").write_text(
                "FROM amazoncorretto:21\nCOPY . /app"
            )
            (java_template_dir / "build.gradle.template").write_text(
                "plugins { id 'java' }"
            )

            yield templates_root

    @pytest.fixture
    def template_manager(self, temp_templates_dir):
        """Create a TemplateManager instance with temporary templates."""
        return TemplateManager(templates_root=temp_templates_dir)

    def test_init_with_default_path(self):
        """Test TemplateManager initialization with default path."""
        manager = TemplateManager()
        assert manager.templates_root.name == "templates"
        assert manager._template_cache == {}

    def test_init_with_custom_path(self, temp_templates_dir):
        """Test TemplateManager initialization with custom path."""
        manager = TemplateManager(templates_root=temp_templates_dir)
        assert manager.templates_root == temp_templates_dir

    def test_discover_templates_success(self, template_manager):
        """Test successful template discovery."""
        templates = template_manager.discover_templates()

        assert len(templates) == 1
        template = templates[0]
        assert template.name == "java-micronaut"
        assert template.version == "1.0.0"
        assert template.language == "java"
        assert template.framework == "micronaut"
        assert "fargate-service" in template.terraform_modules
        assert "muppet_name" in template.required_variables

    def test_discover_templates_empty_directory(self):
        """Test template discovery with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TemplateManager(templates_root=Path(temp_dir))
            templates = manager.discover_templates()
            assert templates == []

    def test_discover_templates_nonexistent_directory(self):
        """Test template discovery with nonexistent directory."""
        manager = TemplateManager(templates_root=Path("/nonexistent"))
        templates = manager.discover_templates()
        assert templates == []

    def test_get_template_found(self, template_manager):
        """Test getting an existing template."""
        # First discover templates
        template_manager.discover_templates()

        template = template_manager.get_template("java-micronaut")
        assert template is not None
        assert template.name == "java-micronaut"

    def test_get_template_not_found(self, template_manager):
        """Test getting a non-existent template."""
        template = template_manager.get_template("nonexistent")
        assert template is None

    def test_validate_template_success(self, template_manager):
        """Test successful template validation."""
        template_manager.discover_templates()

        result = template_manager.validate_template("java-micronaut")
        assert result is True

    def test_validate_template_not_found(self, template_manager):
        """Test validation of non-existent template."""
        with pytest.raises(TemplateNotFoundError):
            template_manager.validate_template("nonexistent")

    def test_validate_template_missing_files(self, temp_templates_dir):
        """Test validation with missing template files."""
        # Create template with missing files
        invalid_template_dir = temp_templates_dir / "invalid-template"
        invalid_template_dir.mkdir()

        template_config = {
            "name": "invalid-template",
            "version": "1.0.0",
            "description": "Invalid template",
            "language": "java",
            "framework": "micronaut",
            "terraform_modules": ["fargate-service"],
            "required_variables": ["muppet_name"],
            "supported_features": ["health_checks"],
            "template_files": ["missing-file.txt"],  # This file doesn't exist
        }

        with open(invalid_template_dir / "template.yaml", "w") as f:
            yaml.dump(template_config, f)

        manager = TemplateManager(templates_root=temp_templates_dir)
        manager.discover_templates()

        with pytest.raises(TemplateValidationError):
            manager.validate_template("invalid-template")

    def test_generate_code_success(self, template_manager):
        """Test successful code generation."""
        template_manager.discover_templates()

        with tempfile.TemporaryDirectory() as output_dir:
            context = GenerationContext(
                muppet_name="test-muppet",
                template_name="java-micronaut",
                parameters={"custom_param": "value"},
                output_path=Path(output_dir),
            )

            result_path = template_manager.generate_code(context)

            assert result_path == Path(output_dir)
            assert (Path(output_dir) / "src" / "Application.java").exists()
            assert (Path(output_dir) / "Dockerfile").exists()
            assert (Path(output_dir) / "build.gradle").exists()

            # Check that template variables were injected
            java_content = (Path(output_dir) / "src" / "Application.java").read_text()
            assert "test-muppet" in java_content

    def test_generate_code_template_not_found(self, template_manager):
        """Test code generation with non-existent template."""
        with tempfile.TemporaryDirectory() as output_dir:
            context = GenerationContext(
                muppet_name="test-muppet",
                template_name="nonexistent",
                parameters={},
                output_path=Path(output_dir),
            )

            with pytest.raises(TemplateNotFoundError):
                template_manager.generate_code(context)

    def test_get_template_versions(self, template_manager):
        """Test getting template versions."""
        template_manager.discover_templates()

        versions = template_manager.get_template_versions()
        assert "java-micronaut" in versions
        assert versions["java-micronaut"] == "1.0.0"

    def test_generation_context_get_all_variables(self):
        """Test GenerationContext variable aggregation."""
        context = GenerationContext(
            muppet_name="test-muppet",
            template_name="java-micronaut",
            parameters={"custom_param": "value"},
            output_path=Path("/tmp"),
            aws_region="us-west-2",
            environment="production",
        )

        variables = context.get_all_variables()

        assert variables["muppet_name"] == "test-muppet"
        assert variables["template_name"] == "java-micronaut"
        assert variables["aws_region"] == "us-west-2"
        assert variables["environment"] == "production"
        assert variables["custom_param"] == "value"


class TestTemplateMetadata:
    """Test cases for TemplateMetadata class."""

    def test_template_metadata_creation(self):
        """Test TemplateMetadata creation."""
        template = Template(
            name="test",
            version="1.0.0",
            description="Test template",
            language="java",
            framework="micronaut",
            terraform_modules=[],
            required_variables=[],
            supported_features=[],
        )

        metadata = TemplateMetadata(
            template=template,
            template_path=Path("/test"),
            config_path=Path("/test/template.yaml"),
        )

        assert metadata.template == template
        assert metadata.validation_errors == []
        assert metadata.last_validated is None


class TestGenerationContext:
    """Test cases for GenerationContext class."""

    def test_generation_context_defaults(self):
        """Test GenerationContext with default values."""
        context = GenerationContext(
            muppet_name="test",
            template_name="java-micronaut",
            parameters={},
            output_path=Path("/tmp"),
        )

        assert context.aws_region == "us-east-1"
        assert context.environment == "development"

    def test_generation_context_custom_values(self):
        """Test GenerationContext with custom values."""
        context = GenerationContext(
            muppet_name="test",
            template_name="java-micronaut",
            parameters={"key": "value"},
            output_path=Path("/tmp"),
            aws_region="eu-west-1",
            environment="staging",
        )

        variables = context.get_all_variables()
        assert variables["aws_region"] == "eu-west-1"
        assert variables["environment"] == "staging"
        assert variables["key"] == "value"
