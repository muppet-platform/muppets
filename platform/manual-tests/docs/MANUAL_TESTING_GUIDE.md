# Manual Testing Guide: Muppet Platform with Real Integrations

This guide provides step-by-step instructions for manually testing the Muppet Platform with real AWS and GitHub integrations.

## Overview

Manual testing allows you to verify that the platform works correctly with real external services, providing confidence that the implementation will work in production environments.

## Prerequisites

### Required Tools
- **AWS CLI** - For AWS service interaction
- **GitHub CLI** - For GitHub authentication and operations
- **Python 3.10+** - Platform runtime
- **Docker** - For container operations (optional)

### Required Access
- **AWS Account** with appropriate permissions
- **GitHub Account** with organization access
- **muppet-platform GitHub Organization** (or permission to create it)

### Required Permissions

#### AWS Permissions
Your AWS user/role needs the following permissions:
- **ECS**: `CreateCluster`, `CreateService`, `RegisterTaskDefinition`, `DescribeServices`
- **ECR**: `CreateRepository`, `GetAuthorizationToken`, `BatchCheckLayerAvailability`
- **CloudWatch**: `CreateLogGroup`, `PutLogEvents`, `DescribeLogGroups`
- **SSM**: `PutParameter`, `GetParameter`, `GetParametersByPath`, `DeleteParameter`
- **IAM**: `CreateRole`, `AttachRolePolicy`, `PassRole`
- **VPC**: `CreateVpc`, `CreateSubnet`, `CreateSecurityGroup` (if creating new VPC)

#### GitHub Permissions
Your GitHub account needs:
- **Organization Access**: Admin or owner access to `muppet-platform` organization
- **Repository Management**: Create, delete, and manage repositories
- **Workflow Management**: Create and update GitHub Actions workflows

## Setup Process

### Step 1: Initial Setup

1. **Clone and Navigate to Platform**
   ```bash
   cd platform
   ```

2. **Run Setup Script**
   ```bash
   ./scripts/setup-real-integrations.sh
   ```

   This script will:
   - Check prerequisites (AWS CLI, GitHub CLI)
   - Verify AWS credentials and permissions
   - Verify GitHub authentication and organization access
   - Create `.env.real` configuration file
   - Set up manual testing directory structure

3. **Review Configuration**
   ```bash
   cat .env.real
   ```

   Verify the configuration matches your environment.

### Step 2: Configure Real Integration Mode

1. **Switch to Real Integration Mode**
   ```bash
   cp .env.real .env
   ```

2. **Verify Configuration**
   ```bash
   # Check AWS configuration
   aws sts get-caller-identity
   aws configure list

   # Check GitHub configuration
   gh auth status
   gh api user
   ```

### Step 3: Start Platform Service

1. **Start the Platform**
   ```bash
   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify Service Health**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {"status": "healthy", "timestamp": "2024-01-15T10:00:00Z"}
   ```

## Manual Testing Scenarios

### Scenario 1: Basic Muppet Creation

**Objective**: Test end-to-end muppet creation with real services.

#### Test Steps

1. **List Available Templates**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "list_templates", "arguments": {}}'
   ```

   **Expected**: List of available templates including `java-micronaut`

2. **Create Test Muppet**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "test-manual-muppet", "template": "java-micronaut"}}'
   ```

   **Expected**: Success response with repository URL

3. **Verify GitHub Repository**
   - Navigate to: https://github.com/muppet-platform/test-manual-muppet
   - Verify repository exists and contains template code
   - Check that branch protection rules are configured
   - Verify GitHub Actions workflows are present

4. **Verify AWS Resources**
   ```bash
   # Check ECS cluster
   aws ecs describe-clusters --clusters muppet-platform-cluster

   # Check ECR repository
   aws ecr describe-repositories --repository-names test-manual-muppet

   # Check Parameter Store entries
   aws ssm get-parameters-by-path --path "/muppet-platform/test-manual-muppet"

   # Check CloudWatch log group
   aws logs describe-log-groups --log-group-name-prefix "/aws/fargate/test-manual-muppet"
   ```

