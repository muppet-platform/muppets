# Muppet Platform Product Overview

The Muppet Platform is an internal developer platform that enables rapid creation and management of backend applications ("muppets") through a standardized Java Micronaut template.

## Core Purpose

- **Standardized Template**: Pre-configured Java Micronaut application template with Amazon Corretto 21 LTS
- **AWS Fargate Deployment**: Serverless container management with automatic scaling
- **Centralized Infrastructure**: Shared OpenTofu modules for consistent infrastructure patterns
- **GitHub Integration**: Automatic repository creation, CI/CD setup, and branch protection
- **Kiro Integration**: MCP tools for seamless developer experience

## Key Components

- **Platform Service**: Core orchestration service managing muppet lifecycle
- **Java Micronaut Template**: Production-ready application template with best practices
- **OpenTofu Modules**: Shared infrastructure components (ECR, Fargate, networking, monitoring)
- **Steering Docs**: Centralized development guidelines and best practices

## Target Users

Internal development teams who need to quickly spin up new Java-based backend services with consistent infrastructure, monitoring, and deployment patterns.

## Architecture Philosophy

Modular design with clear separation of concerns, enabling parallel development across teams while maintaining consistency across all generated Java Micronaut applications. The platform focuses on providing a single, well-tested, production-ready template rather than multiple template options.