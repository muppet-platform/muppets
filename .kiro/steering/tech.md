---
inclusion: always
---

# Technology Stack & Build System

## Core Platform Service
- **Language**: Python 3.11+
- **Framework**: FastAPI with Pydantic Settings
- **HTTP Client**: httpx for async calls
- **Testing**: pytest with moto for AWS mocking
- **Code Quality**: black, isort, mypy

## Infrastructure
- **IaC**: OpenTofu (not Terraform)
- **Container**: Rancher Desktop for local development
- **AWS**: ECS Fargate, ECR, CloudWatch, VPC
- **Local AWS**: LocalStack for development simulation

## Key Commands
```bash
# Development
make setup && make test-platform && make build-platform

# Platform service
cd platform && python3 -m uvicorn src.main:app --reload

# Infrastructure
make opentofu-init && make opentofu-plan && make opentofu-apply
```

## Configuration
- Environment variables with Pydantic validation
- Component-specific config.yaml files
- Structured JSON logging with 7-day CloudWatch retention