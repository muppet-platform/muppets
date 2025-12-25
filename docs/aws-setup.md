# AWS Infrastructure Setup

This document outlines the AWS infrastructure setup for the Muppet Platform, including the shared ECR registry and basic infrastructure components.

## Shared ECR Registry

The platform uses a centralized Amazon ECR registry for all container images (platform and muppets).

### Registry Configuration

- **Registry Name**: `muppet-platform`
- **Region**: `us-west-2` (configurable)
- **Image Scanning**: Enabled for security
- **Lifecycle Policy**: Configured to retain latest 10 images per repository

### Repository Structure

```
muppet-platform ECR Registry:
├── platform-service          # Core platform service container
├── mcp-server                # MCP server container
├── template-tools            # Template development tools
└── muppets/
    ├── {muppet-name-1}       # Individual muppet containers
    ├── {muppet-name-2}
    └── ...
```

### Access Control

- Platform service: Full access to all repositories
- Muppet services: Read access to shared images, full access to own repository
- CI/CD pipelines: Push access for automated builds
- Developers: Pull access for local development

## Basic AWS Infrastructure

### Core Services

1. **Amazon ECS Fargate Cluster**
   - Cluster name: `muppet-platform-cluster`
   - Capacity providers: FARGATE, FARGATE_SPOT
   - Container insights enabled

2. **VPC Configuration**
   - CIDR: `10.0.0.0/16`
   - Public subnets: 2 AZs for load balancers
   - Private subnets: 2 AZs for Fargate services
   - NAT gateways for outbound internet access

3. **Application Load Balancer**
   - Internet-facing for platform service
   - Internal for muppet-to-muppet communication
   - SSL/TLS termination

4. **CloudWatch Configuration**
   - Log groups for platform and muppets
   - Metrics and alarms for monitoring
   - Cost-optimized retention policies

5. **AWS Systems Manager Parameter Store**
   - Platform configuration storage
   - Terraform module versions
   - Shared secrets management

### Security Configuration

1. **IAM Roles and Policies**
   - Platform service execution role
   - Muppet service execution roles
   - CI/CD pipeline roles
   - Cross-account access policies

2. **Security Groups**
   - Platform service security group
   - Muppet service security groups
   - Database access security groups
   - Load balancer security groups

3. **Secrets Management**
   - AWS Secrets Manager for sensitive data
   - Parameter Store for configuration
   - Encryption at rest and in transit

## Terraform Module Integration

The basic infrastructure is provisioned using the shared Terraform modules:

```hcl
# Example platform infrastructure
module "networking" {
  source = "./terraform-modules/networking"
  
  vpc_cidr = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b"]
}

module "ecr" {
  source = "./terraform-modules/ecr"
  
  registry_name = "muppet-platform"
  enable_scanning = true
  lifecycle_policy = "retain-10-images"
}

module "fargate_cluster" {
  source = "./terraform-modules/fargate-service"
  
  cluster_name = "muppet-platform-cluster"
  vpc_id = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids
}
```

## Cost Optimization

1. **Fargate Spot Instances**: Use for non-critical workloads
2. **CloudWatch Log Retention**: 7 days for debug logs, 30 days for application logs
3. **ECR Lifecycle Policies**: Automatic cleanup of old images
4. **Resource Tagging**: Comprehensive tagging for cost allocation

## Monitoring and Alerting

1. **CloudWatch Dashboards**: Platform and muppet health monitoring
2. **Alarms**: CPU, memory, and error rate thresholds
3. **SNS Notifications**: Alert routing to platform team
4. **X-Ray Tracing**: Distributed tracing for performance analysis

## Setup Instructions

1. Configure AWS CLI with appropriate credentials
2. Create S3 bucket for Terraform state storage
3. Deploy shared Terraform modules
4. Provision basic infrastructure using modules
5. Configure ECR registry and repositories
6. Set up monitoring and alerting
7. Test platform service deployment

## Environment Management

- **Development**: Isolated AWS account for testing
- **Staging**: Production-like environment for validation
- **Production**: Live environment with full monitoring

Each environment uses the same Terraform modules with different variable configurations.