5. **Check Muppet Status**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "get_muppet_status", "arguments": {"name": "test-manual-muppet"}}'
   ```

   **Expected**: Status information including GitHub repo and AWS resources

6. **List All Muppets**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "list_muppets", "arguments": {}}'
   ```

   **Expected**: List including the newly created muppet

#### Cleanup
```bash
curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "test-manual-muppet"}}'
```

### Scenario 2: Pipeline Management

**Objective**: Test pipeline management with real GitHub workflows.

#### Test Steps

1. **List Workflow Versions**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "list_workflow_versions", "arguments": {"template_type": "java-micronaut"}}'
   ```

2. **Create Test Muppet** (if not exists)
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "pipeline-test-muppet", "template": "java-micronaut"}}'
   ```

3. **Update Muppet Pipelines**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "update_muppet_pipelines", "arguments": {"muppet_name": "pipeline-test-muppet", "workflow_version": "java-micronaut-v1.2.3"}}'
   ```

4. **Verify GitHub Workflow Updates**
   - Check repository: https://github.com/muppet-platform/pipeline-test-muppet
   - Verify `.github/workflows/` directory contains updated workflows
   - Check workflow files reference the correct version

5. **Test Rollback**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "rollback_muppet_pipelines", "arguments": {"muppet_name": "pipeline-test-muppet", "workflow_version": "java-micronaut-v1.2.2"}}'
   ```

#### Cleanup
```bash
curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "pipeline-test-muppet"}}'
```

### Scenario 3: Java Package Naming and Token Replacement

**Objective**: Test Java package name validation and template token replacement with edge cases.

#### Test Steps

1. **Test Basic Java Package Naming**
   ```bash
   # Test simple names
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "simple-service", "template": "java-micronaut"}}'
   ```

   **Verification**:
   - Check repository: https://github.com/muppet-platform/simple-service
   - Verify Java files use package `com.muppetplatform.simple_service`
   - Confirm directory structure: `src/main/java/com/muppetplatform/simple_service/`

2. **Test Special Characters in Muppet Names**
   ```bash
   # Test with special characters
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "my@special#service", "template": "java-micronaut"}}'
   ```

   **Verification**:
   - Check repository: https://github.com/muppet-platform/my@special#service (URL encoded)
   - Verify Java package name is sanitized: `com.muppetplatform.my_special_service`
   - Confirm all Java files compile without errors

3. **Test Numeric Prefix Handling**
   ```bash
   # Test names starting with numbers
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "2fa-auth-service", "template": "java-micronaut"}}'
   ```

   **Verification**:
   - Verify Java package name: `com.muppetplatform.pkg_2fa_auth_service`
   - Check that package starts with letter (pkg_ prefix added)

4. **Test Java Keyword Collision**
   ```bash
   # Test Java keywords
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "class", "template": "java-micronaut"}}'
   ```

   **Verification**:
   - Verify Java package name: `com.muppetplatform.class_`
   - Check underscore suffix added to avoid keyword collision

5. **Test Complex Real-World Names**
   ```bash
   # Test complex service names
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "User-Authentication-Service-v2.1", "template": "java-micronaut"}}'
   ```

   **Verification**:
   - Verify Java package name: `com.muppetplatform.user_authentication_service_v2_1`
   - Check all special characters converted to underscores
   - Verify case conversion to lowercase

6. **Test Template Variable Replacement**
   
   For each created muppet, verify the following template variables are correctly replaced:

   **Java Files Verification**:
   ```bash
   # Clone and check a test repository
   git clone https://github.com/muppet-platform/simple-service.git /tmp/simple-service
   cd /tmp/simple-service
   
   # Check Application.java
   grep -n "package com.muppetplatform.simple_service;" src/main/java/com/muppetplatform/simple_service/Application.java
   grep -n "simple-service" src/main/java/com/muppetplatform/simple_service/Application.java
   
   # Check controllers
   grep -n "package com.muppetplatform.simple_service.controller;" src/main/java/com/muppetplatform/simple_service/controller/HealthController.java
   grep -n "simple-service" src/main/java/com/muppetplatform/simple_service/controller/HealthController.java
   ```

   **Gradle Configuration Verification**:
   ```bash
   # Check build.gradle
   grep -n "simple-service" build.gradle
   grep -n "com.muppetplatform.simple_service.Application" build.gradle
   ```

   **Docker Configuration Verification**:
   ```bash
   # Check Dockerfile
   grep -n "simple-service" Dockerfile
   ```

   **GitHub Actions Verification**:
   ```bash
   # Check workflow files
   grep -n "simple-service" .github/workflows/ci.yml
   grep -n "simple-service" .github/workflows/cd.yml
   ```

