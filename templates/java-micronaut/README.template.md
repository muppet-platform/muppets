# {{muppet_name}}

A Java Micronaut microservice built with the Muppet Platform template.

## 🚀 Quick Start

```bash
# Setup development environment
make setup

# Build and run with Docker (recommended)
make run

# Or run in development mode with hot reload
make run-dev
```

The service will be available at:
- **Application**: http://localhost:3000
- **Health Check**: http://localhost:3000/health
- **Metrics**: http://localhost:3000/metrics

## 📋 Requirements

- **Java 21 LTS** (Amazon Corretto 21)
- **Docker** (Rancher Desktop recommended)
- **Make** (for build automation)

### Java 21 LTS Installation

```bash
# macOS
brew install --cask corretto21

# Verify installation
java -version
# Should show: openjdk version "21.x.x" ... LTS
```

## 🛠️ Development Commands

| Command | Description |
|---------|-------------|
| `make setup` | Set up development environment |
| `make build` | Build JAR and Docker image |
| `make run` | Start with Docker (production-like) |
| `make run-dev` | Start with Gradle (hot reload) |
| `make run-aws` | Start with LocalStack (AWS services) |
| `make test` | Run all tests |
| `make format` | Format code with Spotless |
| `make clean` | Clean build artifacts |

## 🏗️ Architecture

### Technology Stack
- **Language**: Java 21 LTS (Amazon Corretto)
- **Framework**: Micronaut 4.4.4
- **Build Tool**: Gradle 8.10.2
- **Container**: Docker with Alpine Linux
- **Testing**: JUnit 5, Mockito

### Project Structure
```
{{muppet_name}}/
├── src/main/java/           # Application source code
├── src/main/resources/      # Configuration files
├── src/test/java/           # Test source code
├── scripts/                 # Build and utility scripts
├── terraform/               # Infrastructure as code
├── build.gradle             # Gradle build configuration
├── Dockerfile               # Container configuration
└── Makefile                 # Development commands
```

## 🔧 Configuration

### Environment Variables
Configure the application using `.env.local`:

```bash
# Application settings
MICRONAUT_ENVIRONMENTS=development
SERVER_PORT=3000
LOG_LEVEL=DEBUG

# AWS settings (for production)
AWS_REGION={{aws_region}}
ENVIRONMENT={{environment}}

# LocalStack (for local AWS development)
# Uncomment these when using 'make run-aws'
# AWS_ENDPOINT_OVERRIDE=http://localhost:4566
# AWS_ACCESS_KEY_ID=test
# AWS_SECRET_ACCESS_KEY=test
```

### Application Profiles
- **development**: Local development with debug logging
- **production**: Production deployment with optimized settings

### LocalStack Integration
When you need to test AWS services locally:

```bash
# Start with LocalStack (includes S3, DynamoDB, SQS, etc.)
make run-aws

# LocalStack services available at:
# - S3: http://localhost:4566
# - DynamoDB: http://localhost:4566
# - SQS: http://localhost:4566
# - Health: http://localhost:4566/_localstack/health
```

**Smart LocalStack Detection:**
- If LocalStack is already running on port 4566 (e.g., from the Muppet Platform), it will reuse the existing instance
- If no LocalStack is running, it will start a new instance automatically
- This prevents port conflicts and allows sharing LocalStack across multiple muppets

**When to use LocalStack:**
- Testing S3 file operations
- DynamoDB database interactions
- SQS/SNS message handling
- Parameter Store configuration
- CloudWatch metrics (when re-enabled)
- Cost-free AWS development

## 🧪 Testing

```bash
# Run all tests
make test

# Run tests with coverage
./gradlew test jacocoTestReport

# View coverage report
open build/reports/jacoco/test/html/index.html
```

## 📦 Building and Deployment

### Local Development
```bash
# Hot reload development
make run-dev

# Production-like with Docker
make run

# With AWS services (LocalStack)
make run-aws
```

### Docker Build
```bash
# Build Docker image
make build

# Run standalone (no AWS services)
docker-compose up {{muppet_name}}-standalone

# Run with LocalStack (AWS services)
docker-compose --profile full-stack up
```

### AWS Deployment

#### Infrastructure Management
Infrastructure is managed with OpenTofu (Terraform):

```bash
cd terraform
tofu init
tofu plan
tofu apply
```

#### GitHub CI/CD Setup

