# Muppet Platform Infrastructure
# Deploys the core platform service to AWS ECS Fargate
# Follows "Simple by Default, Extensible by Choice" principle

terraform {
  required_version = ">= 1.5"
  
  backend "s3" {
    bucket = "muppet-platform-terraform-state"
    key    = "platform/terraform.tfstate"
    region = "us-west-2"
    
    # State locking
    dynamodb_table = "muppet-platform-terraform-locks"
    encrypt        = true
  }
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

# Get default VPC for simplified deployment
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ECR Repository is created by CD workflow step "Ensure ECR repository exists"
# Reference existing repository by name
data "aws_ecr_repository" "platform" {
  name = "muppet-platform"
}

# ECR Lifecycle Policy (separate resource)
resource "aws_ecr_lifecycle_policy" "platform" {
  repository = data.aws_ecr_repository.platform.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["main", "v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Security group for the platform service
resource "aws_security_group" "platform" {
  name_prefix = "muppet-platform-"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "muppet-platform-sg"
  })
}

# ECS Cluster for the platform
resource "aws_ecs_cluster" "platform" {
  name = "muppet-platform-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.platform.name
      }
    }
  }

  tags = local.common_tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "platform" {
  name              = "/ecs/muppet-platform"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "execution" {
  name = "muppet-platform-execution-role"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for SSM parameter access
resource "aws_iam_role_policy" "execution_ssm" {
  name = "muppet-platform-execution-ssm-policy"
  role = aws_iam_role.execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Resource = [
          aws_ssm_parameter.github_token.arn
        ]
      }
    ]
  })
}

# IAM Role for ECS Task (platform service permissions)
resource "aws_iam_role" "task" {
  name = "muppet-platform-task-role"

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

  tags = local.common_tags
}

# Platform service needs extensive AWS permissions for muppet management
resource "aws_iam_role_policy" "platform_permissions" {
  name = "muppet-platform-permissions"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # ECS permissions for muppet deployment
          "ecs:*",
          # ECR permissions for image management
          "ecr:*",
          # IAM permissions for role management
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PassRole",
          "iam:GetRole",
          "iam:ListRoles",
          # CloudWatch permissions for logging and monitoring
          "logs:*",
          "cloudwatch:*",
          # Application Load Balancer permissions
          "elasticloadbalancing:*",
          # Auto Scaling permissions
          "application-autoscaling:*",
          # VPC permissions for networking
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupEgress",
          # S3 permissions for terraform state
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          # DynamoDB permissions for terraform locking
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "*"
      }
    ]
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "platform" {
  family                   = "muppet-platform"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn           = aws_iam_role.task.arn
  
  # Use ARM64 architecture for better cost/performance
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([
    {
      name  = "muppet-platform"
      image = "${data.aws_ecr_repository.platform.repository_url}:${var.image_tag}"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "LOG_LEVEL"
          value = var.log_level
        },
        {
          name  = "INTEGRATION_MODE"
          value = "real"
        },
        {
          name  = "GITHUB_ORGANIZATION"
          value = var.github_organization
        }
      ]
      
      secrets = [
        {
          name      = "GITHUB_TOKEN"
          valueFrom = aws_ssm_parameter.github_token.arn
        }
      ]
      
      healthCheck = {
        command = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval = 30
        timeout = 10
        retries = 3
        startPeriod = 60
      }
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.platform.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = local.common_tags
}

# Application Load Balancer
resource "aws_lb" "platform" {
  name               = "muppet-platform-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.platform.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection = false

  tags = local.common_tags
}

resource "aws_lb_target_group" "platform" {
  name        = "muppet-platform-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 10
    unhealthy_threshold = 3
  }

  tags = local.common_tags
}

resource "aws_lb_listener" "platform" {
  load_balancer_arn = aws_lb.platform.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.platform.arn
  }
}

# ECS Service
resource "aws_ecs_service" "platform" {
  name            = "muppet-platform"
  cluster         = aws_ecs_cluster.platform.id
  task_definition = aws_ecs_task_definition.platform.arn
  desired_count   = var.min_capacity
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.platform.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.platform.arn
    container_name   = "muppet-platform"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.platform]

  tags = local.common_tags
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "platform" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.platform.name}/${aws_ecs_service.platform.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "platform_cpu" {
  name               = "muppet-platform-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.platform.resource_id
  scalable_dimension = aws_appautoscaling_target.platform.scalable_dimension
  service_namespace  = aws_appautoscaling_target.platform.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = var.target_cpu_utilization
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "platform_memory" {
  name               = "muppet-platform-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.platform.resource_id
  scalable_dimension = aws_appautoscaling_target.platform.scalable_dimension
  service_namespace  = aws_appautoscaling_target.platform.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = var.target_memory_utilization
  }
}

# SSM Parameter for GitHub Token (must be created manually or via separate process)
resource "aws_ssm_parameter" "github_token" {
  name  = "/muppet-platform/github-token"
  type  = "SecureString"
  value = "placeholder-token-update-manually"

  tags = merge(local.common_tags, {
    Name = "muppet-platform-github-token"
  })

  lifecycle {
    ignore_changes = [value]
  }
}

# CloudWatch Alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "muppet-platform-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors platform CPU utilization"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    ServiceName = aws_ecs_service.platform.name
    ClusterName = aws_ecs_cluster.platform.name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "muppet-platform-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors platform memory utilization"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    ServiceName = aws_ecs_service.platform.name
    ClusterName = aws_ecs_cluster.platform.name
  }

  tags = local.common_tags
}

# Common tags and local values
locals {
  common_tags = {
    Service       = "muppet-platform"
    Environment   = var.environment
    ManagedBy     = "terraform"
    Repository    = "muppet-platform/muppets"
    Component     = "platform-service"
    Language      = "python"
    Framework     = "fastapi"
    CostCenter    = var.cost_center
    Owner         = var.owner_email
    Project       = "muppet-platform"
  }
}