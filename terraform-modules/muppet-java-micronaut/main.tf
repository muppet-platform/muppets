# Complete Java Micronaut Muppet Module
# This module provides everything needed for a Java Micronaut muppet
# Includes networking, fargate service, and all Java-specific configuration

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
  
  # Resource allocation optimized for Java 21 LTS
  cpu    = var.cpu
  memory = var.memory
  
  # Auto-scaling configuration
  desired_count            = var.min_capacity
  autoscaling_min_capacity = var.min_capacity
  autoscaling_max_capacity = var.max_capacity
  autoscaling_cpu_target   = var.target_cpu_utilization
  autoscaling_memory_target = var.target_memory_utilization
  
  # Java 21 LTS optimized environment variables
  environment_variables = merge(var.additional_environment_variables, {
    JAVA_OPTS = "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC -XX:+UseStringDeduplication"
    JVM_ARGS  = "-Djava.security.egd=file:/dev/./urandom -XX:+EnableDynamicAgentLoading"
    JAVA_VERSION = "21"
    JAVA_DISTRIBUTION = "amazon-corretto"
    SERVER_PORT = "3000"
    MICRONAUT_ENVIRONMENTS = var.environment
  })
  
  # Health check configuration optimized for Java applications
  health_check_path = "/health"
  health_check_enabled = true
  health_check_command = ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
  health_check_start_period = 120  # Java applications need more startup time
  health_check_interval = 30
  health_check_timeout = 10
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

# Common tags for all Java Micronaut muppets
locals {
  # Base tags with all values
  base_tags = {
    MuppetName    = var.muppet_name
    Environment   = var.environment
    ManagedBy     = "muppet-platform"
    Template      = "java-micronaut"
    Language      = "java"
    Framework     = "micronaut"
    JavaVersion   = "21-LTS"
    Architecture  = "X86_64"
    CreatedBy     = "muppet-java-micronaut-module"
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