# Technology Stack & Build System

## Core Platform Service

**Language**: Python 3.x  
**Framework**: FastAPI  
**Configuration**: Pydantic Settings with environment variable support  
**HTTP Client**: httpx for async external API calls  

### Key Dependencies

- **FastAPI**: 0.104.1 - Modern async web framework
- **Pydantic**: 2.5.0 - Data validation and settings management
- **Uvicorn**: 0.24.0 - ASGI server with hot reload support
- **Boto3**: 1.34.0 - AWS SDK for Python
- **PyGithub**: 2.1.1 - GitHub API client
- **python-json-logger**: 2.0.7 - Structured logging

### Development Tools

- **Testing**: pytest with asyncio support, moto for AWS mocking
- **Code Quality**: black (formatting), isort (imports), flake8 (linting), mypy (type checking)
- **Coverage**: pytest-cov for test coverage reporting

## Infrastructure

**IaC**: OpenTofu for all infrastructure components  
**Container Runtime**: Rancher Desktop for local development  
**AWS Services**: ECS Fargate, ECR, CloudWatch, VPC  
**Local AWS**: LocalStack for development simulation  

## Common Commands

### Development
```bash
# Set up development environment
make setup

# Run platform tests
make test-platform

# Build platform service
make build-platform

# Clean build artifacts
make clean
```

### Platform Service
```bash
# Run locally with hot reload
cd platform
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
cd platform
python3 -m pytest

# Code formatting and linting
cd platform
python3 -m black src/ tests/
python3 -m isort src/ tests/
python3 -m flake8 src/ tests/
python3 -m mypy src/
```

### Infrastructure
```bash
# Initialize OpenTofu modules
make opentofu-init

# Plan infrastructure changes
make opentofu-plan

# Apply infrastructure changes
make opentofu-apply
```

## Configuration Management

- **Environment Variables**: All configuration via environment variables with sensible defaults
- **Pydantic Settings**: Type-safe configuration with validation
- **Component Configs**: Each component has its own config.yaml file
- **Global Settings**: Shared settings in muppet-platform.yaml

## Logging & Monitoring

- **Structured Logging**: JSON format with python-json-logger
- **Log Levels**: Configurable via LOG_LEVEL environment variable
- **CloudWatch**: 7-day retention for cost optimization
- **X-Ray**: Disabled by default for cost optimization