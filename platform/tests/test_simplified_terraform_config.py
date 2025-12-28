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

    def test_default_vpc_usage(self, main_tf_template):
        """Test default VPC data source configuration."""
        content = main_tf_template

        # Check for default VPC data source
        assert (
            'data "aws_vpc" "default"' in content
        ), "Should use default VPC data source"
        assert "default = true" in content, "Should specify default VPC"

        # Check for default subnets data source
        assert (
            'data "aws_subnets" "default"' in content
        ), "Should use default subnets data source"
        assert "vpc-id" in content, "Should filter subnets by VPC ID"

    def test_ecr_data_source_approach(self, main_tf_template):
        """Test ECR repository data source vs resource approach."""
        content = main_tf_template

        # Should use data source, not resource
        assert (
            'data "aws_ecr_repository" "main"' in content
        ), "Should use ECR data source"
        assert (
            'resource "aws_ecr_repository"' not in content
        ), "Should NOT create ECR resource"

        # Should reference data source in task definition
        assert (
            "data.aws_ecr_repository.main.repository_url" in content
        ), "Should reference ECR data source"

        # Should include comment explaining the approach
        assert (
            'CD workflow step "Ensure ECR repository exists"' in content
        ), "Should document ECR creation approach"

    def test_arm64_architecture_config(self, main_tf_template):
        """Test ARM64 runtime platform configuration."""
        content = main_tf_template

        # Check for ARM64 runtime platform
        assert "runtime_platform {" in content, "Should specify runtime platform"
        assert 'operating_system_family = "LINUX"' in content, "Should use Linux OS"
        assert (
            'cpu_architecture        = "ARM64"' in content
        ), "Should use ARM64 architecture"

        # Check for ARM64 comment
        assert (
            "Use ARM64 architecture for better cost/performance" in content
        ), "Should document ARM64 benefits"

    def test_java21_environment_variables(self, main_tf_template):
        """Test Java 21 LTS environment variables in ECS task."""
        content = main_tf_template

        # Check for Java 21 LTS environment variables
        assert (
            '"JAVA_VERSION"' in content
        ), "Should set JAVA_VERSION environment variable"
        assert 'value = "21"' in content, "Should set Java version to 21"
        assert (
            '"JAVA_DISTRIBUTION"' in content
        ), "Should set JAVA_DISTRIBUTION environment variable"
        assert '"amazon-corretto"' in content, "Should use Amazon Corretto distribution"

        # Check for Java 21 optimizations
        assert "JAVA_OPTS" in content, "Should include JAVA_OPTS"
        assert "UseContainerSupport" in content, "Should enable container support"
        assert "UseG1GC" in content, "Should use G1 garbage collector"
        assert "UseStringDeduplication" in content, "Should enable string deduplication"

        # Check for JVM args
        assert "JVM_ARGS" in content, "Should include JVM_ARGS"
        assert (
            "EnableDynamicAgentLoading" in content
        ), "Should enable dynamic agent loading"

    def test_complexity_reduction_validation(self, main_tf_template):
        """Test that simplified config achieves complexity reduction."""
        content = main_tf_template
        lines = content.split("\n")

        # Should be around 300 lines (50% reduction from 600+)
        assert (
            len(lines) < 400
        ), f"Simplified config should be under 400 lines, got {len(lines)}"
        assert (
            len(lines) > 250
        ), f"Config should have substantial content, got {len(lines)}"

        # Should not contain module references
        assert 'module "' not in content, "Should not use terraform modules"
        assert 'source = "git::' not in content, "Should not reference external modules"

    def test_direct_aws_resources(self, main_tf_template):
        """Test that config uses direct AWS resources."""
        content = main_tf_template

        # Check for direct AWS resources
        required_resources = [
            'resource "aws_security_group" "app"',
            'resource "aws_ecs_cluster" "main"',
            'resource "aws_cloudwatch_log_group" "app"',
            'resource "aws_iam_role" "execution"',
            'resource "aws_iam_role" "task"',
            'resource "aws_ecs_task_definition" "app"',
            'resource "aws_lb" "main"',
            'resource "aws_lb_target_group" "app"',
            'resource "aws_lb_listener" "app"',
            'resource "aws_ecs_service" "app"',
            'resource "aws_appautoscaling_target" "ecs_target"',
            'resource "aws_appautoscaling_policy" "ecs_policy_cpu"',
            'resource "aws_appautoscaling_policy" "ecs_policy_memory"',
        ]

        for resource in required_resources:
            assert resource in content, f"Should contain {resource}"

    def test_common_tags_configuration(self, main_tf_template):
        """Test common tags configuration."""
        content = main_tf_template

        # Check for common tags local
        assert "locals {" in content, "Should define locals block"
        assert "common_tags = {" in content, "Should define common_tags"

        # Check for required tags
        required_tags = [
            "MuppetName",
            "Environment",
            "ManagedBy",
            "Template",
            "Language",
            "Framework",
            "JavaVersion",
            "CreatedBy",
        ]

        for tag in required_tags:
            assert tag in content, f"Should include {tag} tag"

        # Check for Java 21 LTS tag
        assert (
            'JavaVersion   = "21-LTS"' in content
        ), "Should tag with Java 21 LTS version"

    def test_health_check_configuration(self, main_tf_template):
        """Test health check configuration."""
        content = main_tf_template

        # Check for container health check
        assert "healthCheck = {" in content, "Should define container health check"
        assert (
            "curl -f http://localhost:3000/health" in content
        ), "Should check health endpoint"
        assert "startPeriod = 120" in content, "Should allow startup time for Java apps"

        # Check for ALB health check
        assert "health_check {" in content, "Should define ALB health check"
        assert 'path                = "/health"' in content, "Should use /health path"
        assert 'matcher             = "200"' in content, "Should expect 200 response"

    def test_auto_scaling_configuration(self, main_tf_template):
        """Test auto-scaling configuration."""
        content = main_tf_template

        # Check for auto-scaling target
        assert (
            'resource "aws_appautoscaling_target" "ecs_target"' in content
        ), "Should define auto-scaling target"

        # Check for CPU-based scaling
        assert (
            'resource "aws_appautoscaling_policy" "ecs_policy_cpu"' in content
        ), "Should define CPU scaling policy"
        assert (
            "ECSServiceAverageCPUUtilization" in content
        ), "Should use CPU utilization metric"

        # Check for memory-based scaling
        assert (
            'resource "aws_appautoscaling_policy" "ecs_policy_memory"' in content
        ), "Should define memory scaling policy"
        assert (
            "ECSServiceAverageMemoryUtilization" in content
        ), "Should use memory utilization metric"

    def test_template_variable_placeholders(self, main_tf_template):
        """Test that template contains proper variable placeholders."""
        content = main_tf_template

        # Should contain template variable placeholders
        assert "{{muppet_name}}" in content, "Should contain muppet_name placeholder"

        # Should use variables in resource names and references
        assert "var.muppet_name" in content, "Should reference muppet_name variable"
        assert "var.environment" in content, "Should reference environment variable"
        assert "var.aws_region" in content, "Should reference aws_region variable"