7. **Test Unicode and International Characters**
   ```bash
   # Test with Unicode characters
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "café-service", "template": "java-micronaut"}}'
   ```

   **Verification**:
   - Verify Java package name: `com.muppetplatform.caf_service`
   - Check Unicode characters are properly handled

8. **Test Length Validation**
   ```bash
   # Test very long names
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "create_muppet", "arguments": {"name": "very-long-service-name-that-exceeds-reasonable-limits-for-package-names", "template": "java-micronaut"}}'
   ```

   **Verification**:
   - Verify package name is truncated to reasonable length (≤50 chars)
   - Check truncation doesn't break Java syntax

#### Cleanup for Java Package Tests
```bash
# Clean up test repositories
curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "simple-service"}}'

curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "my@special#service"}}'

curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "2fa-auth-service"}}'

curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "class"}}'

curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "User-Authentication-Service-v2.1"}}'

curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "café-service"}}'

curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "very-long-service-name-that-exceeds-reasonable-limits-for-package-names"}}'
```

### Scenario 4: Steering Documentation

**Objective**: Test steering documentation distribution.

#### Test Steps

1. **List Steering Documents**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "list_steering_docs", "arguments": {}}'
   ```

2. **List Muppet-Specific Steering**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "list_steering_docs", "arguments": {"muppet_name": "test-manual-muppet"}}'
   ```

3. **Update Shared Steering**
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool": "update_shared_steering", "arguments": {}}'
   ```

4. **Verify Steering Distribution**
   - Check muppet repositories for `.kiro/steering/` directories
   - Verify shared steering documents are present
   - Check that updates are reflected across all muppets

## Interactive Testing

For a more user-friendly testing experience, use the interactive testing script:

```bash
cd manual-tests
python scripts/interactive_test.py
```

This provides a menu-driven interface for testing all platform functionality.

## Troubleshooting

### Common Issues

#### AWS Permission Errors
```
Error: User: arn:aws:iam::123456789012:user/test-user is not authorized to perform: ecs:CreateCluster
```

**Solution**: Ensure your AWS user/role has the required permissions listed in the prerequisites.

#### GitHub Authentication Issues
```
Error: HTTP 401: Bad credentials
```

**Solutions**:
1. Re-authenticate with GitHub CLI: `gh auth login`
2. Check token permissions: `gh auth status`
3. Verify organization access: `gh api orgs/muppet-platform`

#### Java Package Naming Issues
```
Error: Invalid package name in generated Java files
```

**Solutions**:
1. Check muppet name contains only valid characters
2. Verify package name conversion logic in `GenerationContext._to_java_package_name`
3. Test with edge cases: `curl -X POST http://localhost:8000/mcp/tools/execute -H "Content-Type: application/json" -d '{"tool": "create_muppet", "arguments": {"name": "test@name", "template": "java-micronaut"}}'`

#### Template Variable Replacement Issues
```
Error: Template variables not replaced in generated files
```

**Solutions**:
1. Check template files contain correct `{{variable}}` syntax
2. Verify `GenerationContext.get_all_variables()` includes required variables
3. Test variable replacement: `grep -r "{{" /path/to/generated/muppet/`
4. Check file processing in `TemplateManager._process_template_files`

#### Java Compilation Errors in Generated Code
```
Error: Package does not exist or invalid package declaration
```

**Solutions**:
1. Verify Java package name follows naming conventions
2. Check directory structure matches package declaration
3. Validate Java 21 LTS compatibility
4. Test compilation: `cd /path/to/muppet && ./gradlew build`

