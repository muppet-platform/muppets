# Outputs for Fargate Service module

# Cluster Information
output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

# Service Information
output "service_id" {
  description = "ID of the ECS service"
  value       = aws_ecs_service.main.id
}

output "service_arn" {
  description = "ARN of the ECS service"
  value       = aws_ecs_service.main.id
}

output "service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.main.name
}

# Task Definition Information
output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = aws_ecs_task_definition.main.arn
}

output "task_definition_family" {
  description = "Family of the task definition"
  value       = aws_ecs_task_definition.main.family
}

output "task_definition_revision" {
  description = "Revision of the task definition"
  value       = aws_ecs_task_definition.main.revision
}

# Load Balancer Information
output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = var.create_load_balancer ? aws_lb.main[0].arn : null
}

output "load_balancer_dns_name" {
  description = "DNS name of the load balancer"
  value       = var.create_load_balancer ? aws_lb.main[0].dns_name : null
}

output "load_balancer_zone_id" {
  description = "Zone ID of the load balancer"
  value       = var.create_load_balancer ? aws_lb.main[0].zone_id : null
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = var.create_load_balancer ? aws_lb_target_group.main[0].arn : null
}

# Security Group Information
output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = aws_security_group.ecs.id
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = var.create_load_balancer ? aws_security_group.alb[0].id : null
}

# IAM Role Information
output "execution_role_arn" {
  description = "ARN of the task execution role"
  value       = aws_iam_role.execution.arn
}

output "task_role_arn" {
  description = "ARN of the task role"
  value       = aws_iam_role.task.arn
}

# CloudWatch Log Group Information
output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app.arn
}

# Auto Scaling Information
output "autoscaling_target_resource_id" {
  description = "Resource ID of the auto scaling target"
  value       = var.enable_autoscaling ? aws_appautoscaling_target.ecs_target[0].resource_id : null
}

# Service URLs
output "service_url" {
  description = "HTTP URL to access the service"
  value       = var.create_load_balancer ? "http://${aws_lb.main[0].dns_name}" : null
}

output "service_https_url" {
  description = "HTTPS URL to access the service"
  value       = var.create_load_balancer && var.enable_https ? "https://${aws_lb.main[0].dns_name}" : null
}

output "service_domain_url" {
  description = "Domain-based URL to access the service"
  value       = var.create_load_balancer && var.domain_name != "" ? (var.enable_https ? "https://${var.domain_name}" : "http://${var.domain_name}") : null
}

# TLS Certificate Information
output "certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = var.create_certificate ? aws_acm_certificate.main[0].arn : var.certificate_arn
}

output "certificate_domain_validation_options" {
  description = "Domain validation options for the certificate"
  value       = var.create_certificate ? aws_acm_certificate.main[0].domain_validation_options : null
}