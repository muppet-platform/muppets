# Variables for Monitoring module

# Basic Configuration
variable "service_name" {
  description = "Name of the service being monitored"
  type        = string
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  type        = string
  default     = ""
}

# Log Configuration
variable "log_group_name" {
  description = "Name of the CloudWatch log group"
  type        = string
}

# Load Balancer Configuration
variable "load_balancer_arn_suffix" {
  description = "ARN suffix of the load balancer (for ALB metrics)"
  type        = string
  default     = ""
}

variable "target_group_arn_suffix" {
  description = "ARN suffix of the target group (for target group metrics)"
  type        = string
  default     = ""
}

# Alarm Configuration
variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers"
  type        = list(string)
  default     = []
}

# Alarm Thresholds
variable "cpu_alarm_threshold" {
  description = "CPU utilization threshold for alarm (percentage)"
  type        = number
  default     = 80
}

variable "memory_alarm_threshold" {
  description = "Memory utilization threshold for alarm (percentage)"
  type        = number
  default     = 85
}

variable "response_time_alarm_threshold" {
  description = "Response time threshold for alarm (seconds)"
  type        = number
  default     = 2.0
}

variable "error_rate_alarm_threshold" {
  description = "5XX error count threshold for alarm"
  type        = number
  default     = 10
}

# Log-based Monitoring
variable "enable_log_based_alarms" {
  description = "Enable log-based alarms"
  type        = bool
  default     = true
}

variable "error_log_pattern" {
  description = "Log pattern to match for error detection"
  type        = string
  default     = "[ERROR]"
}

variable "log_error_alarm_threshold" {
  description = "Number of log errors to trigger alarm"
  type        = number
  default     = 5
}

# Custom Metrics
variable "custom_log_metrics" {
  description = "Custom log-based metrics to create"
  type = map(object({
    pattern     = string
    metric_name = string
    value       = string
  }))
  default = {}
}

# SNS Configuration
variable "create_sns_topic" {
  description = "Create SNS topic for alarm notifications"
  type        = bool
  default     = false
}

variable "alarm_email_endpoints" {
  description = "Email addresses to receive alarm notifications"
  type        = list(string)
  default     = []
}

# CloudWatch Insights
variable "create_insights_queries" {
  description = "Create CloudWatch Insights saved queries"
  type        = bool
  default     = true
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "muppet-platform"
    ManagedBy = "terraform"
  }
}