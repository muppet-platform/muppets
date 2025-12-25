# Monitoring Module

This Terraform module creates comprehensive CloudWatch monitoring, alarms, and dashboards for Muppet Platform services. It provides cost-optimized monitoring with essential metrics and alerting.

## Features

- **CloudWatch Dashboard**: Visual monitoring with ECS, ALB, and log metrics
- **CloudWatch Alarms**: CPU, memory, response time, and error rate monitoring
- **Log-based Monitoring**: Error detection and custom metrics from application logs
- **SNS Integration**: Email notifications for critical alerts
- **CloudWatch Insights**: Saved queries for common troubleshooting scenarios
- **Cost Optimization**: 7-day log retention and efficient metric collection

## Usage

```hcl
module "monitoring" {
  source = "../terraform-modules/monitoring"

  service_name = "my-muppet"
  cluster_name = "muppet-platform"
  
  # Log configuration
  log_group_name = "/aws/fargate/my-muppet"
  
  # Load balancer metrics (optional)
  load_balancer_arn_suffix = "app/my-muppet-alb/1234567890abcdef"
  target_group_arn_suffix  = "targetgroup/my-muppet-tg/1234567890abcdef"
  
  # Alarm configuration
  enable_alarms = true
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  # Custom thresholds
  cpu_alarm_threshold          = 70
  memory_alarm_threshold       = 80
  response_time_alarm_threshold = 1.5
  
  # Email notifications
  create_sns_topic      = true
  alarm_email_endpoints = ["team@company.com"]
  
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
| aws_cloudwatch_dashboard.main | resource |
| aws_cloudwatch_metric_alarm.high_cpu | resource |
| aws_cloudwatch_metric_alarm.high_memory | resource |
| aws_cloudwatch_metric_alarm.high_response_time | resource |
| aws_cloudwatch_metric_alarm.high_5xx_errors | resource |
| aws_cloudwatch_metric_alarm.no_healthy_targets | resource |
| aws_cloudwatch_log_metric_filter.error_count | resource |
| aws_cloudwatch_metric_alarm.log_errors | resource |
| aws_sns_topic.alarms | resource |
| aws_cloudwatch_query_definition.error_analysis | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| service_name | Name of the service being monitored | `string` | n/a | yes |
| cluster_name | Name of the ECS cluster | `string` | n/a | yes |
| log_group_name | Name of the CloudWatch log group | `string` | n/a | yes |
| load_balancer_arn_suffix | ARN suffix of the load balancer | `string` | `""` | no |
| target_group_arn_suffix | ARN suffix of the target group | `string` | `""` | no |
| enable_alarms | Enable CloudWatch alarms | `bool` | `true` | no |
| cpu_alarm_threshold | CPU utilization threshold (percentage) | `number` | `80` | no |
| memory_alarm_threshold | Memory utilization threshold (percentage) | `number` | `85` | no |
| response_time_alarm_threshold | Response time threshold (seconds) | `number` | `2.0` | no |
| error_rate_alarm_threshold | 5XX error count threshold | `number` | `10` | no |
| create_sns_topic | Create SNS topic for notifications | `bool` | `false` | no |
| alarm_email_endpoints | Email addresses for notifications | `list(string)` | `[]` | no |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| dashboard_name | Name of the CloudWatch dashboard |
| dashboard_url | URL of the CloudWatch dashboard |
| cpu_alarm_arn | ARN of the CPU utilization alarm |
| memory_alarm_arn | ARN of the memory utilization alarm |
| sns_topic_arn | ARN of the SNS topic for alarms |

## Monitoring Strategy

### Core Metrics

1. **ECS Service Metrics**
   - CPU Utilization (threshold: 80%)
   - Memory Utilization (threshold: 85%)

2. **Load Balancer Metrics**
   - Request Count
   - Response Time (threshold: 2 seconds)
   - HTTP 2XX/4XX/5XX Counts
   - Healthy Target Count

3. **Application Logs**
   - Error Count (threshold: 5 errors in 5 minutes)
   - Custom business metrics

### Alarm Strategy

- **Evaluation Periods**: 2 consecutive periods to reduce false positives
- **Missing Data**: Treated as "not breaching" to handle intermittent metrics
- **Notification**: SNS topic with email subscriptions

### Cost Optimization

- **Log Retention**: 7 days default (configurable)
- **Metric Frequency**: 5-minute intervals for most metrics
- **Alarm Actions**: Only critical alarms trigger notifications

## Dashboard Widgets

The CloudWatch dashboard includes:

1. **ECS Service Metrics**: CPU and Memory utilization over time
2. **Load Balancer Metrics**: Request count, response time, and HTTP status codes
3. **Recent Logs**: Last 100 log entries for quick troubleshooting

## CloudWatch Insights Queries

Pre-configured saved queries for common investigations:

1. **Error Analysis**: Find and analyze ERROR log entries
2. **Performance Analysis**: Analyze request duration statistics
3. **Request Volume**: Track request volume over time

## Custom Metrics

You can define custom log-based metrics:

```hcl
custom_log_metrics = {
  "user_signups" = {
    pattern     = "[timestamp, request_id, level=\"INFO\", message=\"User signup completed\"]"
    metric_name = "UserSignups"
    value       = "1"
  }
  "payment_failures" = {
    pattern     = "[timestamp, request_id, level=\"ERROR\", message=\"Payment failed\"]"
    metric_name = "PaymentFailures"
    value       = "1"
  }
}
```

## Examples

### Basic Monitoring

```hcl
module "basic_monitoring" {
  source = "../terraform-modules/monitoring"

