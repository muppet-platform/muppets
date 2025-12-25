# Outputs for IAM module

# ECS Execution Role
output "ecs_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "ecs_execution_role_name" {
  description = "Name of the ECS task execution role"
  value       = aws_iam_role.ecs_execution_role.name
}

# ECS Task Role
output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_task_role_name" {
  description = "Name of the ECS task role"
  value       = aws_iam_role.ecs_task_role.name
}

# Platform Service Role
output "platform_service_role_arn" {
  description = "ARN of the platform service role"
  value       = var.create_platform_service_role ? aws_iam_role.platform_service_role[0].arn : null
}

output "platform_service_role_name" {
  description = "Name of the platform service role"
  value       = var.create_platform_service_role ? aws_iam_role.platform_service_role[0].name : null
}

# GitHub Actions Role
output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions role"
  value       = var.create_github_actions_role ? aws_iam_role.github_actions_role[0].arn : null
}

output "github_actions_role_name" {
  description = "Name of the GitHub Actions role"
  value       = var.create_github_actions_role ? aws_iam_role.github_actions_role[0].name : null
}

# Custom Policies
output "custom_policy_arns" {
  description = "ARNs of custom IAM policies"
  value       = { for k, v in aws_iam_policy.custom_policies : k => v.arn }
}

output "custom_policy_names" {
  description = "Names of custom IAM policies"
  value       = { for k, v in aws_iam_policy.custom_policies : k => v.name }
}