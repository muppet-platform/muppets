# Variables for ECR module

variable "registry_name" {
  description = "Name of the ECR registry"
  type        = string
  default     = "muppet-platform"
}

variable "enable_scanning" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "muppet-platform"
    Environment = "shared"
    ManagedBy   = "terraform"
  }
}