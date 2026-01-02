# Complete Node.js Express Muppet Module
# This module provides everything needed for a Node.js Express muppet
# Includes networking, fargate service, and all Node.js-specific configuration

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ECR Repository reference (created by CD workflow)
data "aws_ecr_repository" "main" {
  name = var.muppet_name
}

# Networking Module - Creates VPC, subnets, NAT gateways, and VPC endpoints
module "networking" {
  source = "../networking"
  
  name_prefix = var.muppet_name
  vpc_cidr    = var.vpc_cidr
  
  # Multi-AZ deployment for high availability
  public_subnet_count  = var.public_subnet_count
  private_subnet_count = var.private_subnet_count
  
  # Cost optimization based on environment
  single_nat_gateway   = var.environment != "production"
  enable_vpc_endpoints = var.environment == "production"
  
  # Enhanced security for production
  enable_network_acls = var.environment == "production"
  
  tags = local.common_tags
}

# Fargate Service Module - Creates complete ECS Fargate service with ALB
module "fargate_service" {
  source = "../fargate-service"
  
  service_name    = var.muppet_name
  cluster_name    = "${var.muppet_name}-cluster"
  container_image = "${data.aws_ecr_repository.main.repository_url}:${var.image_tag}"
  
  # Networking from shared module
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids
  
  # Resource allocation optimized for Node.js 20 LTS
  cpu    = var.cpu
  memory = var.memory
  
  # Auto-scaling configuration
  desired_count            = var.min_capacity
  autoscaling_min_capacity = var.min_capacity
  autoscaling_max_capacity = var.max_capacity
  autoscaling_cpu_target   = var.target_cpu_utilization
  autoscaling_memory_target = var.target_memory_utilization
  
  # Node.js 20 LTS optimized environment variables
  environment_variables = merge(var.additional_environment_variables, {
    NODE_ENV = var.environment
    PORT     = "3000"
    LOG_LEVEL = var.environment == "production" ? "info" : "debug"
    AWS_REGION = var.aws_region
    NODE_OPTIONS = "--max-old-space-size=${floor(var.memory * 0.8)}"  # 80% of container memory
    UV_THREADPOOL_SIZE = "16"  # Optimize for I/O operations
  })
  
  # Health check configuration optimized for Node.js applications
  health_check_path = "/health"
  health_check_enabled = true
  health_check_command = ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
  health_check_start_period = 60   # Node.js applications start faster than Java
  health_check_interval = 30
  health_check_timeout = 5
  health_check_retries = 3
  
  # Logging configuration with cost optimization
  log_retention_days = var.log_retention_days
  enable_container_insights = var.environment == "production"
  
  # Load balancer configuration with TLS-by-default
  create_load_balancer = true
  internal_load_balancer = false
  enable_https = var.enable_https
  certificate_arn = var.certificate_arn
  redirect_http_to_https = var.redirect_http_to_https
  ssl_policy = var.ssl_policy
  
  # Monitoring configuration
  enable_monitoring = var.environment == "production"
  
  tags = local.common_tags
}

# Common tags for all Node.js Express muppets
locals {
  # Base tags with all values
  base_tags = {
    MuppetName    = var.muppet_name
    Environment   = var.environment
    ManagedBy     = "muppet-platform"
    Template      = "node-express"
    Language      = "nodejs"
    Framework     = "express"
    NodeVersion   = "20-LTS"
    Architecture  = "ARM64"
    CreatedBy     = "muppet-node-express-module"
    CostCenter    = var.cost_center
    Owner         = var.owner_email
    Project       = var.muppet_name
    IaC           = "opentofu"
  }
  
  # Filter out empty values to prevent AWS tagging errors
  common_tags = {
    for key, value in local.base_tags : key => value
    if value != null && value != ""
  }
}