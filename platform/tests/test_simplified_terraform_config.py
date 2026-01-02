"""
Tests for the Simplified Terraform Configuration.

This module tests the new simplified terraform approach that replaces
complex module-based configuration with direct AWS resources.
"""

from pathlib import Path

import pytest


class TestSimplifiedTerraformConfig:
    """Test cases for simplified terraform configuration."""

    @pytest.fixture
    def templates_root(self):
        """Get the templates root directory."""
        return Path(__file__).parent.parent.parent / "templates"

    @pytest.fixture
    def terraform_template_dir(self, templates_root):
        """Get the terraform template directory."""
        return templates_root / "java-micronaut" / "terraform"

    @pytest.fixture
    def main_tf_template(self, terraform_template_dir):
        """Get the main.tf template content."""
        template_path = terraform_template_dir / "main.tf.template"
        return template_path.read_text()

    def test_terraform_main_template_exists(self, terraform_template_dir):
        """Test that simplified terraform main template exists."""
        template_path = terraform_template_dir / "main.tf.template"
        assert (
            template_path.exists()
        ), "Simplified terraform main.tf.template should exist"

    def test_terraform_validation_syntax(self, main_tf_template):
        """Test that simplified terraform config has valid syntax."""
        content = main_tf_template

        # Check for required terraform block
        assert "terraform {" in content, "Should contain terraform configuration block"
        assert (
            'required_version = ">= 1.5"' in content
        ), "Should specify minimum terraform version"
        assert "required_providers {" in content, "Should specify required providers"

        # Check for AWS provider
        assert (
            'source  = "hashicorp/aws"' in content
        ), "Should use hashicorp AWS provider"
        assert 'version = "~> 5.0"' in content, "Should use AWS provider v5.x"

    def test_module_handles_networking(self, main_tf_template):
        """Test that module handles networking configuration."""
        content = main_tf_template

        # Should NOT use direct VPC data sources (module handles networking)
        assert (
            'data "aws_vpc" "default"' not in content
        ), "Should NOT use direct VPC data source (handled by module)"
        assert (
            'data "aws_subnets" "default"' not in content
        ), "Should NOT use direct subnets data source (handled by module)"

        # Should pass networking configuration to module
        assert "vpc_cidr" in content, "Should pass VPC CIDR to module"
        assert (
            "public_subnet_count" in content
        ), "Should pass subnet configuration to module"

    def test_module_handles_ecr(self, main_tf_template):
        """Test that module handles ECR repository access."""
        content = main_tf_template

        # Should NOT use direct ECR data source (module handles this)
        assert (
            'data "aws_ecr_repository" "main"' not in content
        ), "Should NOT use direct ECR data source (handled by module)"

        # Module handles ECR repository access internally

    def test_module_handles_runtime_platform(self, main_tf_template):
        """Test that module handles runtime platform configuration."""
        content = main_tf_template

        # Should NOT have direct runtime platform config (module handles this)
        assert (
            "runtime_platform {" not in content
        ), "Should NOT specify runtime platform directly (handled by module)"
        assert (
            'operating_system_family = "LINUX"' not in content
        ), "Should NOT specify OS directly (handled by module)"
        assert (
            'cpu_architecture        = "ARM64"' not in content
        ), "Should NOT specify architecture directly (handled by module)"

        # Module handles all runtime platform configuration internally

    def test_module_handles_java_config(self, main_tf_template):
        """Test that module handles Java-specific configuration."""
        content = main_tf_template

        # Should NOT have direct Java environment variables (module handles this)
        assert (
            '"JAVA_VERSION"' not in content
        ), "Should NOT set JAVA_VERSION directly (handled by module)"
        assert (
            '"JAVA_DISTRIBUTION"' not in content
        ), "Should NOT set JAVA_DISTRIBUTION directly (handled by module)"
        assert (
            "JAVA_OPTS" not in content
        ), "Should NOT set JAVA_OPTS directly (handled by module)"
        assert (
            "JVM_ARGS" not in content
        ), "Should NOT set JVM_ARGS directly (handled by module)"

        # Module handles all Java-specific environment variables and optimizations internally

    def test_complexity_reduction_validation(self, main_tf_template):
        """Test that simplified config achieves complexity reduction."""
        content = main_tf_template
        lines = content.split("\n")

        # Should be much smaller now (under 100 lines vs 400+ before)
        assert (
            len(lines) < 100
        ), f"Simplified config should be under 100 lines, got {len(lines)}"
        assert (
            len(lines) > 50
        ), f"Config should have substantial content, got {len(lines)}"

        # Should use shared modules (this is the new simplified approach)
        assert 'module "muppet"' in content, "Should use shared muppet module"
        assert "terraform-modules/" in content, "Should reference shared modules"
        assert 'source = "git::' in content, "Should reference GitHub URL modules"

    def test_shared_module_usage(self, main_tf_template):
        """Test that config uses shared modules instead of direct resources."""
        content = main_tf_template

        # Should use shared module
        assert 'module "muppet"' in content, "Should use shared muppet module"
        assert (
            "terraform-modules/muppet-java-micronaut" in content
        ), "Should reference Java module"

        # Should NOT contain direct AWS resources (they're in the module now)
        direct_resources = [
            'resource "aws_security_group"',
            'resource "aws_ecs_cluster"',
            'resource "aws_cloudwatch_log_group"',
            'resource "aws_iam_role"',
            'resource "aws_ecs_task_definition"',
            'resource "aws_lb"',
            'resource "aws_lb_target_group"',
            'resource "aws_lb_listener"',
            'resource "aws_ecs_service"',
            'resource "aws_appautoscaling_target"',
            'resource "aws_appautoscaling_policy"',
        ]

        for resource in direct_resources:
            assert (
                resource not in content
            ), f"Should NOT contain direct resource {resource} (should be in module)"

    def test_module_configuration_structure(self, main_tf_template):
        """Test module configuration structure instead of common tags."""
        content = main_tf_template

        # Should NOT have locals block (that's in the module now)
        assert (
            "locals {" not in content
        ), "Should NOT define locals block (handled by module)"

        # Should have module configuration sections
        assert (
            "# Basic configuration" in content
        ), "Should have basic configuration section"
        assert (
            "# Container configuration" in content
        ), "Should have container configuration section"
        assert (
            "# Auto-scaling configuration" in content
        ), "Should have auto-scaling configuration section"
        assert "# TLS configuration" in content, "Should have TLS configuration section"

    def test_module_handles_health_checks(self, main_tf_template):
        """Test that module handles health check configuration."""
        content = main_tf_template

        # Should NOT have direct health check config (that's in the module now)
        assert (
            "healthCheck = {" not in content
        ), "Should NOT define container health check directly (handled by module)"
        assert (
            "health_check {" not in content
        ), "Should NOT define ALB health check directly (handled by module)"

        # Module handles all health check configuration internally

    def test_module_handles_auto_scaling(self, main_tf_template):
        """Test that module handles auto-scaling configuration."""
        content = main_tf_template

        # Should NOT have direct auto-scaling resources (that's in the module now)
        assert (
            'resource "aws_appautoscaling_target"' not in content
        ), "Should NOT define auto-scaling target directly (handled by module)"
        assert (
            'resource "aws_appautoscaling_policy"' not in content
        ), "Should NOT define auto-scaling policies directly (handled by module)"

        # Should pass auto-scaling parameters to module
        assert (
            "target_cpu_utilization" in content
        ), "Should pass CPU utilization target to module"
        assert (
            "target_memory_utilization" in content
        ), "Should pass memory utilization target to module"

    def test_template_variable_placeholders(self, main_tf_template):
        """Test that template contains proper variable placeholders."""
        content = main_tf_template

        # Should contain template variable placeholders
        assert "{{muppet_name}}" in content, "Should contain muppet_name placeholder"

        # Should use variables in resource names and references
        assert "var.muppet_name" in content, "Should reference muppet_name variable"
        assert "var.environment" in content, "Should reference environment variable"
        assert "var.aws_region" in content, "Should reference aws_region variable"
