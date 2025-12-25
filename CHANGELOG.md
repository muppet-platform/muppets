# Changelog

All notable changes to the Muppet Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Comprehensive CI/CD Pipeline**: Complete GitHub Actions workflows for continuous integration and deployment
  - CI Pipeline: Automated testing, code quality checks, and security scanning
  - CD Pipeline: Automated deployment to staging and production environments
  - Security Pipeline: Daily vulnerability scans and security analysis
  - Release Pipeline: Automated release management with artifact generation
  - Maintenance Pipeline: Weekly dependency updates and cleanup automation
- **Multi-Platform Docker Support**: Container builds for linux/amd64 and linux/arm64
- **Environment Protection**: Staging and production deployment with approval workflows
- **Artifact Management**: Automated cleanup and retention policies
- **Security Integration**: GitHub Security tab integration with SARIF reports
- **Local CI/CD Testing**: Script to simulate CI/CD pipeline locally (`scripts/test-ci-cd.sh`)
- **Workflow Validation**: Automated validation of GitHub Actions workflows
- **CI/CD Documentation**: Comprehensive documentation for pipeline configuration and troubleshooting
- Monorepo project structure with component-based organization
- Comprehensive testing framework with component-specific test scripts
- Project-level automation scripts (setup, build, test)
- GitHub templates for issues and pull requests
- Contributing guidelines and development workflow documentation
- MCP server integration for Kiro IDE support

### Enhanced
- **README**: Added CI/CD status badges and pipeline information
- **Documentation**: Added detailed CI/CD pipeline documentation (`docs/ci-cd.md`)
- **Security**: Integrated multiple security scanning tools (Bandit, Safety, Trivy, tfsec, Checkov)
- **Monitoring**: Added workflow status monitoring and notification systems

### Infrastructure
- **GitHub Container Registry**: Automated Docker image publishing
- **OpenTofu Integration**: Infrastructure deployment automation
- **AWS Deployment**: Automated ECS Fargate deployment with smoke tests
- **Multi-Environment Support**: Separate staging and production environments

### Changed
- Reorganized project as modular monorepo
- Simplified state management to startup initialization (removed lazy loading)
- Enhanced template verification system with comprehensive validation
- Updated Java Micronaut template to use Amazon Corretto 21 LTS exclusively

### Fixed
- Gradle wrapper corruption issues in Java Micronaut template
- Template script permissions and execution
- MCP configuration for generated muppets
- JaCoCo test coverage reporting in templates

### Security
- Added .gitattributes to prevent binary file corruption
- Implemented proper secret management guidelines
- Enhanced security scanning in CI/CD pipelines

## [0.1.0] - 2024-12-25

### Added
- Initial Muppet Platform implementation
- Core platform service with FastAPI
- Java Micronaut template with Amazon Corretto 21 LTS
- OpenTofu infrastructure modules
- GitHub integration for repository management
- AWS integration for Fargate deployment
- MCP server for Kiro IDE integration
- Comprehensive test suite with 245+ tests
- Template verification system
- Steering documentation system
- Docker containerization support

### Platform Service Features
- Muppet lifecycle management (create, deploy, monitor, delete)
- Template processing and code generation
- GitHub repository creation and management
- AWS infrastructure orchestration
- State management with GitHub discovery
- Health and readiness endpoints
- Structured logging with JSON format

### Java Micronaut Template Features
- Amazon Corretto 21 LTS support
- Gradle 8.5+ build system with wrapper
- Micronaut 4.0.4 framework
- Docker containerization
- AWS CloudWatch integration
- Comprehensive development scripts
- JaCoCo code coverage reporting
- Kiro MCP configuration

### Infrastructure Modules
- ECS Fargate service module
- CloudWatch monitoring module
- VPC networking module
- ECR container registry module
- OpenTofu 1.6+ compatibility

### Development Tools
- UV-based Python dependency management
- Property-based testing with Hypothesis
- Automated code formatting and linting
- Docker development environment
- Local development scripts

---

## Release Notes Format

Each release includes:
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

## Component Versioning

- **Platform Service**: Independent versioning based on API changes
- **Templates**: Version tracking in template.yaml files
- **Infrastructure**: Module versioning with Git tags
- **Documentation**: Version alignment with platform releases