# Variables for IAM module

# Basic Configuration
variable "name_prefix" {
  description = "Prefix for IAM resource names"
  type        = string
  default     = "muppet-platform"
}

# Platform Service Role Configuration
variable "create_platform_service_role" {
  description = "Create IAM role for platform service"
  type        = bool
  default     = false
}

# GitHub Actions Role Configuration
variable "create_github_actions_role" {
  description = "Create IAM role for GitHub Actions CI/CD"
  type        = bool
  default     = false
}

variable "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  type        = string
  default     = ""
}

variable "github_repository_subjects" {
  description = "List of GitHub repository subjects allowed to assume the role"
  type        = list(string)
  default     = []
}

# Custom Policies Configuration
variable "custom_policies" {
  description = "Map of custom IAM policies to create and attach to the task role"
  type = map(object({
    description     = string
    policy_document = string
  }))
  default = {}
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