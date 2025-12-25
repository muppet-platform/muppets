# Outputs for Monitoring module

# Dashboard Information
output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

# Alarm Information
output "cpu_alarm_arn" {
  description = "ARN of the CPU utilization alarm"
  value       = var.enable_alarms ? aws_cloudwatch_metric_alarm.high_cpu[0].arn : null
}

output "memory_alarm_arn" {
  description = "ARN of the memory utilization alarm"
  value       = var.enable_alarms ? aws_cloudwatch_metric_alarm.high_memory[0].arn : null
}

output "response_time_alarm_arn" {
  description = "ARN of the response time alarm"
  value       = var.enable_alarms && var.load_balancer_arn_suffix != "" ? aws_cloudwatch_metric_alarm.high_response_time[0].arn : null
}

output "error_rate_alarm_arn" {
  description = "ARN of the 5XX error rate alarm"
  value       = var.enable_alarms && var.load_balancer_arn_suffix != "" ? aws_cloudwatch_metric_alarm.high_5xx_errors[0].arn : null
}

output "healthy_targets_alarm_arn" {
  description = "ARN of the healthy targets alarm"
  value       = var.enable_alarms && var.target_group_arn_suffix != "" ? aws_cloudwatch_metric_alarm.no_healthy_targets[0].arn : null
}

output "log_error_alarm_arn" {
  description = "ARN of the log-based error alarm"
  value       = var.enable_log_based_alarms ? aws_cloudwatch_metric_alarm.log_errors[0].arn : null
}

# SNS Topic Information
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarms"
  value       = var.create_sns_topic ? aws_sns_topic.alarms[0].arn : null
}

# CloudWatch Insights Queries
output "insights_query_names" {
  description = "Names of the CloudWatch Insights saved queries"
  value = var.create_insights_queries ? [
    aws_cloudwatch_query_definition.error_analysis[0].name,
    aws_cloudwatch_query_definition.performance_analysis[0].name,
    aws_cloudwatch_query_definition.request_volume[0].name
  ] : []
}

# Metric Filter Information
output "error_metric_filter_name" {
  description = "Name of the error log metric filter"
  value       = var.enable_log_based_alarms ? aws_cloudwatch_log_metric_filter.error_count[0].name : null
}

output "custom_metric_filter_names" {
  description = "Names of custom log metric filters"
  value       = [for k, v in aws_cloudwatch_log_metric_filter.custom_metrics : v.name]
}