**Required GitHub Secrets:**
Configure these secrets in your GitHub repository (Settings → Secrets and variables → Actions):

1. **AWS_ACCESS_KEY_ID** - AWS access key with deployment permissions
2. **AWS_SECRET_ACCESS_KEY** - AWS secret access key

**Required AWS Permissions:**
- ECR: Create repositories, push/pull images
- ECS: Create/update clusters, services, task definitions
- IAM: Create/manage service roles
- EC2: Manage security groups, load balancers, VPC resources
- CloudWatch: Create/manage log groups
- Application Auto Scaling: Manage scaling policies

**Deployment Process:**
The CD workflow automatically:
1. ✅ Builds JAR file with Gradle
2. ✅ Creates ECR repository if needed
3. ✅ Builds and pushes ARM64 Docker image
4. ✅ Deploys infrastructure with OpenTofu
5. ✅ Updates ECS service with new image
6. ✅ Waits for deployment to stabilize

**Triggering Deployments:**
- **Automatic**: Push to main branch
- **Manual**: Actions → CD → Run workflow
- **Environment**: Select development/staging/production

**Monitoring Deployment:**
- **Application URL**: Available in workflow output
- **Health Check**: Accessible at `/health` endpoint
- **Logs**: Available in CloudWatch
- **Metrics**: ECS service metrics in AWS console

## 🔍 Monitoring and Health

### Health Endpoints
- **Health**: `GET /health` - Application health status
- **Readiness**: `GET /health/ready` - Readiness probe
- **Liveness**: `GET /health/live` - Liveness probe

### Metrics
- **Metrics**: `GET /metrics` - Application metrics
- **JVM Metrics**: Memory, GC, threads (in production)

### Logging
- **Format**: Structured JSON logging
- **Levels**: Configurable via `LOG_LEVEL` environment variable
- **Output**: Console (Docker logs in production)

## 🚀 API Endpoints

### Core Endpoints
```bash
# Application info
curl http://localhost:3000/api

# Health check
curl http://localhost:3000/health

# Application metrics
curl http://localhost:3000/metrics
```

### Example Response
```json
{
  "service": "{{muppet_name}}",
  "message": "Welcome to {{muppet_name}} API",
  "version": "1.0.0"
}
```

## 🔧 Troubleshooting

### Common Issues

**Java Version Issues**
```bash
# Check Java version
java -version

# Should show Java 21 LTS
# If not, install Amazon Corretto 21
brew install --cask corretto21
```

**Docker Issues**
```bash
# Check Docker is running
docker info

# If not running, start Rancher Desktop
# Preferences → Container Engine → dockerd (moby)
```

**Build Issues**
```bash
# Clean and rebuild
make clean
make build

# Check Gradle wrapper
./gradlew --version
```

**Deployment Issues**
```bash
# Check GitHub Actions logs for detailed errors
# Common issues:
# - Permission Denied: Verify AWS credentials and permissions
# - ECR Push Failed: Check ECR permissions and repository access
# - ECS Deployment Failed: Validate task definition and service config
# - Health Check Failed: Verify application starts and /health responds

# Debug steps:
# 1. Check CloudWatch logs for application startup issues
# 2. Validate security group and networking configuration
# 3. Verify AWS credentials have required permissions
# 4. Test local Docker build: make build && docker run <image>
```

### Performance Tuning

**JVM Settings** (already optimized in Dockerfile):
```bash
-XX:+UseContainerSupport
-XX:MaxRAMPercentage=75.0
-XX:+UseG1GC
-XX:+UseStringDeduplication
```

**Container Resources**:
- **CPU**: 1 vCPU minimum for Java applications
- **Memory**: 2GB minimum for JVM overhead
- **Startup**: ~30-60 seconds for full initialization

## 📚 Resources

- [Micronaut Documentation](https://docs.micronaut.io/)
- [Amazon Corretto 21 Guide](https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/)
- [Muppet Platform Documentation](../docs/)
- [OpenTofu Documentation](https://opentofu.org/docs/)

## 🤝 Contributing

1. Follow Java 21 LTS requirements
2. Run `make format` before committing
3. Ensure all tests pass with `make test`
4. Update documentation for new features

### Security Best Practices

- Use IAM roles with minimal required permissions
- Rotate AWS credentials regularly
- Enable CloudTrail for audit logging
- Use environment-specific secrets for staging/production
- Review and approve production deployments

## 📄 License

This project is part of the Muppet Platform ecosystem.