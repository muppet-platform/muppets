# Manual Test Scenario 1: Basic Muppet Creation

## Objective
Test end-to-end muppet creation with real AWS and GitHub integrations.

## Prerequisites
- Real integrations configured (run setup-real-integrations.sh)
- AWS credentials configured
- GitHub authentication configured
- Platform service running

## Test Steps

### 1. Start Platform Service
```bash
# Use real integration environment
cp .env.real .env
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test MCP Tools (using Kiro or direct API)
```bash
# List available templates
curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_templates", "arguments": {}}'

# Create a test muppet
curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "create_muppet", "arguments": {"name": "test-manual-muppet", "template": "java-micronaut"}}'
```

### 3. Verify GitHub Repository Creation
- Check https://github.com/muppet-platform/test-manual-muppet
- Verify repository has template code
- Check branch protection rules
- Verify GitHub Actions workflows

### 4. Verify AWS Resources
```bash
# Check ECS cluster
aws ecs describe-clusters --clusters muppet-platform-cluster

# Check ECR repository
aws ecr describe-repositories --repository-names test-manual-muppet

# Check Parameter Store
aws ssm get-parameters-by-path --path "/muppet-platform/test-manual-muppet"
```

### 5. Test Muppet Status
```bash
# Get muppet status
curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "get_muppet_status", "arguments": {"name": "test-manual-muppet"}}'
```

### 6. Cleanup
```bash
# Delete the test muppet
curl -X POST http://localhost:8000/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "delete_muppet", "arguments": {"name": "test-manual-muppet"}}'
```

## Expected Results
- ✅ GitHub repository created with template code
- ✅ AWS ECS cluster and ECR repository created
- ✅ Parameter Store entries created
- ✅ Muppet status shows "creating" then "running"
- ✅ Cleanup removes all resources

## Troubleshooting
- Check AWS CloudWatch logs for errors
- Verify GitHub token has organization permissions
- Check AWS permissions for ECS, ECR, SSM access
