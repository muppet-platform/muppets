# Muppet Platform AWS Deployment Guide

This guide covers deploying the Muppet Platform to AWS using the automated CI/CD pipeline.

## Overview

The Muppet Platform is deployed as a containerized FastAPI service on AWS ECS Fargate with:

- **ECS Fargate**: Serverless container hosting
- **Application Load Balancer**: HTTP traffic distribution
- **ECR**: Container image registry
- **CloudWatch**: Logging and monitoring
- **Auto Scaling**: Automatic capacity management
- **ARM64 Architecture**: Cost-optimized compute

## Prerequisites

### 1. AWS Account Setup

Ensure you have:
- AWS account with appropriate permissions
- AWS CLI configured locally (for manual operations)
- S3 bucket for Terraform state: `muppet-platform-terraform-state`
- DynamoDB table for state locking: `muppet-platform-terraform-locks`

### 2. GitHub Secrets Configuration

Configure these secrets in your GitHub repository:

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`: AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for deployment

**Optional Secrets:**
- `PLATFORM_GITHUB_TOKEN`: GitHub token for platform operations (stored in SSM)

### 3. AWS Permissions

The deployment user needs permissions for:
- ECS (clusters, services, task definitions)
- ECR (repositories, images)
- IAM (roles, policies)
- CloudWatch (logs, metrics, alarms)
- Application Load Balancer
- Auto Scaling
- VPC (security groups, subnets)
- S3 (Terraform state)
- DynamoDB (Terraform locking)
- SSM (parameter store)

## Deployment Process

### Automatic Deployment

The platform deploys automatically when:

1. **Push to main branch**: Triggers CI → CD pipeline
2. **Manual trigger**: Use GitHub Actions "workflow_dispatch"

### Manual Deployment

To deploy manually:

1. Go to GitHub Actions in your repository
2. Select "CD" workflow
3. Click "Run workflow"
4. Choose environment (staging/production)
5. Click "Run workflow"

## Infrastructure Components

### Core Services

- **ECS Cluster**: `muppet-platform-cluster`
- **ECS Service**: `muppet-platform`
- **Load Balancer**: `muppet-platform-alb`
- **ECR Repository**: `muppet-platform`

### Networking

- **VPC**: Uses default VPC for simplicity
- **Subnets**: All available subnets in default VPC
- **Security Group**: Allows HTTP (80), HTTPS (443), and app port (8000)

### Monitoring

- **CloudWatch Logs**: `/ecs/muppet-platform`
- **CPU Alarm**: Triggers at 80% utilization
- **Memory Alarm**: Triggers at 80% utilization
- **Auto Scaling**: CPU and memory-based scaling

## Configuration

### Environment Variables

The platform service receives these environment variables:

- `ENVIRONMENT`: Deployment environment (staging/production)
- `AWS_REGION`: AWS region (us-west-2)
- `LOG_LEVEL`: Application log level (INFO)
- `INTEGRATION_MODE`: Set to "real" for AWS deployment
- `GITHUB_ORGANIZATION`: GitHub organization name
- `GITHUB_TOKEN`: Retrieved from SSM Parameter Store

### Resource Sizing

**Default Configuration:**
- **CPU**: 1024 units (1 vCPU)
- **Memory**: 2048 MB (2 GB)
- **Min Instances**: 1
- **Max Instances**: 5
- **Auto Scaling**: 70% CPU, 80% Memory

**Production Recommendations:**
- **CPU**: 2048 units (2 vCPU)
- **Memory**: 4096 MB (4 GB)
- **Min Instances**: 2
- **Max Instances**: 10

## Post-Deployment Setup

### 1. GitHub Token Configuration

If you have a GitHub token for platform operations:

```bash
# Set the GitHub token in SSM Parameter Store
aws ssm put-parameter \
  --name "/muppet-platform/github-token" \
  --value "your-github-token" \
  --type "SecureString" \
  --overwrite
```

### 2. Verify Deployment

Check these endpoints after deployment:

```bash
# Get the load balancer DNS
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names muppet-platform-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

# Test health endpoint
curl http://${ALB_DNS}/health

