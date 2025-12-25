# Muppet Platform - Templates

This directory contains muppet template development tools and the Java Micronaut template for creating standardized applications.

## Structure

- `java-micronaut/` - Java Micronaut template with Amazon Corretto 21 LTS
- `template-tools/` - Template development utilities
- `tests/` - Template validation tests
- `.github/workflows/` - Template CI/CD

## Template Development

The Java Micronaut template provides a complete, production-ready application structure with:

- **Amazon Corretto 21 LTS**: Long-term support Java distribution optimized for AWS
- **Micronaut Framework**: Modern, JVM-based framework for microservices
- **Gradle Build System**: Fast, flexible build automation
- **Comprehensive Testing**: Unit tests, integration tests, and property-based testing
- **Docker Support**: Multi-stage builds with Alpine Linux base images
- **AWS Integration**: Ready for deployment on AWS Fargate
- **Security Best Practices**: Built-in authentication, authorization, and security headers
- **Monitoring & Logging**: Structured logging and CloudWatch integration
- **CI/CD Pipelines**: GitHub Actions workflows for automated testing and deployment

## Getting Started

To work with templates:

```bash
cd templates

# Validate Java Micronaut template
./scripts/validate-template.sh java-micronaut

# Test template generation
./scripts/test-template-generation.sh java-micronaut test-muppet

# Run template development tools
cd template-tools && ./run-validation.sh
```

## Template Standards

All templates must follow the platform's standardized structure and include:

- Comprehensive test coverage (minimum 70%)
- Security best practices implementation
- Structured logging with JSON format
- Performance optimization guidelines
- OpenTofu infrastructure modules integration
- GitHub Actions CI/CD workflows
- Kiro IDE configuration for development

[Documentation will be expanded as additional templates are added in the future]