# IAM Module

This Terraform module creates IAM roles and policies for the Muppet Platform, following the principle of least privilege and supporting various deployment scenarios.

## Features

- **ECS Task Execution Role**: Standard role for ECS task execution with ECR and Parameter Store access
- **ECS Task Role**: Application-specific role for muppet runtime permissions
- **Platform Service Role**: Enhanced role for platform service operations
- **GitHub Actions Role**: OIDC-based role for CI/CD deployments
- **Custom Policies**: Flexible policy attachment for specific muppet requirements
- **Least Privilege**: Minimal permissions with resource-specific access

## Usage

```hcl
module "iam" {
  source = "../terraform-modules/iam"

  name_prefix = "my-muppet"
  
  # Platform service role (for platform components)
  create_platform_service_role = true
  
  # GitHub Actions role (for CI/CD)
  create_github_actions_role = true
  github_oidc_provider_arn   = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
  github_repository_subjects = [
    "repo:muppet-platform/my-muppet:ref:refs/heads/main",
    "repo:muppet-platform/my-muppet:ref:refs/heads/develop"
  ]
  
  # Custom policies for specific muppet needs
  custom_policies = {
    "s3-access" = {
      description = "S3 bucket access for my-muppet"
      policy_document = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Effect = "Allow"
            Action = [
              "s3:GetObject",
              "s3:PutObject"
            ]
            Resource = "arn:aws:s3:::my-muppet-bucket/*"
          }
        ]
      })
    }
  }
  
  tags = {
    Environment = "production"
    Muppet      = "my-muppet"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | ~> 5.0 |

## Providers

| Name | Version |
|------|---------|
| aws | ~> 5.0 |

## Resources

| Name | Type |
|------|------|
| aws_iam_role.ecs_execution_role | resource |
| aws_iam_role.ecs_task_role | resource |
| aws_iam_role.platform_service_role | resource |
| aws_iam_role.github_actions_role | resource |
| aws_iam_policy.custom_policies | resource |
| aws_iam_role_policy.ecs_execution_ecr_policy | resource |
| aws_iam_role_policy.ecs_task_logs_policy | resource |
| aws_iam_role_policy.platform_service_policy | resource |
| aws_iam_role_policy.github_actions_policy | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name_prefix | Prefix for IAM resource names | `string` | `"muppet-platform"` | no |
| create_platform_service_role | Create IAM role for platform service | `bool` | `false` | no |
| create_github_actions_role | Create IAM role for GitHub Actions | `bool` | `false` | no |
| github_oidc_provider_arn | ARN of the GitHub OIDC provider | `string` | `""` | no |
| github_repository_subjects | GitHub repository subjects for OIDC | `list(string)` | `[]` | no |
| custom_policies | Custom IAM policies to create | `map(object)` | `{}` | no |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| ecs_execution_role_arn | ARN of the ECS task execution role |
| ecs_task_role_arn | ARN of the ECS task role |
| platform_service_role_arn | ARN of the platform service role |
| github_actions_role_arn | ARN of the GitHub Actions role |
| custom_policy_arns | ARNs of custom IAM policies |

## IAM Roles

### ECS Task Execution Role

**Purpose**: Used by ECS to pull container images and start tasks

**Permissions**:
- ECR image pulling
- CloudWatch Logs creation
- Parameter Store access (for secrets)
- Secrets Manager access (for secrets)

**Trust Policy**: `ecs-tasks.amazonaws.com`

### ECS Task Role

**Purpose**: Used by the running application for AWS API calls

**Permissions**:
- CloudWatch Logs writing
- Custom policies (attached dynamically)

**Trust Policy**: `ecs-tasks.amazonaws.com`

### Platform Service Role

**Purpose**: Used by the platform service for muppet management

**Permissions**:
- ECS service management
- ECR repository management
- Parameter Store management
- Load balancer inspection

**Trust Policy**: `ecs-tasks.amazonaws.com`

### GitHub Actions Role

**Purpose**: Used by GitHub Actions for CI/CD deployments

**Permissions**:
- ECR image pushing
- ECS service updates
- Task definition registration
- IAM role passing

**Trust Policy**: GitHub OIDC provider with repository restrictions

## Security Best Practices

### Least Privilege

All roles follow the principle of least privilege:

```hcl
# Resource-specific permissions
Resource = [
  "arn:aws:ssm:${region}:${account}:parameter/${name_prefix}/*"
]
```

### Resource Scoping

Permissions are scoped to specific resources when possible:

```hcl
# Scoped to muppet-specific log groups
Resource = [
  "arn:aws:logs:${region}:${account}:log-group:/aws/fargate/${name_prefix}*"
]
```

### OIDC for GitHub Actions

Uses OpenID Connect instead of long-lived access keys:

```hcl
# Repository-specific trust policy
Condition = {
  StringLike = {
    "token.actions.githubusercontent.com:sub" = [
      "repo:muppet-platform/my-muppet:ref:refs/heads/main"
    ]
  }
}
```

## Custom Policies

Add muppet-specific permissions using custom policies:

```hcl
custom_policies = {
  "database-access" = {
    description = "RDS database access"
    policy_document = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "rds-db:connect"
          ]
          Resource = "arn:aws:rds-db:us-east-1:123456789012:dbuser:db-instance-id/db-user-name"
        }
      ]
    })
  }
  
  "sqs-access" = {
    description = "SQS queue access"
    policy_document = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "sqs:SendMessage",
            "sqs:ReceiveMessage",
            "sqs:DeleteMessage"
          ]
          Resource = "arn:aws:sqs:us-east-1:123456789012:my-muppet-queue"
        }
      ]
    })
  }
}
```

## Examples

### Basic Muppet IAM

```hcl
module "muppet_iam" {
  source = "../terraform-modules/iam"

