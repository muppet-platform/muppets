#!/bin/bash

# Muppet Platform Local Development Setup Script
# This script sets up the local development environment for the Muppet Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Rancher Desktop is running
check_rancher_desktop() {
    if command_exists docker && docker info >/dev/null 2>&1; then
        local context=$(docker context show 2>/dev/null || echo "")
        if [[ "$context" == "rancher-desktop" ]] || docker info 2>/dev/null | grep -q "rancher-desktop"; then
            return 0
        fi
    fi
    return 1
}

# Function to install Rancher Desktop on macOS
install_rancher_desktop_macos() {
    print_status "Installing Rancher Desktop on macOS..."
    
    if command_exists brew; then
        brew install --cask rancher
        print_success "Rancher Desktop installed via Homebrew"
    else
        print_warning "Homebrew not found. Please install Rancher Desktop manually:"
        print_warning "1. Download from: https://rancherdesktop.io/"
        print_warning "2. Install the .dmg file"
        print_warning "3. Run this script again"
        exit 1
    fi
}

# Function to install Rancher Desktop on Linux
install_rancher_desktop_linux() {
    print_status "Installing Rancher Desktop on Linux..."
    
    # Check for different package managers
    if command_exists apt-get; then
        # Ubuntu/Debian
        print_status "Detected Ubuntu/Debian system"
        curl -s https://download.opensuse.org/repositories/isv:/Rancher:/stable/deb/Release.key | gpg --dearmor | sudo dd status=none of=/usr/share/keyrings/isv-rancher-stable-archive-keyring.gpg
        echo 'deb [signed-by=/usr/share/keyrings/isv-rancher-stable-archive-keyring.gpg] https://download.opensuse.org/repositories/isv:/Rancher:/stable/deb/ ./' | sudo dd status=none of=/etc/apt/sources.list.d/isv-rancher-stable.list
        sudo apt update
        sudo apt install -y rancher-desktop
    elif command_exists yum; then
        # RHEL/CentOS/Fedora
        print_status "Detected RHEL/CentOS/Fedora system"
        sudo yum-config-manager --add-repo=https://download.opensuse.org/repositories/isv:/Rancher:/stable/rpm/isv:Rancher:stable.repo
        sudo yum install -y rancher-desktop
    elif command_exists pacman; then
        # Arch Linux
        print_status "Detected Arch Linux system"
        print_warning "Please install Rancher Desktop from AUR:"
        print_warning "yay -S rancher-desktop-bin"
        exit 1
    else
        print_warning "Package manager not detected. Please install Rancher Desktop manually:"
        print_warning "Visit: https://rancherdesktop.io/"
        exit 1
    fi
    
    print_success "Rancher Desktop installed"
}

# Function to install UV (Python package manager)
install_uv() {
    print_status "Installing UV (Python package manager)..."
    
    if command_exists uv; then
        print_success "UV is already installed"
        return 0
    fi
    
    # Install UV using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    if command_exists uv; then
        print_success "UV installed successfully"
    else
        print_error "Failed to install UV. Please install manually:"
        print_error "Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Navigate to platform directory
    cd "$(dirname "$0")/.."
    
    # Install dependencies using UV
    print_status "Installing Python dependencies..."
    uv sync --dev
    
    print_success "Python environment setup complete"
}

# Function to create Docker Compose configuration
create_docker_compose() {
    print_status "Creating Docker Compose configuration..."
    
    cat > docker-compose.local.yml << 'EOF'
version: '3.8'

services:
  # LocalStack for AWS service simulation
  localstack:
    image: localstack/localstack:3.0
    container_name: muppet-localstack
    ports:
      - "4566:4566"  # LocalStack main port
      - "4510-4559:4510-4559"  # External service ports
    environment:
      - SERVICES=s3,ssm,ecs,ecr,logs,iam
      - DEBUG=1
      - DATA_DIR=/tmp/localstack/data
      - DOCKER_HOST=unix:///var/run/docker.sock
      - HOST_TMP_FOLDER=/tmp/localstack
    volumes:
      - "/tmp/localstack:/tmp/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
      - "./scripts/localstack-init.sh:/etc/localstack/init/ready.d/init.sh"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4566/_localstack/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  # Muppet Platform Service
  platform:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: muppet-platform
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_DEFAULT_REGION=us-west-2
      - GITHUB_TOKEN=${GITHUB_TOKEN:-}
    depends_on:
      localstack:
        condition: service_healthy
    volumes:
      - "./src:/app/src"  # Mount source for hot reload
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

networks:
  default:
    name: muppet-platform-local
EOF

    print_success "Docker Compose configuration created"
}

