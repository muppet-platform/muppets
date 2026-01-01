# Variables for Node.js Express Muppet Module
# Provides sensible defaults for all Node.js Express applications

# Required Configuration
variable "muppet_name" {
  description = "Name of the muppet"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.muppet_name))
    error_message = "Muppet name must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

# Networking Configuration (with sensible defaults)
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_count" {
  description = "Number of public subnets to create"
  type        = number
  default     = 2
}

variable "private_subnet_count" {
  description = "Number of private subnets to create"
  type        = number
  default     = 2
}

# Container Configuration (optimized for Node.js 20 LTS)
variable "image_tag" {
  description = "Container image tag"
  type        = string
  default     = "latest"
}

variable "cpu" {
  description = "CPU units for the container (256 = 0.25 vCPU)"
  type        = number
  default     = 256  # Optimized for Node.js applications (lighter than Java)
  
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "memory" {
  description = "Memory for the container in MB"
  type        = number
  default     = 512  # Optimized for Node.js applications (lighter than Java)
  
  validation {
    condition     = var.memory >= 512 && var.memory <= 30720
    error_message = "Memory must be between 512 MB and 30720 MB."
  }
}

# Auto-scaling Configuration (with sensible defaults)
variable "min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "target_cpu_utilization" {
  description = "Target CPU utilization for auto-scaling"
  type        = number
  default     = 70
}

variable "target_memory_utilization" {
  description = "Target memory utilization for auto-scaling"
  type        = number
  default     = 80
}

# Monitoring Configuration (with cost optimization)
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

# SSL/TLS Configuration (TLS-by-default enabled)
variable "enable_https" {
  description = "Enable HTTPS listener on the load balancer"
  type        = bool
  default     = true  # TLS-by-default
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener"
  type        = string
  default     = ""  # Will be auto-populated by platform TLS auto-generator
}

variable "domain_name" {
  description = "Custom domain name for the muppet (e.g., muppet-name.s3u.dev)"
  type        = string
  default     = ""
  
  validation {
    condition = var.domain_name == "" || can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]\\.[a-z0-9][a-z0-9-]*[a-z0-9]$", var.domain_name))
    error_message = "Domain name must be a valid FQDN (e.g., muppet-name.s3u.dev)."
  }
}

variable "zone_id" {
  description = "Route 53 hosted zone ID for DNS record creation"
  type        = string
  default     = ""
}

variable "redirect_http_to_https" {
  description = "Redirect HTTP traffic to HTTPS"
  type        = bool
  default     = true
}

variable "ssl_policy" {
  description = "SSL policy for HTTPS listener"
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  
  validation {
    condition = contains([
      "ELBSecurityPolicy-TLS13-1-2-2021-06",
      "ELBSecurityPolicy-TLS-1-2-2017-01",
      "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"
    ], var.ssl_policy)
    error_message = "SSL policy must be a valid ELB security policy."
  }
}

variable "create_dns_record" {
  description = "Create Route 53 DNS record for custom domain"
  type        = bool
  default     = false  # Only create if domain_name and zone_id are provided
}

# Extension Points for Advanced Users
variable "additional_environment_variables" {
  description = "Additional environment variables to pass to the container"
  type        = map(string)
  default     = {}
}

variable "additional_iam_policy_statements" {
  description = "Additional IAM policy statements for the task role"
  type        = list(any)
  default     = []
}

variable "additional_security_group_rules" {
  description = "Additional security group rules for the ECS service"
  type = list(object({
    type        = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}

# Cost Management Configuration (optional)
variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "engineering"
}

variable "owner_email" {
  description = "Email address of the service owner"
  type        = string
  default     = ""
}