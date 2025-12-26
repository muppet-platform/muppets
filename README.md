# Muppet Platform

[![CI Pipeline](https://github.com/muppet-platform/muppets/actions/workflows/ci.yml/badge.svg)](https://github.com/muppet-platform/muppets/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/muppet-platform/muppets/actions/workflows/cd.yml/badge.svg)](https://github.com/muppet-platform/muppets/actions/workflows/cd.yml)
[![Security Scan](https://github.com/muppet-platform/muppets/actions/workflows/security.yml/badge.svg)](https://github.com/muppet-platform/muppets/actions/workflows/security.yml)

> Internal developer platform for creating and managing backend applications

The Muppet Platform enables rapid creation and management of standardized backend applications ("muppets") through automated template generation, infrastructure provisioning, and lifecycle management.

## 🚀 Quick Start

### Prerequisites

- **Java 21 LTS**: Amazon Corretto 21 (required)
- **Python 3.10+**: For platform service
- **UV**: Python package manager
- **OpenTofu 1.6+**: For infrastructure
- **Docker**: For containerization (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/muppet-platform/muppets.git
cd muppets

# Run setup script
./scripts/setup.sh

# Verify installation
./scripts/test-all.sh
```

### Start the Platform

```bash
# Start platform service
make platform-dev

# Or using scripts
cd platform && uv run uvicorn src.main:app --reload
```

The platform will be available at `http://localhost:8000`

## 🏗️ Architecture

The Muppet Platform is organized as a modular monorepo:

```
muppet-platform/
├── platform/           # Core FastAPI service
├── templates/          # Muppet templates (Java Micronaut)
├── terraform-modules/  # Shared infrastructure modules
├── steering-docs/      # Development guidelines
├── scripts/           # Project automation
└── .github/           # CI/CD workflows
```

### Core Components

- **Platform Service**: FastAPI-based orchestration service
- **Templates**: Standardized application templates with parameter injection
- **Infrastructure**: OpenTofu modules for AWS deployment
- **Steering**: Centralized development guidelines and best practices

## 🎯 Features

### Platform Service
- 🎭 **Muppet Lifecycle Management**: Create, deploy, monitor, and delete muppets
- 🔧 **Template Processing**: Code generation with parameter injection
- 🐙 **GitHub Integration**: Automatic repository creation and management
- ☁️ **AWS Integration**: ECS Fargate deployment and monitoring
- 🔌 **Kiro MCP Integration**: Seamless IDE integration
- 📊 **Health Monitoring**: Comprehensive health and readiness checks

### Java Micronaut Template
- ☕ **Amazon Corretto 21 LTS**: Latest LTS Java with modern features
- 🏗️ **Gradle 8.5+**: Modern build system with wrapper
- 🚀 **Micronaut 4.0.4**: High-performance microservices framework
- 🐳 **Docker Ready**: Multi-stage builds with Alpine Linux
- 📈 **Observability**: CloudWatch metrics and structured logging
- 🧪 **Testing**: JUnit 5, Mockito, and JaCoCo coverage
- 🔧 **Development Tools**: Comprehensive scripts and Kiro integration

### Infrastructure Modules
- 🚢 **ECS Fargate**: Serverless container deployment
- 📊 **CloudWatch**: Monitoring, logging, and alerting
- 🌐 **VPC Networking**: Secure network configuration
- 📦 **ECR**: Container registry with lifecycle policies

## 🛠️ Development

### Component Testing

```bash
# Test individual components
./scripts/test-platform.sh      # Platform service
./scripts/test-templates.sh     # Templates
./scripts/test-infrastructure.sh # Infrastructure

# Test everything
./scripts/test-all.sh
```

### Component Development

```bash
# Platform service
cd platform
uv run pytest                   # Run tests
uv run uvicorn src.main:app --reload  # Dev server

# Template development
cd templates/java-micronaut
./scripts/init.sh              # Initialize
./scripts/build.sh             # Build
./scripts/test.sh              # Test

# Infrastructure
cd terraform-modules/module-name
tofu init && tofu validate     # Validate
```

## 📚 Documentation

- **[Architecture](docs/README.md)** - System architecture and design
- **[AWS Setup](docs/aws-test-setup.md)** - AWS integration and testing setup
- **[AWS Deployment Ready](docs/aws-deployment-ready.md)** - AWS deployment readiness status
- **[API Documentation](docs/api/)** - REST API reference
- **[Templates](templates/README.md)** - Template development guide
- **[Infrastructure](terraform-modules/README.md)** - Infrastructure modules
- **[Contributing](CONTRIBUTING.md)** - Development guidelines
- **[Deployment](docs/deployment/)** - Deployment procedures

## 🔧 Usage

### Creating a Muppet

```bash
# Using the API
curl -X POST http://localhost:8000/api/v1/muppets/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "user-service",
    "template": "java-micronaut",
    "description": "User management service"
  }'

# Using Kiro MCP tools
# In Kiro: "Create a new muppet called user-service"
```

### Available Templates

- **java-micronaut**: Java 21 + Micronaut 4.0.4 + Gradle 8.5
- More templates coming soon...

### Infrastructure Deployment

```bash
# Deploy muppet infrastructure
curl -X POST http://localhost:8000/api/v1/muppets/user-service/deploy

# Check deployment status
curl http://localhost:8000/api/v1/muppets/user-service/status
```

## 🔌 Kiro Integration

The platform includes MCP (Model Context Protocol) integration for seamless Kiro IDE support:

```json
{
  "mcpServers": {
    "muppet-platform": {
      "command": "uv",
      "args": ["run", "mcp-server"],
      "cwd": "./platform"
    }
  }
}
```

Available MCP tools:
- `list_muppets` - List all muppets
- `create_muppet` - Create new muppets
- `get_muppet_status` - Get muppet status
- `list_templates` - Show available templates

## 🚀 Deployment

### Local Development

```bash
# Start all services
docker-compose -f platform/docker-compose.local.yml up

# Or start platform only
cd platform && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Production Deployment

1. **Build Docker images**:
   ```bash
   cd platform && docker build -t muppet-platform:latest .
   ```

2. **Deploy to ECS**:
   ```bash
   # Use provided OpenTofu modules
   cd terraform-modules/fargate-service
   tofu init && tofu apply
   ```

3. **Configure environment**:
   - Set `INTEGRATION_MODE=real`
   - Configure GitHub and AWS credentials
   - Set up monitoring and logging

## 🧪 Testing

The platform includes comprehensive testing:

- **Unit Tests**: 245+ tests with 80%+ coverage
- **Integration Tests**: Cross-component testing
- **Property-Based Tests**: Hypothesis-driven testing
- **Template Verification**: Automated template validation
- **Infrastructure Tests**: OpenTofu validation

```bash
# Run all tests
./scripts/test-all.sh

# Component-specific tests
./scripts/test-platform.sh
./scripts/test-templates.sh
./scripts/test-infrastructure.sh
```

## 📊 Monitoring

### Health Endpoints

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /api/v1/muppets/` - List all muppets
- `GET /api/v1/templates/` - List available templates

### Metrics

- Platform service metrics via CloudWatch
- Muppet application metrics via Micrometer
- Infrastructure metrics via AWS CloudWatch

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `./scripts/test-all.sh`
5. Submit a pull request

### Code Standards

- **Java**: Amazon Corretto 21 LTS only
- **Python**: Type hints, docstrings, 80%+ coverage
- **Infrastructure**: OpenTofu with proper documentation
- **Testing**: Comprehensive test coverage required

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/muppet-platform/muppets/issues)
- **Discussions**: [GitHub Discussions](https://github.com/muppet-platform/muppets/discussions)

## 🗺️ Roadmap

- [ ] Additional template types (Python FastAPI, Node.js)
- [ ] Enhanced monitoring and alerting
- [ ] Multi-region deployment support
- [ ] Advanced security features
- [ ] Performance optimizations

---

**Built with ❤️ by the Platform Team**