#### Platform Service Connection Issues
```
Error: Connection refused to localhost:8000
```

**Solutions**:
1. Ensure the platform service is running
2. Check for port conflicts
3. Review service logs for startup errors

#### AWS Endpoint Issues (LocalStack)
```
Error: Could not connect to the endpoint URL
```

**Solutions**:
1. Ensure LocalStack is running (if using local mode)
2. Check `AWS_ENDPOINT_URL` configuration
3. Verify network connectivity

### Debugging Tips

1. **Check Service Logs**
   ```bash
   tail -f logs/platform.log
   ```

2. **Verify Environment Configuration**
   ```bash
   env | grep -E "(AWS_|GITHUB_|INTEGRATION_)"
   ```

3. **Test AWS Connectivity**
   ```bash
   aws sts get-caller-identity
   aws ecs list-clusters
   ```

4. **Test GitHub Connectivity**
   ```bash
   gh api user
   gh api orgs/muppet-platform
   ```

5. **Check Platform Health**
   ```bash
   curl -v http://localhost:8000/health
   ```

## Resource Cleanup

### Automated Cleanup
```bash
./manual-tests/cleanup/cleanup-test-resources.sh
```

### Manual Cleanup

#### AWS Resources
```bash
# Delete ECS services
aws ecs update-service --cluster muppet-platform-cluster --service test-manual-muppet --desired-count 0
aws ecs delete-service --cluster muppet-platform-cluster --service test-manual-muppet

# Delete ECR repositories
aws ecr delete-repository --repository-name test-manual-muppet --force

# Delete Parameter Store parameters
aws ssm delete-parameters-by-path --path "/muppet-platform/test-manual-muppet" --recursive

# Delete CloudWatch log groups
aws logs delete-log-group --log-group-name "/aws/fargate/test-manual-muppet"
```

#### GitHub Resources
```bash
# Delete test repositories
gh repo delete muppet-platform/test-manual-muppet --confirm
gh repo delete muppet-platform/pipeline-test-muppet --confirm
```

## Best Practices

### Before Testing
1. Always run the setup script first
2. Verify all prerequisites are met
3. Test with a dedicated AWS account/region if possible
4. Use test-specific naming conventions (e.g., `test-*`, `manual-*`)

### During Testing
1. Test one scenario at a time
2. Verify each step before proceeding
3. Document any unexpected behavior
4. Take screenshots of successful operations

### After Testing
1. Always run cleanup scripts
2. Verify all test resources are removed
3. Check AWS billing for unexpected charges
4. Document any issues or improvements needed

## Cost Considerations

### AWS Costs
- **ECS Fargate**: Charged per vCPU and memory per second
- **ECR**: Storage costs for container images
- **CloudWatch**: Log storage and API calls
- **Parameter Store**: Standard parameters are free, advanced parameters have costs

### Minimizing Costs
1. Clean up resources immediately after testing
2. Use Fargate Spot for non-production testing
3. Set short log retention periods (7 days)
4. Delete unused ECR repositories
5. Use AWS Cost Explorer to monitor spending

## Security Considerations

### AWS Security
1. Use IAM roles with minimal required permissions
2. Enable CloudTrail for audit logging
3. Use VPC endpoints for private communication
4. Encrypt sensitive parameters in Parameter Store

### GitHub Security
1. Use fine-grained personal access tokens
2. Limit token permissions to required scopes
3. Regularly rotate access tokens
4. Enable two-factor authentication

### Platform Security
1. Don't commit real credentials to version control
2. Use environment variables for sensitive configuration
3. Regularly update dependencies
4. Monitor for security vulnerabilities

## Next Steps

After successful manual testing:

1. **Document Results**: Record test outcomes and any issues
2. **Update Automation**: Improve automated tests based on manual findings
3. **Production Readiness**: Prepare for production deployment
4. **Monitoring Setup**: Configure production monitoring and alerting
5. **Documentation Updates**: Update user documentation based on testing experience

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review platform logs in `logs/platform.log`
3. Check AWS CloudWatch logs for service-specific issues
4. Consult GitHub API documentation for repository issues
5. Create issues in the platform repository for bugs or improvements