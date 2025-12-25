# Monitoring Module
# This module creates CloudWatch monitoring, alarms, and dashboards for the Muppet Platform

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.service_name, "ClusterName", var.cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "ECS Service Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.load_balancer_arn_suffix],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Load Balancer Metrics"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6

        properties = {
          query   = "SOURCE '${var.log_group_name}' | fields @timestamp, @message | sort @timestamp desc | limit 100"
          region  = data.aws_region.current.name
          title   = "Recent Logs"
        }
      }
    ]
  })

  tags = var.tags
}

# CloudWatch Alarms

# High CPU Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.service_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ServiceName = var.service_name
    ClusterName = var.cluster_name
  }

  tags = var.tags
}

# High Memory Utilization Alarm
resource "aws_cloudwatch_metric_alarm" "high_memory" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.service_name}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.memory_alarm_threshold
  alarm_description   = "This metric monitors ECS memory utilization"
  alarm_actions       = var.alarm_actions

  dimensions = {
    ServiceName = var.service_name
    ClusterName = var.cluster_name
  }

  tags = var.tags
}

# High Response Time Alarm
resource "aws_cloudwatch_metric_alarm" "high_response_time" {
  count = var.enable_alarms && var.load_balancer_arn_suffix != "" ? 1 : 0

  alarm_name          = "${var.service_name}-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = var.response_time_alarm_threshold
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = var.alarm_actions

  dimensions = {
    LoadBalancer = var.load_balancer_arn_suffix
  }

  tags = var.tags
}

# High Error Rate Alarm (5XX errors)
resource "aws_cloudwatch_metric_alarm" "high_5xx_errors" {
  count = var.enable_alarms && var.load_balancer_arn_suffix != "" ? 1 : 0

  alarm_name          = "${var.service_name}-high-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_rate_alarm_threshold
  alarm_description   = "This metric monitors 5XX error rate"
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.load_balancer_arn_suffix
  }

  tags = var.tags
}

# Service Unavailable Alarm (no healthy targets)
resource "aws_cloudwatch_metric_alarm" "no_healthy_targets" {
  count = var.enable_alarms && var.target_group_arn_suffix != "" ? 1 : 0

  alarm_name          = "${var.service_name}-no-healthy-targets"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors healthy target count"
  alarm_actions       = var.alarm_actions

  dimensions = {
    TargetGroup  = var.target_group_arn_suffix
    LoadBalancer = var.load_balancer_arn_suffix
  }

  tags = var.tags
}

# Log-based Error Alarm
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  count = var.enable_log_based_alarms ? 1 : 0

  name           = "${var.service_name}-error-count"
  log_group_name = var.log_group_name
  pattern        = var.error_log_pattern

  metric_transformation {
    name      = "${var.service_name}-ErrorCount"
    namespace = "MuppetPlatform/Logs"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "log_errors" {
  count = var.enable_log_based_alarms ? 1 : 0

  alarm_name          = "${var.service_name}-log-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "${var.service_name}-ErrorCount"
  namespace           = "MuppetPlatform/Logs"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.log_error_alarm_threshold
  alarm_description   = "This metric monitors application errors in logs"
  alarm_actions       = var.alarm_actions
  treat_missing_data  = "notBreaching"

  tags = var.tags
}

# Custom Metrics (for application-specific monitoring)
resource "aws_cloudwatch_log_metric_filter" "custom_metrics" {
  for_each = var.custom_log_metrics

  name           = "${var.service_name}-${each.key}"
  log_group_name = var.log_group_name
  pattern        = each.value.pattern

  metric_transformation {
    name      = "${var.service_name}-${each.value.metric_name}"
    namespace = "MuppetPlatform/Custom"
    value     = each.value.value
  }
}

# SNS Topic for Alarms (if not provided)
resource "aws_sns_topic" "alarms" {
  count = var.create_sns_topic ? 1 : 0

  name = "${var.service_name}-alarms"
  tags = var.tags
}

resource "aws_sns_topic_subscription" "email" {
  count = var.create_sns_topic && length(var.alarm_email_endpoints) > 0 ? length(var.alarm_email_endpoints) : 0

  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email_endpoints[count.index]
}

# CloudWatch Insights Queries (saved queries for common investigations)
resource "aws_cloudwatch_query_definition" "error_analysis" {
  count = var.create_insights_queries ? 1 : 0

  name = "${var.service_name}-error-analysis"

  log_group_names = [var.log_group_name]

  query_string = <<EOF
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
EOF
}

resource "aws_cloudwatch_query_definition" "performance_analysis" {
  count = var.create_insights_queries ? 1 : 0

  name = "${var.service_name}-performance-analysis"

  log_group_names = [var.log_group_name]

  query_string = <<EOF
fields @timestamp, @message, @duration
| filter @message like /request/
| stats avg(@duration), max(@duration), min(@duration) by bin(5m)
| sort @timestamp desc
EOF
}

resource "aws_cloudwatch_query_definition" "request_volume" {
  count = var.create_insights_queries ? 1 : 0

  name = "${var.service_name}-request-volume"

  log_group_names = [var.log_group_name]

  query_string = <<EOF
fields @timestamp, @message
| filter @message like /request/
| stats count() by bin(5m)
| sort @timestamp desc
EOF
}