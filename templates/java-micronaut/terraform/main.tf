# {{muppet_name}} Muppet Infrastructure
# This configuration uses shared Terraform modules from the platform

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Use shared ECR module for container registry
module "ecr" {
  source = "git::https://github.com/muppet-platform/terraform-modules.git//ecr?ref=v1.0.0"
  
  repository_name = var.muppet_name
  environment     = var.environment
  
  tags = {
    MuppetName  = var.muppet_name
    Environment = var.environment
    ManagedBy   = "muppet-platform"
  }
}

# Use shared networking module
module "networking" {
  source = "git::https://github.com/muppet-platform/terraform-modules.git//networking?ref=v1.0.0"
  
  vpc_name    = "${var.muppet_name}-vpc"
  environment = var.environment
  
  tags = {
    MuppetName  = var.muppet_name
    Environment = var.environment
    ManagedBy   = "muppet-platform"
  }
}

# Use shared Fargate service module
module "fargate_service" {
  source = "git::https://github.com/muppet-platform/terraform-modules.git//fargate-service?ref=v1.0.0"
  
  service_name     = var.muppet_name
  cluster_name     = "${var.muppet_name}-cluster"
  environment      = var.environment
  
  # Container configuration
  container_image = "${module.ecr.repository_url}:latest"
  container_port  = 3000
  
  # Networking
  vpc_id              = module.networking.vpc_id
  private_subnet_ids  = module.networking.private_subnet_ids
  public_subnet_ids   = module.networking.public_subnet_ids
  
  # Health check configuration
  health_check_path = "/health"
  
  # Auto-scaling configuration
  min_capacity = 1
  max_capacity = 10
  target_cpu   = 70
  
  tags = {
    MuppetName  = var.muppet_name
    Environment = var.environment
    ManagedBy   = "muppet-platform"
  }
}

# Use shared monitoring module
module "monitoring" {
  source = "git::https://github.com/muppet-platform/terraform-modules.git//monitoring?ref=v1.0.0"
  
  service_name = var.muppet_name
  environment  = var.environment
  
  # CloudWatch configuration
  log_group_name        = "/aws/fargate/${var.muppet_name}"
  log_retention_days    = 7  # Cost-optimized retention
  
  # Metrics and alarms
  cluster_name = module.fargate_service.cluster_name
  service_name_full = module.fargate_service.service_name
  
  # Cost optimization
  enable_xray = false  # Disabled by default for cost optimization
  
  tags = {
    MuppetName  = var.muppet_name
    Environment = var.environment
    ManagedBy   = "muppet-platform"
  }
}