  name_prefix = "simple-muppet"
  
  tags = {
    Environment = "development"
    Muppet      = "simple-muppet"
  }
}
```

### Production Muppet with CI/CD

```hcl
# First, create GitHub OIDC provider (one-time setup)
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  
  client_id_list = ["sts.amazonaws.com"]
  
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]
}

module "production_muppet_iam" {
  source = "../terraform-modules/iam"

  name_prefix = "production-muppet"
  
  # Enable GitHub Actions deployment
  create_github_actions_role = true
  github_oidc_provider_arn   = aws_iam_openid_connect_provider.github.arn
  github_repository_subjects = [
    "repo:muppet-platform/production-muppet:ref:refs/heads/main"
  ]
  
  # Custom permissions for production workload
  custom_policies = {
    "production-s3" = {
      description = "Production S3 bucket access"
      policy_document = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Effect = "Allow"
            Action = [
              "s3:GetObject",
              "s3:PutObject",
              "s3:DeleteObject"
            ]
            Resource = "arn:aws:s3:::production-muppet-data/*"
          }
        ]
      })
    }
  }
  
  tags = {
    Environment = "production"
    Muppet      = "production-muppet"
    Team        = "platform"
  }
}
```

### Platform Service IAM

```hcl
module "platform_iam" {
  source = "../terraform-modules/iam"

  name_prefix = "muppet-platform"
  
  # Enable platform service role
  create_platform_service_role = true
  
  # Enable GitHub Actions for platform deployments
  create_github_actions_role = true
  github_oidc_provider_arn   = aws_iam_openid_connect_provider.github.arn
  github_repository_subjects = [
    "repo:muppet-platform/platform:ref:refs/heads/main",
    "repo:muppet-platform/platform:ref:refs/heads/develop"
  ]
  
  tags = {
    Environment = "shared"
    Component   = "platform"
  }
}
```

## Integration with Other Modules

```hcl
module "iam" {
  source = "../terraform-modules/iam"
  # ... IAM configuration
}

module "fargate_service" {
  source = "../terraform-modules/fargate-service"

  service_name = "my-muppet"
  
  # Use IAM module outputs
  execution_role_arn = module.iam.ecs_execution_role_arn
  task_role_arn      = module.iam.ecs_task_role_arn
  
  # ... other configuration
}
```

## GitHub Actions Workflow Example

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push Docker image
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$GITHUB_SHA .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$GITHUB_SHA
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster muppet-platform \
            --service my-muppet \
            --force-new-deployment
```