# Test API documentation
curl http://${ALB_DNS}/docs
```

### 3. Monitor Deployment

**CloudWatch Logs:**
```bash
aws logs tail /ecs/muppet-platform --follow
```

**ECS Service Status:**
```bash
aws ecs describe-services \
  --cluster muppet-platform-cluster \
  --services muppet-platform
```

## Troubleshooting

### Common Issues

**1. Service Won't Start**
- Check CloudWatch logs: `/ecs/muppet-platform`
- Verify environment variables in task definition
- Check security group allows port 8000

**2. Health Check Failures**
- Verify application starts on port 8000
- Check `/health` endpoint responds with 200
- Review application logs for startup errors

**3. Load Balancer Issues**
- Verify target group health checks
- Check security group allows ALB traffic
- Ensure subnets are in different AZs

**4. Auto Scaling Issues**
- Check CloudWatch metrics for CPU/Memory
- Verify auto scaling policies are active
- Review scaling events in ECS console

### Useful Commands

**View Service Status:**
```bash
aws ecs describe-services \
  --cluster muppet-platform-cluster \
  --services muppet-platform \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

**View Recent Logs:**
```bash
aws logs tail /ecs/muppet-platform --since 1h
```

**Force New Deployment:**
```bash
aws ecs update-service \
  --cluster muppet-platform-cluster \
  --service muppet-platform \
  --force-new-deployment
```

**Check Load Balancer Health:**
```bash
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names muppet-platform-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)
```

## Cost Optimization

### ARM64 Architecture
- Uses ARM64 for ~20% cost savings vs x86
- Better performance per dollar
- Fully compatible with Python/FastAPI

### Auto Scaling
- Scales down to 1 instance during low usage
- Scales up based on CPU/Memory utilization
- Uses Fargate Spot for additional savings (optional)

### Log Retention
- CloudWatch logs retained for 7 days
- Reduces storage costs
- Increase retention for production if needed

## Security Considerations

### Network Security
- ALB in public subnets, ECS tasks in private subnets
- Security groups restrict access to necessary ports
- No direct internet access to ECS tasks

### Secrets Management
- GitHub token stored in SSM Parameter Store
- Encrypted at rest and in transit
- IAM roles for service-to-service authentication

### Container Security
- Base image: `python:3.11-slim`
- Non-root user in container
- Regular security scanning via Trivy

## Monitoring and Alerting

### CloudWatch Metrics
- ECS service metrics (CPU, Memory, Task count)
- ALB metrics (Request count, Response time, Errors)
- Custom application metrics (if implemented)

### Alarms
- High CPU utilization (>80%)
- High memory utilization (>80%)
- Service task count (for availability)

### Logs
- Application logs in CloudWatch
- Structured JSON logging
- Log aggregation and search capabilities

## Backup and Recovery

### State Management
- Terraform state in S3 with versioning
- State locking via DynamoDB
- Cross-region replication for disaster recovery

### Container Images
- ECR repository with lifecycle policies
- Automatic vulnerability scanning
- Image retention policies

### Configuration
- Infrastructure as Code (Terraform)
- Version controlled configuration
- Reproducible deployments

## Scaling Considerations

### Horizontal Scaling
- Auto scaling based on CPU/Memory
- Can scale from 1 to 5+ instances
- Load balancer distributes traffic

### Vertical Scaling
- Adjust CPU/Memory in Terraform variables
- Requires service restart
- Monitor resource utilization

### Database Scaling
- Platform uses external services (GitHub, AWS APIs)
- No persistent database to scale
- Stateless service design

## Production Readiness Checklist

- [ ] AWS account and permissions configured
- [ ] GitHub secrets configured
- [ ] S3 backend and DynamoDB table created
- [ ] GitHub token stored in SSM
- [ ] Resource sizing appropriate for load
- [ ] Monitoring and alerting configured
- [ ] Log retention policy set
- [ ] Security groups reviewed
- [ ] Backup and recovery procedures documented
- [ ] Runbook for common operations created
- [ ] Load testing performed
- [ ] Disaster recovery plan documented

## Support

For deployment issues:

1. Check CloudWatch logs first
2. Review ECS service events
3. Verify AWS permissions
4. Check GitHub Actions logs
5. Review Terraform state and outputs

For platform functionality issues, refer to the main platform documentation.