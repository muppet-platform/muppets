# Manual Testing with Real Integrations

This directory contains tools and documentation for manually testing the Muppet Platform with real AWS and GitHub integrations.

## Quick Start

1. **Setup Real Integrations**
   ```bash
   ./scripts/setup-real-integrations.sh
   ```

2. **Start Platform with Real Integrations**
   ```bash
   cp .env.real .env
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Run Interactive Tests**
   ```bash
   cd manual-tests
   python scripts/interactive_test.py
   ```

4. **Cleanup Test Resources**
   ```bash
   ./manual-tests/cleanup/cleanup-test-resources.sh
   ```

## Directory Structure

- `scenarios/` - Step-by-step manual test scenarios
- `scripts/` - Interactive testing scripts and utilities
- `docs/` - Testing documentation and guides
- `cleanup/` - Resource cleanup scripts

## Prerequisites

- AWS CLI configured with appropriate permissions
- GitHub CLI authenticated
- Python environment with platform dependencies
- Access to muppet-platform GitHub organization

## Test Scenarios

1. **Basic Muppet Creation** (`scenarios/01-basic-muppet-creation.md`)
   - End-to-end muppet creation with real services
   - GitHub repository creation and configuration
   - AWS resource provisioning

2. **Pipeline Management** (Coming soon)
   - Workflow version management
   - Pipeline updates and rollbacks

3. **Steering Documentation** (Coming soon)
   - Document distribution and updates
   - Cross-muppet synchronization

## Troubleshooting

### Common Issues

1. **AWS Permission Errors**
   - Ensure your AWS user/role has ECS, ECR, CloudWatch, SSM, and IAM permissions
   - Check AWS CLI configuration: `aws sts get-caller-identity`

2. **GitHub Authentication Issues**
   - Verify GitHub CLI authentication: `gh auth status`
   - Check organization access: `gh api orgs/muppet-platform`

3. **Platform Service Errors**
   - Check logs in `logs/platform.log`
   - Verify environment configuration in `.env`

### Getting Help

- Check CloudWatch logs for AWS-related errors
- Review GitHub API rate limits and permissions
- Verify network connectivity to AWS and GitHub services
