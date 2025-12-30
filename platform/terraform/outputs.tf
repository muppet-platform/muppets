# Outputs for Muppet Platform Infrastructure

output "platform_url" {
  description = "URL of the deployed platform service"
  value       = var.enable_https ? "https://${var.domain_name}" : "http://${aws_lb.platform.dns_name}"
}

output "platform_health_url" {
  description = "Health check URL for the platform service"
  value       = var.enable_https ? "https://${var.domain_name}/health" : "http://${aws_lb.platform.dns_name}/health"
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.platform.dns_name
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.platform.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.platform.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.platform.name
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = data.aws_ecr_repository.platform.repository_url
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.platform.name
}

output "security_group_id" {
  description = "Security group ID for the platform service"
  value       = aws_security_group.platform.id
}

# Environment Information
output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "image_tag" {
  description = "Deployed image tag"
  value       = var.image_tag
}

# HTTPS Configuration (conditional outputs)
output "certificate_arn" {
  description = "ARN of the ACM certificate (when HTTPS is enabled)"
  value       = var.enable_https ? aws_acm_certificate.platform[0].arn : null
}

output "certificate_status" {
  description = "Status of the ACM certificate (when HTTPS is enabled)"
  value       = var.enable_https ? aws_acm_certificate.platform[0].status : null
}

output "domain_name" {
  description = "Platform domain name (when HTTPS is enabled)"
  value       = var.enable_https ? var.domain_name : null
}

output "https_url" {
  description = "HTTPS URL of the platform (when HTTPS is enabled)"
  value       = var.enable_https ? "https://${var.domain_name}" : null
}

output "https_health_url" {
  description = "HTTPS health check URL (when HTTPS is enabled)"
  value       = var.enable_https ? "https://${var.domain_name}/health" : null
}

# Monitoring URLs
output "cloudwatch_logs_url" {
  description = "CloudWatch logs URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.platform.name, "/", "$252F")}"
}

output "ecs_service_url" {
  description = "ECS service console URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/ecs/home?region=${var.aws_region}#/clusters/${aws_ecs_cluster.platform.name}/services/${aws_ecs_service.platform.name}/details"
}