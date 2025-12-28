"""
Test terraform template backport to ensure simplified configuration works correctly.
"""
import tempfile
from pathlib import Path

import pytest

from src.managers.template_manager import GenerationContext, TemplateManager


class TestTerraformTemplateBackport:
    """Test that backported terraform templates work correctly."""

    @pytest.mark.asyncio
    async def test_terraform_templates_generated_correctly(self):
        """Test that terraform templates are generated with correct content."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "terraform-backport-test"

            context = GenerationContext(
                muppet_name="terraform-backport-test",
                template_name="java-micronaut",
                parameters={
                    "github_organization": "test-org",
                    "aws_region": "us-east-1",
                },
                output_path=output_path,
                aws_region="us-east-1",
                environment="development",
            )

            # Generate code
            generated_path = template_manager.generate_code(context)

            # Check terraform directory exists
            terraform_dir = generated_path / "terraform"
            assert terraform_dir.exists(), "Terraform directory should be created"

            # Check all terraform files exist
            terraform_files = ["main.tf", "variables.tf", "outputs.tf"]
            for tf_file in terraform_files:
                file_path = terraform_dir / tf_file
                assert file_path.exists(), f"{tf_file} should exist"

            # Verify main.tf has backend configuration
            main_tf_content = (terraform_dir / "main.tf").read_text()
            assert (
                'backend "s3"' in main_tf_content
            ), "Should have S3 backend configuration"
            assert (
                "terraform-backport-test" in main_tf_content
            ), "Should contain muppet name"
            assert "us-east-1" in main_tf_content, "Should contain AWS region"

            # Verify variables.tf has simplified variables
            variables_tf_content = (terraform_dir / "variables.tf").read_text()
            assert (
                "muppet_name" in variables_tf_content
            ), "Should have muppet_name variable"
            assert "us-east-1" in variables_tf_content, "Should have default AWS region"
            assert "Java 21 LTS" in variables_tf_content, "Should reference Java 21 LTS"

            # Verify outputs.tf has simplified outputs
            outputs_tf_content = (terraform_dir / "outputs.tf").read_text()
            assert (
                "application_url" in outputs_tf_content
            ), "Should have application_url output"
            assert (
                "health_check_url" in outputs_tf_content
            ), "Should have health_check_url output"
            assert (
                "load_balancer_dns" in outputs_tf_content
            ), "Should have load_balancer_dns output"

    def test_no_duplicate_backend_configuration(self):
        """Test that there's no duplicate backend configuration."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "backend-test"

            context = GenerationContext(
                muppet_name="backend-test",
                template_name="java-micronaut",
                parameters={},
                output_path=output_path,
            )

            # Generate code
            generated_path = template_manager.generate_code(context)
            terraform_dir = generated_path / "terraform"

            # Should not have backend.tf file
            backend_tf = terraform_dir / "backend.tf"
            assert not backend_tf.exists(), "Should not have separate backend.tf file"

            # Should have backend in main.tf
            main_tf_content = (terraform_dir / "main.tf").read_text()
            backend_count = main_tf_content.count('backend "s3"')
            assert (
                backend_count == 1
            ), f"Should have exactly 1 backend configuration, found {backend_count}"

    def test_simplified_variables_only(self):
        """Test that only simplified variables are included."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "variables-test"

            context = GenerationContext(
                muppet_name="variables-test",
                template_name="java-micronaut",
                parameters={},
                output_path=output_path,
            )

            # Generate code
            generated_path = template_manager.generate_code(context)
            terraform_dir = generated_path / "terraform"

            variables_tf_content = (terraform_dir / "variables.tf").read_text()

            # Should have essential variables
            essential_vars = [
                "muppet_name",
                "environment",
                "aws_region",
                "image_tag",
                "cpu",
                "memory",
                "min_capacity",
                "max_capacity",
            ]

            for var in essential_vars:
                assert (
                    f'variable "{var}"' in variables_tf_content
                ), f"Should have {var} variable"

            # Should NOT have complex variables that caused issues
            complex_vars = [
                "use_existing_vpc",
                "existing_vpc_id",
                "vpc_cidr",
                "availability_zones",
                "private_subnet_cidrs",
                "public_subnet_cidrs",
                "cluster_name",
                "enable_ecs_exec",
                "service_discovery_namespace",
                "enable_alarms",
                "alarm_actions",
                "max_image_count",
                "hosted_zone_id",
                "custom_domain",
                "additional_domains",
                "allowed_cidr_blocks",
                "secrets_manager_arns",
                "enable_waf",
                "access_logs_bucket",
                "enable_cost_monitoring",
                "monthly_budget_limit",
            ]

            for var in complex_vars:
                assert (
                    f'variable "{var}"' not in variables_tf_content
                ), f"Should NOT have complex variable {var}"

    def test_simplified_outputs_only(self):
        """Test that only simplified outputs are included."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "outputs-test"

            context = GenerationContext(
                muppet_name="outputs-test",
                template_name="java-micronaut",
                parameters={},
                output_path=output_path,
            )

            # Generate code
            generated_path = template_manager.generate_code(context)
            terraform_dir = generated_path / "terraform"

            outputs_tf_content = (terraform_dir / "outputs.tf").read_text()

            # Should have essential outputs
            essential_outputs = [
                "application_url",
                "health_check_url",
                "load_balancer_dns",
                "service_name",
                "cluster_name",
                "ecr_repository_url",
            ]

            for output in essential_outputs:
                assert (
                    f'output "{output}"' in outputs_tf_content
                ), f"Should have {output} output"

            # Should NOT reference non-existent modules
            module_references = [
                "module.alb",
                "module.networking",
                "module.ecr",
                "module.monitoring",
                "module.tls",
                "module.security",
                "module.fargate_service",
            ]

            for module_ref in module_references:
                assert (
                    module_ref not in outputs_tf_content
                ), f"Should NOT reference {module_ref}"

    def test_parameter_substitution_works(self):
        """Test that parameter substitution works correctly in terraform templates."""
        template_manager = TemplateManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "param-test"

            context = GenerationContext(
                muppet_name="param-test",
                template_name="java-micronaut",
                parameters={
                    "aws_region": "eu-west-1",
                },
                output_path=output_path,
                aws_region="eu-west-1",
                environment="staging",
            )

            # Generate code
            generated_path = template_manager.generate_code(context)
            terraform_dir = generated_path / "terraform"

            # Check parameter substitution in main.tf
            main_tf_content = (terraform_dir / "main.tf").read_text()
            assert "param-test" in main_tf_content, "Should substitute muppet name"
            assert "eu-west-1" in main_tf_content, "Should substitute AWS region"

            # Check parameter substitution in variables.tf
            variables_tf_content = (terraform_dir / "variables.tf").read_text()
            assert (
                "param-test" in variables_tf_content
            ), "Should substitute muppet name in variables"
            assert (
                "eu-west-1" in variables_tf_content
            ), "Should substitute AWS region in variables"

            # Check parameter substitution in outputs.tf
            outputs_tf_content = (terraform_dir / "outputs.tf").read_text()
            assert (
                "param-test" in outputs_tf_content
            ), "Should substitute muppet name in outputs"
