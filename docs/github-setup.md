# GitHub Organization Setup

This document outlines the GitHub repository structure for the Muppet Platform under the `muppet-platform` organization.

## Repository Structure

All repositories are created under the `muppet-platform` organization (https://github.com/muppet-platform) and are private by default.

### Core Repositories

1. **Platform Repository**: `https://github.com/muppet-platform/platform`
   - Contains the core platform service
   - MCP server implementation
   - Platform infrastructure code

2. **Templates Repository**: `https://github.com/muppet-platform/templates`
   - Contains all muppet templates
   - Template development tools
   - Template validation and testing

3. **Terraform Modules Repository**: `https://github.com/muppet-platform/terraform-modules`
   - Shared infrastructure modules
   - Module versioning and testing
   - Infrastructure documentation

4. **Steering Docs Repository**: `https://github.com/muppet-platform/steering-docs`
   - Centralized steering documentation
   - Shared development best practices
   - Template-specific steering additions

### Muppet Repositories

Each created muppet gets its own private repository:
- **Format**: `https://github.com/muppet-platform/{muppet-name}`
- **Visibility**: Private
- **Features**: Branch protection, CI/CD workflows, issue templates

## Repository Configuration

### Branch Protection Rules
- Require pull request reviews before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Restrict pushes to main branch

### CI/CD Integration
- GitHub Actions workflows for automated testing
- Automated deployment pipelines
- Integration with AWS services
- Shared ECR registry for container images

## Setup Instructions

1. Create the `muppet-platform` GitHub organization
2. Configure organization settings and permissions
3. Set up shared secrets for AWS integration
4. Configure shared ECR registry access
5. Create initial repositories with proper templates

## Access Control

- Organization owners: Platform team leads
- Repository admins: Component team leads
- Developers: Read/write access to relevant repositories
- Muppet creators: Admin access to their muppet repositories

## Automation

The platform automatically:
- Creates new muppet repositories
- Configures branch protection rules
- Sets up CI/CD workflows
- Manages access permissions
- Populates repositories with template code