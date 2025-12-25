output "service_url" {
  description = "URL of the deployed service"
  value       = module.fargate_service.service_url
}

output "ecr_repository_url" {
  description = "ECR repository URL for the container image"
  value       = module.ecr.repository_url
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = module.monitoring.log_group_name
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = module.fargate_service.cluster_name
}

output "service_name" {
  description = "ECS service name"
  value       = module.fargate_service.service_name
}