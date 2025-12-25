# Muppet Platform - Project Structure

## Overview

The Muppet Platform is organized as a monorepo with clear module boundaries. Each component has its own build system, testing, and deployment pipeline while sharing common tooling and documentation.

## Directory Structure

```
muppet-platform/
├── .github/
│   ├── workflows/
│   │   ├── platform-ci.yml          # Platform service CI/CD
│   │   ├── templates-ci.yml          # Template validation
│   │   ├── infrastructure-ci.yml     # Infrastructure testing
│   │   └── docs-ci.yml              # Documentation builds
│   ├── ISSUE_TEMPLATE/
│   └── dependabot.yml
├── .kiro/
│   ├── settings/
│   │   └── mcp.json                 # Project MCP configuration
│   ├── steering/                    # Project-level steering
│   └── specs/                       # Project specifications
├── docs/
│   ├── README.md                    # Project overview
│   ├── architecture/                # Architecture documentation
│   ├── api/                         # API documentation
│   └── deployment/                  # Deployment guides
├── platform/                       # Core Platform Service
│   ├── src/                         # Python source code
│   ├── tests/                       # Unit and integration tests
│   ├── docker/                      # Docker configuration
│   ├── terraform/                   # Platform infrastructure
│   ├── docs/                        # Platform-specific docs
│   ├── pyproject.toml              # Python dependencies
│   ├── Makefile                    # Platform build tasks
│   └── README.md                   # Platform documentation
├── templates/                       # Muppet Templates
│   ├── java-micronaut/             # Java Micronaut template
│   │   ├── src/                    # Template source code
│   │   ├── scripts/                # Template scripts
│   │   ├── .kiro/                  # Template Kiro config
│   │   ├── terraform/              # Template infrastructure
│   │   └── template.yaml           # Template metadata
│   ├── template-tools/             # Template development tools
│   └── README.md                   # Templates documentation
├── terraform-modules/              # Shared Infrastructure Modules
│   ├── fargate-service/            # ECS Fargate module
│   ├── monitoring/                 # CloudWatch monitoring
│   ├── networking/                 # VPC and networking
│   ├── ecr/                        # Container registry
│   └── README.md                   # Infrastructure documentation
├── steering-docs/                  # Centralized Steering Documentation
│   ├── shared/                     # Shared steering files
│   ├── templates/                  # Steering templates
│   └── README.md                   # Steering documentation
├── scripts/                        # Project-level Scripts
│   ├── setup.sh                    # Project setup
│   ├── test-all.sh                 # Run all tests
│   ├── build-all.sh                # Build all components
│   └── deploy.sh                   # Deployment script
├── .gitignore                      # Git ignore rules
├── .gitattributes                  # Git attributes
├── README.md                       # Project README
├── CONTRIBUTING.md                 # Contribution guidelines
├── LICENSE                         # Project license
├── CHANGELOG.md                    # Change log
└── Makefile                        # Top-level build tasks
```

## Component Responsibilities

### Platform Service (`platform/`)
- **Purpose**: Core orchestration service for muppet lifecycle management
- **Technology**: Python 3.10+, FastAPI, Pydantic
- **Responsibilities**:
  - Muppet creation, deployment, and management
  - Template processing and code generation
  - GitHub integration and repository management
  - AWS infrastructure orchestration
  - MCP server for Kiro integration
- **Build System**: UV for dependency management, pytest for testing
- **Deployment**: Docker containers on ECS Fargate

### Templates (`templates/`)
- **Purpose**: Standardized application templates for muppet generation
- **Current Templates**: Java Micronaut with Amazon Corretto 21
- **Responsibilities**:
  - Application code templates with parameter injection
  - Build system configuration (Gradle, Docker)
  - Infrastructure as code templates
  - Development tooling and scripts
- **Validation**: Template verification system with comprehensive testing
- **Extensibility**: Plugin architecture for new template types

