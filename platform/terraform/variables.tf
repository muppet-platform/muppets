# Variables for Muppet Platform Infrastructure

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# ECS Configuration
variable "cpu" {
  description = "CPU units for the platform service (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "memory" {
  description = "Memory in MB for the platform service"
  type        = number
  default     = 2048
}

variable "min_capacity" {
  description = "Minimum number of platform service instances (0 for cost optimization)"
  type        = number
  default     = 0
}

variable "max_capacity" {
  description = "Maximum number of platform service instances"
  type        = number
  default     = 2
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization percentage for auto scaling"
  type        = number
  default     = 70
}

variable "target_memory_utilization" {
  description = "Target memory utilization percentage for auto scaling"
  type        = number
  default     = 80
}

# Logging Configuration
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR."
  }
}

# GitHub Configuration
variable "github_organization" {
  description = "GitHub organization name"
  type        = string
  default     = "muppet-platform"
}

# HTTPS Configuration
variable "enable_https" {
  description = "Enable HTTPS with ACM certificate"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Platform domain name"
  type        = string
  default     = "muppet-platform.s3u.dev"
}

variable "parent_zone_id" {
  description = "Route 53 hosted zone ID for s3u.dev (required when enable_https is true)"
  type        = string
  default     = ""
}

# Cost and Ownership
variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "platform-engineering"
}

variable "owner_email" {
  description = "Owner email for resource tagging"
  type        = string
  default     = "platform-team@company.com"
}

# TLS Configuration for Muppets
variable "enable_muppet_tls_by_default" {
  description = "Enable TLS by default for all new muppets"
  type        = bool
  default     = true
}

variable "s3u_dev_zone_name" {
  description = "Route 53 hosted zone name for s3u.dev domain"
  type        = string
  default     = "s3u.dev"
  
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.s3u_dev_zone_name))
    error_message = "Zone name must be a valid domain name."
  }
}

variable "s3u_dev_zone_id" {
  description = "Route 53 hosted zone ID for s3u.dev domain"
  type        = string
  default     = ""  # Will be populated after zone creation
}

variable "muppet_wildcard_certificate_arn" {
  description = "ARN of the wildcard certificate for muppet endpoints (will be populated after certificate creation)"
  type        = string
  default     = ""
}

