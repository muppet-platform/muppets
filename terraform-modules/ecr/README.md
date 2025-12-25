# ECR Module

This Terraform module creates a shared Amazon ECR registry for the Muppet Platform.

## Features

- Centralized container registry for platform and muppet images
- Image scanning enabled for security
- Lifecycle policies for cost optimization
- Encryption at rest
- Proper tagging for resource management

## Usage

```hcl
module "ecr" {
  source = "./terraform-modules/ecr"
  
  registry_name   = "muppet-platform"
  enable_scanning = true
  
  tags = {
    Project     = "muppet-platform"
    Environment = "production"
    Team        = "platform"
  }
}
```

## Repositories Created

- `muppet-platform/platform-service` - Core platform service
- `muppet-platform/mcp-server` - MCP server component
- `muppet-platform/template-tools` - Template development tools

## Lifecycle Policy

The module applies a lifecycle policy that:
- Keeps the last 10 tagged images
- Deletes untagged images older than 1 day
- Helps optimize storage costs

## Outputs

- `registry_url` - Base URL of the ECR registry
- `*_repository_url` - Full URLs for each repository
- `*_repository_arn` - ARNs for each repository

## Requirements

- Terraform >= 1.0
- AWS Provider ~> 5.0
- Appropriate AWS credentials and permissions