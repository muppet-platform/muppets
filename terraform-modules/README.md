# Muppet Platform - Shared Terraform Modules

This directory contains shared, versioned infrastructure modules used by both the platform and muppets.

## Structure

- `fargate-service/` - Reusable Fargate service module
- `monitoring/` - CloudWatch monitoring module
- `networking/` - VPC and networking module
- `ecr/` - Shared ECR registry module
- `iam/` - IAM roles and policies module
- `tests/` - Terraform module tests
- `.github/workflows/` - Module CI/CD

## Module Development

All modules follow Terraform best practices and are versioned for controlled updates across the platform.

[Documentation will be expanded as modules are implemented]