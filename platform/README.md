# Muppet Platform - Core Platform Service

The core platform service that manages muppet lifecycle, coordinates with external services, and provides MCP tools for developer interaction.

## 🏗️ Architecture

- **FastAPI Application**: Modern async web framework with automatic API documentation
- **MCP Server**: Model Context Protocol server for Kiro integration
- **State Management**: Distributed state reconstruction from GitHub, Parameter Store, and ECS
- **AWS Integration**: Native integration with Fargate, ECR, CloudWatch, and other AWS services
- **GitHub Integration**: Automated repository creation and management

## 📁 Project Structure

```
platform/
├── src/                    # Platform source code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Pydantic settings and configuration
│   ├── models.py          # Data models and schemas
│   ├── state_manager.py   # Distributed state management
│   ├── integrations/      # External service integrations
│   ├── platform_mcp/      # MCP server implementation
│   └── routers/           # FastAPI route handlers
├── tests/                 # Unit and integration tests
├── scripts/               # Development and deployment scripts
├── docker/                # Container configuration
├── terraform/             # Infrastructure as code
└── .github/workflows/     # CI/CD pipelines
```

## 🚀 Quick Start

### Prerequisites

- **Rancher Desktop** (for Docker and Kubernetes)
- **Python 3.10+** with UV package manager
- **Git** for version control

### Automated Setup

Run the automated setup script to install all dependencies and configure your local environment:

```bash
# Make the script executable and run it
chmod +x scripts/setup-local-dev.sh
./scripts/setup-local-dev.sh
```

This script will:
- ✅ Install Rancher Desktop (if not present)
- ✅ Install UV Python package manager
- ✅ Set up Python virtual environment and dependencies
- ✅ Create Docker Compose configuration for local development
- ✅ Set up LocalStack for AWS service simulation
- ✅ Create development scripts for common tasks

### Manual Setup (Alternative)

If you prefer manual setup or the automated script fails:

#### 1. Install Rancher Desktop

**macOS (with Homebrew):**
```bash
brew install --cask rancher
```

**Linux (Ubuntu/Debian):**
```bash
curl -s https://download.opensuse.org/repositories/isv:/Rancher:/stable/deb/Release.key | gpg --dearmor | sudo dd status=none of=/usr/share/keyrings/isv-rancher-stable-archive-keyring.gpg
echo 'deb [signed-by=/usr/share/keyrings/isv-rancher-stable-archive-keyring.gpg] https://download.opensuse.org/repositories/isv:/Rancher:/stable/deb/ ./' | sudo dd status=none of=/etc/apt/sources.list.d/isv-rancher-stable.list
sudo apt update && sudo apt install -y rancher-desktop
```

