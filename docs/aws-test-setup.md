# AWS Testing Environment Setup

This document provides instructions for setting up a real AWS environment to test muppet deployments.

## Prerequisites

1. **AWS Account**: You need an AWS account with appropriate permissions
2. **AWS CLI**: Install and configure AWS CLI v2
3. **OpenTofu**: Install OpenTofu (already done via homebrew)
4. **Domain (Optional)**: For TLS testing, you'll need a domain managed by Route53

## Step 1: AWS Credentials Setup

### Option A: AWS CLI Configuration
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter your default region (e.g., us-west-2)
# Enter output format (json)
```

### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

### Option C: IAM Role (for EC2/ECS)
If running on AWS infrastructure, use IAM roles instead of access keys.

## Step 2: Required AWS Permissions

Your AWS user/role needs the following permissions:
- ECS (Elastic Container Service) - Full access
- ECR (Elastic Container Registry) - Full access
- VPC (Virtual Private Cloud) - Full access
- ALB (Application Load Balancer) - Full access
- CloudWatch - Full access
- IAM - Limited access for service roles
- Route53 - For domain management (optional)
- ACM (Certificate Manager) - For TLS certificates (optional)

## Step 3: Platform Configuration

Update the platform configuration to use real AWS services:

```bash
# In platform/.env.real (create this file)
ENVIRONMENT=production
AWS_REGION=us-west-2
GITHUB_TOKEN=your-github-token
GITHUB_ORG=muppet-platform

# Enable real AWS integration
USE_REAL_AWS=true
USE_REAL_GITHUB=true

# ECR Configuration
ECR_REGISTRY_URL=123456789012.dkr.ecr.us-west-2.amazonaws.com
ECR_REPOSITORY_PREFIX=muppet-platform

# Optional: Domain configuration for TLS
DOMAIN_NAME=your-domain.com
HOSTED_ZONE_ID=Z1234567890ABC
```

## Step 4: Initialize AWS Resources

Create basic AWS resources needed for the platform:

```bash
# Switch to real environment
cd platform
cp .env.real .env

# Test AWS connectivity
aws sts get-caller-identity

# Create ECR repositories (if needed)
aws ecr create-repository --repository-name muppet-platform/java-micronaut --region us-west-2
```

## Step 5: Test Muppet Deployment

### 5.1 Create a Test Muppet
```bash
# Use the platform MCP tools or direct API
curl -X POST http://localhost:8000/api/v1/muppets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-muppet-aws",
    "template": "java-micronaut",
    "parameters": {
      "description": "Test muppet for AWS deployment"
    }
  }'
```

### 5.2 Deploy to AWS
```bash
# Deploy the muppet to AWS Fargate
curl -X POST http://localhost:8000/api/v1/muppets/test-muppet-aws/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "container_image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/muppet-platform/test-muppet-aws:latest",
    "environment_variables": {
      "ENVIRONMENT": "production"
    }
  }'
```

### 5.3 Monitor Deployment
```bash
# Check deployment status
curl http://localhost:8000/api/v1/muppets/test-muppet-aws/deployment-status

# Get service logs
curl http://localhost:8000/api/v1/muppets/test-muppet-aws/logs
```

## Step 6: TLS Testing (Optional)

If you have a domain in Route53:

### 6.1 Update Muppet with Domain
```bash
# Update the muppet configuration to include domain
curl -X PUT http://localhost:8000/api/v1/muppets/test-muppet-aws \
  -H "Content-Type: application/json" \
  -d '{
    "domain_name": "test-muppet.your-domain.com",
    "enable_https": true,
    "create_certificate": true
  }'
```

### 6.2 Verify HTTPS Access
```bash
# Test HTTPS endpoint (after certificate validation)
curl -I https://test-muppet.your-domain.com/health
```

## Step 7: Cleanup

To avoid AWS charges, clean up resources after testing:

```bash
# Undeploy the muppet
curl -X DELETE http://localhost:8000/api/v1/muppets/test-muppet-aws/deployment

# Delete the muppet (if cleanup is enabled)
curl -X DELETE http://localhost:8000/api/v1/muppets/test-muppet-aws
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check AWS credentials and permissions
2. **Region Mismatch**: Ensure all resources are in the same region
3. **ECR Authentication**: Run `aws ecr get-login-password` if needed
4. **Certificate Validation**: DNS validation can take 5-10 minutes
5. **Security Groups**: Ensure ALB security group allows inbound traffic

### Useful Commands

```bash
# Check AWS credentials
aws sts get-caller-identity

# List ECS clusters
aws ecs list-clusters

# List ECR repositories
aws ecr describe-repositories

# Check certificate status
aws acm list-certificates

# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/fargate/"
```

## Cost Considerations

AWS resources incur costs. Typical costs for testing:
- ECS Fargate: ~$0.04/hour per task
- ALB: ~$0.025/hour + $0.008 per LCU-hour
- NAT Gateway: ~$0.045/hour + data processing
- CloudWatch Logs: ~$0.50/GB ingested

**Recommendation**: Use AWS Free Tier when possible and clean up resources promptly.