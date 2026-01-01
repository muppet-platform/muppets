# Outputs for Java Micronaut Muppet Module
# Provides essential information for developers and CI/CD

# Application URLs
output "service_url" {
  description = "URL to access the service (HTTPS by default)"
  value       = var.enable_https && var.domain_name != "" ? "https://${var.domain_name}" : "http://${module.fargate_service.alb_dns_name}"
}

output "application_url" {
  description = "Application URL (alias for service_url)"
  value       = var.enable_https && var.domain_name != "" ? "https://${var.domain_name}" : "http://${module.fargate_service.alb_dns_name}"
}

output "health_check_url" {
  description = "Health check endpoint URL"
  value       = "${var.enable_https && var.domain_name != "" ? "https://${var.domain_name}" : "http://${module.fargate_service.alb_dns_name}"}/health"
}

# Load Balancer Information
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.fargate_service.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.fargate_service.alb_zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.fargate_service.alb_arn
}

# Service Information
output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.fargate_service.ecs_service_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.fargate_service.ecs_cluster_name
}

output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = module.fargate_service.task_definition_arn
}

# Networking Information
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

# Container Registry Information
output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = data.aws_ecr_repository.main.repository_url
}

# TLS Information
output "custom_domain_url" {
  description = "Custom domain URL (if configured)"
  value       = var.enable_https && var.domain_name != "" ? "https://${var.domain_name}" : null
}

output "tls_enabled" {
  description = "Whether TLS/HTTPS is enabled"
  value       = var.enable_https
}

# Deployment Information for CI/CD
output "deployment_info" {
  description = "Deployment information for CI/CD pipelines"
  value = {
    service_name      = module.fargate_service.ecs_service_name
    cluster_name      = module.fargate_service.ecs_cluster_name
    container_name    = var.muppet_name
    container_port    = 3000
    load_balancer_dns = module.fargate_service.alb_dns_name
    health_check_path = "/health"
    environment       = var.environment
    tls_enabled       = var.enable_https
    custom_domain     = var.domain_name
  }
}