### Infrastructure Modules (`terraform-modules/`)
- **Purpose**: Reusable OpenTofu/Terraform modules for AWS infrastructure
- **Technology**: OpenTofu (Terraform-compatible)
- **Modules**:
  - `fargate-service`: ECS Fargate service with auto-scaling
  - `monitoring`: CloudWatch metrics, alarms, and dashboards
  - `networking`: VPC, subnets, security groups
  - `ecr`: Container registry with lifecycle policies
- **Testing**: Terratest for infrastructure validation
- **Versioning**: Semantic versioning with Git tags

### Steering Documentation (`steering-docs/`)
- **Purpose**: Centralized development guidelines and best practices
- **Content**:
  - Coding standards and conventions
  - Architecture decision records (ADRs)
  - Development workflows and processes
  - Security and compliance guidelines
- **Distribution**: Shared across all generated muppets
- **Maintenance**: Version-controlled with change tracking

## Build and Development Workflow

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/your-org/muppet-platform.git
cd muppet-platform

# Run setup script
./scripts/setup.sh

# Start platform service
make platform-dev

# Run all tests
make test-all
```

### Component-Specific Development
```bash
# Platform service development
cd platform
make setup
make test
make run

# Template development
cd templates/java-micronaut
./scripts/init.sh
./scripts/build.sh
./scripts/test.sh

# Infrastructure development
cd terraform-modules/fargate-service
tofu init
tofu plan
tofu apply
```

### Testing Strategy
- **Unit Tests**: Component-level testing with mocking
- **Integration Tests**: Cross-component testing with test environments
- **End-to-End Tests**: Full muppet lifecycle testing
- **Infrastructure Tests**: Terratest for infrastructure validation
- **Template Tests**: Verification system for template generation

### CI/CD Pipeline
- **Platform CI**: Python testing, Docker builds, security scanning
- **Template CI**: Template validation, verification tests
- **Infrastructure CI**: OpenTofu validation, security compliance
- **Documentation CI**: Documentation builds and link checking

## Versioning Strategy

### Semantic Versioning
- **Major**: Breaking changes to APIs or templates
- **Minor**: New features, new templates, infrastructure updates
- **Patch**: Bug fixes, documentation updates

### Component Versioning
- **Platform**: Independent versioning based on API changes
- **Templates**: Version tracking in template.yaml files
- **Infrastructure**: Module versioning with Git tags
- **Documentation**: Version alignment with platform releases

### Release Process
1. **Development**: Feature branches with PR reviews
2. **Testing**: Automated testing in CI/CD pipeline
3. **Staging**: Deployment to staging environment
4. **Release**: Tagged releases with changelog updates
5. **Production**: Automated deployment with rollback capability

## Security and Compliance

### Code Security
- **Dependency Scanning**: Automated vulnerability detection
- **Secret Management**: No secrets in code, use environment variables
- **Access Control**: Role-based access with least privilege
- **Audit Logging**: Comprehensive logging for all operations

### Infrastructure Security
- **Network Security**: VPC isolation, security groups
- **Encryption**: At-rest and in-transit encryption
- **IAM**: Minimal required permissions
- **Compliance**: SOC 2, GDPR compliance where applicable

## Documentation Standards

### Code Documentation
- **Python**: Docstrings with type hints
- **OpenTofu**: Module documentation with examples
- **Templates**: Comprehensive README files
- **APIs**: OpenAPI/Swagger documentation

### Architecture Documentation
- **ADRs**: Architecture Decision Records for major decisions
- **Diagrams**: System architecture and data flow diagrams
- **Runbooks**: Operational procedures and troubleshooting
- **API Docs**: Generated from code with examples

## Contribution Guidelines

### Development Process
1. **Issue Creation**: Use GitHub issues for feature requests and bugs
2. **Branch Strategy**: Feature branches from main with descriptive names
3. **Pull Requests**: Required for all changes with review process
4. **Testing**: All changes must include appropriate tests
5. **Documentation**: Update documentation for user-facing changes

### Code Quality
- **Linting**: Automated code formatting and style checking
- **Testing**: Minimum 80% code coverage requirement
- **Security**: Security scanning and vulnerability assessment
- **Performance**: Performance testing for critical paths

This modular organization provides clear boundaries while maintaining the benefits of a monorepo approach for the Muppet Platform.