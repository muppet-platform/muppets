# Fargate Service Module

This Terraform module creates a complete AWS Fargate service with Application Load Balancer, auto-scaling, and health checks. It's designed to be reusable across all muppets in the Muppet Platform.

## Features

- **ECS Fargate Service**: Serverless container deployment
- **Application Load Balancer**: HTTP load balancing with health checks
- **Auto Scaling**: CPU and memory-based scaling policies
- **Security Groups**: Properly configured network security
- **CloudWatch Logging**: Centralized log management with configurable retention
- **Health Checks**: Container and ALB health monitoring
- **IAM Roles**: Least-privilege access for task execution and application

## Usage

```hcl
module "muppet_service" {
  source = "../terraform-modules/fargate-service"

  service_name    = "my-muppet"
  container_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/muppet-platform/my-muppet:latest"
  
  # Networking
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids
  
  # Resource allocation
  cpu    = 512
  memory = 1024
  
  # Scaling
  desired_count           = 2
  autoscaling_min_capacity = 1
  autoscaling_max_capacity = 10
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = "production"
    LOG_LEVEL   = "INFO"
  }
  
  # Secrets from Parameter Store
  secrets = {
    DATABASE_URL = "/muppet-platform/my-muppet/database-url"
    API_KEY      = "/muppet-platform/my-muppet/api-key"
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
| aws_ecs_cluster.main | resource |
| aws_ecs_service.main | resource |
| aws_ecs_task_definition.main | resource |
| aws_lb.main | resource |
| aws_lb_target_group.main | resource |
| aws_lb_listener.main | resource |
| aws_security_group.ecs | resource |
| aws_security_group.alb | resource |
| aws_appautoscaling_target.ecs_target | resource |
| aws_appautoscaling_policy.ecs_policy_cpu | resource |
| aws_appautoscaling_policy.ecs_policy_memory | resource |
| aws_iam_role.execution | resource |
| aws_iam_role.task | resource |
| aws_cloudwatch_log_group.app | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| service_name | Name of the ECS service | `string` | n/a | yes |
| container_image | Docker image to run in the container | `string` | n/a | yes |
| vpc_id | ID of the VPC | `string` | n/a | yes |
| private_subnet_ids | List of private subnet IDs for ECS service | `list(string)` | n/a | yes |
| public_subnet_ids | List of public subnet IDs for load balancer | `list(string)` | `[]` | no |
| container_port | Port on which the container listens | `number` | `3000` | no |
| cpu | Number of CPU units for the task | `number` | `256` | no |
| memory | Amount of memory (in MiB) for the task | `number` | `512` | no |
| desired_count | Number of instances of the task definition | `number` | `1` | no |
| enable_autoscaling | Enable auto scaling for the ECS service | `bool` | `true` | no |
| autoscaling_min_capacity | Minimum number of tasks | `number` | `1` | no |
| autoscaling_max_capacity | Maximum number of tasks | `number` | `10` | no |
| environment_variables | Environment variables to pass to the container | `map(string)` | `{}` | no |
| secrets | Secrets to pass to the container | `map(string)` | `{}` | no |
| health_check_path | Health check path for ALB target group | `string` | `"/health"` | no |
| log_retention_days | Number of days to retain CloudWatch logs | `number` | `7` | no |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| cluster_arn | ARN of the ECS cluster |
| service_arn | ARN of the ECS service |
| service_url | URL to access the service |
| load_balancer_dns_name | DNS name of the load balancer |
| log_group_name | Name of the CloudWatch log group |

## Health Checks

The module configures two types of health checks:

1. **Container Health Check**: Runs inside the container using curl
2. **ALB Health Check**: HTTP health check from the load balancer

Both health checks target the `/health` endpoint by default, which should be implemented by all muppets.

## Security

- ECS tasks run in private subnets with no direct internet access
- Load balancer runs in public subnets and forwards traffic to private tasks
- Security groups follow least-privilege principles
- IAM roles provide minimal required permissions

## Monitoring

- CloudWatch logs with configurable retention (default: 7 days for cost optimization)
- Container Insights enabled for detailed metrics
- Auto-scaling based on CPU and memory utilization

## Cost Optimization

- Default log retention of 7 days to minimize CloudWatch costs
- Auto-scaling to handle traffic spikes efficiently
- Fargate Spot pricing can be enabled for non-production workloads

## Examples

### Minimal Configuration

```hcl
module "simple_muppet" {
  source = "../terraform-modules/fargate-service"

  service_name    = "simple-muppet"
  container_image = "my-registry/simple-muppet:latest"
  vpc_id          = "vpc-12345678"
  private_subnet_ids = ["subnet-12345678", "subnet-87654321"]
  public_subnet_ids  = ["subnet-abcdef12", "subnet-21fedcba"]
}
```

### Production Configuration

```hcl
module "production_muppet" {
  source = "../terraform-modules/fargate-service"

  service_name    = "production-muppet"
  container_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/muppet-platform/production-muppet:v1.2.3"
  
  # High-availability configuration
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids
  
  # Resource allocation for production workload
  cpu           = 1024
  memory        = 2048
  desired_count = 3
  
  # Auto-scaling for production traffic
  autoscaling_min_capacity = 2
  autoscaling_max_capacity = 20
  autoscaling_cpu_target   = 60
  
  # Production environment variables
  environment_variables = {
    ENVIRONMENT = "production"
    LOG_LEVEL   = "WARN"
    PORT        = "3000"
  }
  
  # Secrets from Parameter Store
  secrets = {
    DATABASE_URL = "/muppet-platform/production-muppet/database-url"
    JWT_SECRET   = "/muppet-platform/production-muppet/jwt-secret"
  }
  
  # Enhanced health checks
  health_check_path                = "/health/ready"
  health_check_healthy_threshold   = 3
  health_check_unhealthy_threshold = 2
  
  # Extended log retention for production
  log_retention_days = 30
  
  tags = {
    Environment = "production"
    Muppet      = "production-muppet"
    Team        = "platform"
  }
}
```