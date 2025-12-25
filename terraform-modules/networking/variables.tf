# Variables for Networking module

# Basic Configuration
variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "muppet-platform"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

# Subnet Configuration
variable "public_subnet_count" {
  description = "Number of public subnets to create"
  type        = number
  default     = 2
  
  validation {
    condition     = var.public_subnet_count >= 1 && var.public_subnet_count <= 6
    error_message = "Public subnet count must be between 1 and 6."
  }
}

variable "private_subnet_count" {
  description = "Number of private subnets to create"
  type        = number
  default     = 2
  
  validation {
    condition     = var.private_subnet_count >= 1 && var.private_subnet_count <= 6
    error_message = "Private subnet count must be between 1 and 6."
  }
}

# NAT Gateway Configuration
variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway for all private subnets (cost optimization)"
  type        = bool
  default     = false
}

# VPC Endpoints Configuration
variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services (cost optimization)"
  type        = bool
  default     = true
}

# Network ACLs Configuration
variable "enable_network_acls" {
  description = "Enable custom Network ACLs for additional security"
  type        = bool
  default     = false
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