**Other platforms:** Download from [rancherdesktop.io](https://rancherdesktop.io/)

#### 2. Install UV (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

#### 3. Set Up Python Environment

```bash
# Install dependencies
uv sync --dev

# Verify installation
uv run python -c "import fastapi; print('FastAPI installed successfully')"
```

## 🔧 Development Workflow

### Environment Configuration

1. **Copy environment template:**
   ```bash
   cp .env.local .env
   ```

2. **Set your GitHub token:**
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   # Or add it to your .env file
   echo "GITHUB_TOKEN=your_github_token_here" >> .env
   ```

### Common Development Tasks

#### Build the Platform
```bash
./scripts/build.sh
```

#### Start Local Development Environment
```bash
./scripts/run.sh
```

This starts:
- 🚀 **Platform API** at http://localhost:8000
- 🔧 **LocalStack** (AWS simulation) at http://localhost:4566
- 📊 **API Documentation** at http://localhost:8000/docs

#### Run Tests
```bash
./scripts/test.sh

# With coverage report
uv run python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
uv run python -m pytest tests/test_main.py -v
```

#### Stop Development Environment
```bash
./scripts/stop.sh
```

#### View Logs
```bash
docker-compose -f docker-compose.local.yml logs -f

# View specific service logs
docker-compose -f docker-compose.local.yml logs -f platform
docker-compose -f docker-compose.local.yml logs -f localstack
```

### Direct Python Development (Without Docker)

For faster development cycles, you can run the platform directly:

```bash
# Install dependencies
uv sync --dev

# Run the platform with hot reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run python -m pytest tests/ -v

# Code formatting and linting
uv run black src/ tests/
uv run isort src/ tests/
uv run flake8 src/ tests/
uv run mypy src/
```

## 🧪 Testing

The platform uses a comprehensive testing strategy:

### Unit Tests
- **FastAPI endpoints** - API functionality and error handling
- **MCP server** - Authentication, tool registry, and tool execution
- **State management** - Caching, reconstruction, and consistency
- **Integration clients** - AWS and GitHub service interactions

### Test Categories
```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test categories
uv run python -m pytest tests/test_main.py -v          # FastAPI tests
uv run python -m pytest tests/test_mcp_server.py -v   # MCP server tests
uv run python -m pytest tests/test_state_manager.py -v # State management tests

# Run with coverage
uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### Test Environment
- **LocalStack** simulates AWS services (S3, Parameter Store, ECS, CloudWatch)
- **Moto** provides AWS service mocking for unit tests
- **pytest-asyncio** handles async test execution
- **Test isolation** ensures tests don't interfere with each other

## 🔌 API Endpoints

### Health Checks
- `GET /health/` - Basic health check
- `GET /health/ready` - Readiness check with dependency status

### Muppet Management
- `GET /api/v1/muppets/` - List all muppets
- `GET /api/v1/muppets/{name}` - Get muppet details
- `POST /api/v1/muppets/` - Create new muppet
- `DELETE /api/v1/muppets/{name}` - Delete muppet

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🛠️ MCP Tools

The platform exposes MCP tools for Kiro integration:

- `create_muppet` - Create new muppet from template
- `delete_muppet` - Remove muppet and cleanup resources
- `list_muppets` - Show all active muppets
- `list_templates` - Show available templates
- `get_muppet_status` - Get detailed muppet information
- `get_muppet_logs` - Retrieve muppet logs
- `setup_muppet_dev` - Configure local development environment
- `update_shared_steering` - Update shared steering docs
- `list_steering_docs` - Show available steering documentation

## 🐛 Troubleshooting

### Common Issues

#### Docker/Rancher Desktop Issues
```bash
# Check if Docker is running
docker info

# Check Docker context
docker context show

# Switch to Rancher Desktop context (if needed)
docker context use rancher-desktop
```

#### LocalStack Issues
```bash
# Check LocalStack health
curl http://localhost:4566/_localstack/health

# View LocalStack logs
docker-compose -f docker-compose.local.yml logs localstack

# Restart LocalStack
docker-compose -f docker-compose.local.yml restart localstack
```

#### Python Environment Issues
```bash
# Recreate virtual environment
uv sync --dev

# Check Python version
uv run python --version

# Verify dependencies
uv run python -c "import fastapi, pydantic, boto3; print('All dependencies OK')"
```

#### Port Conflicts
If ports 8000 or 4566 are in use:
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :4566

# Kill processes using the ports
sudo kill -9 $(lsof -t -i:8000)
sudo kill -9 $(lsof -t -i:4566)
```

### Getting Help

1. **Check logs** for detailed error messages
2. **Verify prerequisites** are installed and running
3. **Check environment variables** in `.env` file
4. **Restart services** if issues persist
5. **Clean up and rebuild** if problems continue:
   ```bash
   ./scripts/stop.sh
   docker system prune -f
   ./scripts/build.sh
   ./scripts/run.sh
   ```

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **UV Documentation**: https://docs.astral.sh/uv/
- **Rancher Desktop**: https://rancherdesktop.io/
- **LocalStack**: https://docs.localstack.cloud/

## 🤝 Contributing

1. **Follow the development workflow** outlined above
2. **Write tests** for new functionality
3. **Run the full test suite** before submitting changes
4. **Use the provided scripts** for consistent development experience
5. **Update documentation** when adding new features