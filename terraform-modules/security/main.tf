# Security Module
# Provides IAM roles, policies, and security configurations for muppet applications

variable "service_name" {
  description = "Name of the service"
  type        = string
}

variable "create_execution_role" {
  description = "Create ECS execution role"
  type        = bool
  default     = true
}

variable "create_task_role" {
  description = "Create ECS task role"
  type        = bool
  default     = true
}

variable "enable_vulnerability_scanning" {
  description = "Enable vulnerability scanning"
  type        = bool
  default     = true
}

variable "secrets_manager_arns" {
  description = "List of Secrets Manager ARNs to grant access to"
  type        = list(string)
  default     = []
}

variable "vpc_id" {
  description = "VPC ID for security groups"
  type        = string
}

variable "enable_security_headers" {
  description = "Enable security headers"
  type        = bool
  default     = true
}

variable "enable_waf" {
  description = "Enable WAF protection"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# ECS Task Execution Role
resource "aws_iam_role" "execution" {
  count = var.create_execution_role ? 1 : 0
  name  = "${var.service_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "execution" {
  count      = var.create_execution_role ? 1 : 0
  role       = aws_iam_role.execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role
resource "aws_iam_role" "task" {
  count = var.create_task_role ? 1 : 0
  name  = "${var.service_name}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Secrets Manager access policy (if secrets provided)
resource "aws_iam_role_policy" "secrets_access" {
  count = var.create_task_role && length(var.secrets_manager_arns) > 0 ? 1 : 0
  name  = "${var.service_name}-secrets-access"
  role  = aws_iam_role.task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.secrets_manager_arns
      }
    ]
  })
}

# Security group for application
resource "aws_security_group" "app" {
  name_prefix = "${var.service_name}-app-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.service_name}-app-sg"
  })
}

# Outputs
output "execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = var.create_execution_role ? aws_iam_role.execution[0].arn : null
}

output "task_role_arn" {
  description = "ARN of the ECS task role"
  value       = var.create_task_role ? aws_iam_role.task[0].arn : null
}

output "security_group_id" {
  description = "Security group ID for the application"
  value       = aws_security_group.app.id
}