# Function to create LocalStack initialization script
create_localstack_init() {
    print_status "Creating LocalStack initialization script..."
    
    mkdir -p scripts
    
    cat > scripts/localstack-init.sh << 'EOF'
#!/bin/bash

# LocalStack initialization script for Muppet Platform
# This script sets up the required AWS resources in LocalStack

echo "Initializing LocalStack for Muppet Platform..."

# Wait for LocalStack to be ready
awslocal --version || pip install awscli-local

# Create S3 buckets
echo "Creating S3 buckets..."
awslocal s3 mb s3://muppet-platform-artifacts
awslocal s3 mb s3://muppet-platform-terraform-state

# Create Parameter Store parameters
echo "Creating Parameter Store parameters..."
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/fargate-service/version" --value "1.0.0" --type "String"
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/monitoring/version" --value "1.0.0" --type "String"
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/networking/version" --value "1.0.0" --type "String"
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/ecr/version" --value "1.0.0" --type "String"

# Create ECR repository
echo "Creating ECR repository..."
awslocal ecr create-repository --repository-name muppet-platform/platform

# Create ECS cluster
echo "Creating ECS cluster..."
awslocal ecs create-cluster --cluster-name muppet-platform-local

# Create CloudWatch log groups
echo "Creating CloudWatch log groups..."
awslocal logs create-log-group --log-group-name /muppet-platform/platform
awslocal logs create-log-group --log-group-name /muppet-platform/muppets

echo "LocalStack initialization complete!"
EOF

    chmod +x scripts/localstack-init.sh
    print_success "LocalStack initialization script created"
}

# Function to create development scripts
create_dev_scripts() {
    print_status "Creating development scripts..."
    
    mkdir -p scripts
    
    # Build script
    cat > scripts/build.sh << 'EOF'
#!/bin/bash

# Build script for Muppet Platform

set -e

echo "Building Muppet Platform..."

# Build Docker image
docker build -t muppet-platform:local -f docker/Dockerfile .

echo "Build complete!"
EOF

    # Run script
    cat > scripts/run.sh << 'EOF'
#!/bin/bash

# Run script for Muppet Platform local development

set -e

echo "Starting Muppet Platform local development environment..."

# Start services with Docker Compose
docker-compose -f docker-compose.local.yml up -d

echo "Services started!"
echo "Platform API: http://localhost:8000"
echo "LocalStack: http://localhost:4566"
echo ""
echo "To view logs: docker-compose -f docker-compose.local.yml logs -f"
echo "To stop: docker-compose -f docker-compose.local.yml down"
EOF

    # Stop script
    cat > scripts/stop.sh << 'EOF'
#!/bin/bash

# Stop script for Muppet Platform local development

set -e

echo "Stopping Muppet Platform local development environment..."

# Stop services
docker-compose -f docker-compose.local.yml down

echo "Services stopped!"
EOF

    # Test script
    cat > scripts/test.sh << 'EOF'
#!/bin/bash

# Test script for Muppet Platform

set -e

echo "Running Muppet Platform tests..."

# Run tests with UV
uv run python -m pytest tests/ -v

echo "Tests complete!"
EOF

    # Make scripts executable
    chmod +x scripts/*.sh
    
    print_success "Development scripts created"
}

# Main setup function
main() {
    print_status "Starting Muppet Platform local development setup..."
    
    # Detect OS
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        *)          MACHINE="UNKNOWN:${OS}"
    esac
    
    print_status "Detected OS: $MACHINE"
    
    # Check and install Rancher Desktop
    if check_rancher_desktop; then
        print_success "Rancher Desktop is already running"
    else
        print_warning "Rancher Desktop not found or not running"
        
        if [[ "$MACHINE" == "Mac" ]]; then
            install_rancher_desktop_macos
        elif [[ "$MACHINE" == "Linux" ]]; then
            install_rancher_desktop_linux
        else
            print_error "Unsupported operating system: $MACHINE"
            exit 1
        fi
        
        print_warning "Please start Rancher Desktop and run this script again"
        exit 1
    fi
    
    # Install UV
    install_uv
    
    # Setup Python environment
    setup_python_env
    
    # Create Docker configurations
    create_docker_compose
    create_localstack_init
    create_dev_scripts
    
    print_success "Local development setup complete!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Set your GitHub token: export GITHUB_TOKEN=your_token_here"
    print_status "2. Build the platform: ./scripts/build.sh"
    print_status "3. Start the environment: ./scripts/run.sh"
    print_status "4. Run tests: ./scripts/test.sh"
    print_status ""
    print_status "Platform will be available at: http://localhost:8000"
    print_status "LocalStack will be available at: http://localhost:4566"
}

# Run main function
main "$@"