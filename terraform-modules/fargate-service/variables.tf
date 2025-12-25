# Variables for Fargate Service module

# Basic Configuration
variable "service_name" {
  description = "Name of the ECS service"
  type        = string
}

variable "cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "muppet-platform"
}

variable "container_image" {
  description = "Docker image to run in the container"
  type        = string
}

variable "container_port" {
  description = "Port on which the container listens"
  type        = number
  default     = 3000
}

# Resource Configuration
variable "cpu" {
  description = "Number of CPU units for the task"
  type        = number
  default     = 256
  
  validation {
    condition = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "memory" {
  description = "Amount of memory (in MiB) for the task"
  type        = number
  default     = 512
  
  validation {
    condition = var.memory >= 512 && var.memory <= 30720
    error_message = "Memory must be between 512 and 30720 MiB."
  }
}

# Networking Configuration
variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS service"
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for load balancer"
  type        = list(string)
  default     = []
}

variable "assign_public_ip" {
  description = "Assign a public IP address to the ENI"
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the service"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# Load Balancer Configuration
variable "create_load_balancer" {
  description = "Whether to create an Application Load Balancer"
  type        = bool
  default     = true
}

variable "internal_load_balancer" {
  description = "Whether the load balancer is internal"
  type        = bool
  default     = false
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection on the load balancer"
  type        = bool
  default     = false
}

# Service Configuration
variable "desired_count" {
  description = "Number of instances of the task definition to place and keep running"
  type        = number
  default     = 1
}

variable "deployment_maximum_percent" {
  description = "Upper limit on the number of running tasks during deployment"
  type        = number
  default     = 200
}

variable "deployment_minimum_healthy_percent" {
  description = "Lower limit on the number of running tasks during deployment"
  type        = number
  default     = 50
}

# Health Check Configuration
variable "health_check_enabled" {
  description = "Enable container health check"
  type        = bool
  default     = true
}

variable "health_check_command" {
  description = "Command to run for container health check"
  type        = list(string)
  default     = ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
}

variable "health_check_interval" {
  description = "Time period in seconds between each health check execution"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Time period in seconds to wait for a health check to succeed"
  type        = number
  default     = 5
}

variable "health_check_retries" {
  description = "Number of times to retry a failed health check"
  type        = number
  default     = 3
}

variable "health_check_start_period" {
  description = "Grace period in seconds to provide containers time to bootstrap"
  type        = number
  default     = 60
}

# ALB Health Check Configuration
variable "health_check_path" {
  description = "Health check path for ALB target group"
  type        = string
  default     = "/health"
}

variable "health_check_matcher" {
  description = "HTTP codes to use when checking for a successful response from a target"
  type        = string
  default     = "200"
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive health checks successes required"
  type        = number
  default     = 2
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive health check failures required"
  type        = number
  default     = 3
}

# Auto Scaling Configuration
variable "enable_autoscaling" {
  description = "Enable auto scaling for the ECS service"
  type        = bool
  default     = true
}

variable "autoscaling_min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "autoscaling_cpu_target" {
  description = "Target CPU utilization percentage for auto scaling"
  type        = number
  default     = 70
}

variable "autoscaling_memory_target" {
  description = "Target memory utilization percentage for auto scaling"
  type        = number
  default     = 80
}

# Environment Configuration
variable "environment_variables" {
  description = "Environment variables to pass to the container"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secrets to pass to the container (from Parameter Store or Secrets Manager)"
  type        = map(string)
  default     = {}
}

# IAM Configuration
variable "task_role_policy_statements" {
  description = "List of IAM policy statements for the task role"
  type        = list(any)
  default     = []
}

# Logging Configuration
variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7
}

variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights for the cluster"
  type        = bool
  default     = true
}

# Tags
variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "muppet-platform"
    ManagedBy   = "terraform"
  }
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

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
  description = "Error rate threshold for alarm (count of 5xx errors)"
  type        = number
  default     = 10
}

variable "alarm_actions" {
  description = "List of ARNs to notify when alarm triggers (e.g., SNS topics)"
  type        = list(string)
  default     = []
}