  service_name   = "simple-muppet"
  cluster_name   = "muppet-platform"
  log_group_name = "/aws/fargate/simple-muppet"
  
  # Minimal configuration
  enable_alarms = true
}
```

### Production Monitoring with Notifications

```hcl
module "production_monitoring" {
  source = "../terraform-modules/monitoring"

  service_name   = "production-muppet"
  cluster_name   = "muppet-platform"
  log_group_name = "/aws/fargate/production-muppet"
  
  # Load balancer monitoring
  load_balancer_arn_suffix = "app/production-muppet-alb/1234567890abcdef"
  target_group_arn_suffix  = "targetgroup/production-muppet-tg/1234567890abcdef"
  
  # Stricter thresholds for production
  cpu_alarm_threshold           = 60
  memory_alarm_threshold        = 70
  response_time_alarm_threshold = 1.0
  error_rate_alarm_threshold    = 5
  
  # Email notifications
  create_sns_topic      = true
  alarm_email_endpoints = [
    "oncall@company.com",
    "platform-team@company.com"
  ]
  
  # Custom business metrics
  custom_log_metrics = {
    "api_errors" = {
      pattern     = "[timestamp, level=\"ERROR\", message*=\"API\"]"
      metric_name = "APIErrors"
      value       = "1"
    }
  }
  
  tags = {
    Environment = "production"
    Muppet      = "production-muppet"
    Team        = "platform"
  }
}
```

## Integration with Fargate Service Module

```hcl
module "muppet_service" {
  source = "../terraform-modules/fargate-service"
  # ... fargate service configuration
}

module "muppet_monitoring" {
  source = "../terraform-modules/monitoring"

  service_name   = module.muppet_service.service_name
  cluster_name   = module.muppet_service.cluster_name
  log_group_name = module.muppet_service.log_group_name
  
  # Extract ARN suffixes for ALB metrics
  load_balancer_arn_suffix = split("/", module.muppet_service.load_balancer_arn)[1]
  target_group_arn_suffix  = split("/", module.muppet_service.target_group_arn)[1]
  
  alarm_actions = [aws_sns_topic.platform_alerts.arn]
  
  tags = var.tags
}
```