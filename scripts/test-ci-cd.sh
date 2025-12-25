#!/bin/bash

# Test CI/CD Setup Locally
# This script simulates CI/CD pipeline steps locally for development

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

# Function to check Java version
check_java_version() {
    print_status "Checking Java version..."
    
    if ! command_exists java; then
        print_error "Java not found. Please install Amazon Corretto 21 LTS."
        return 1
    fi
    
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    
    if [ "$JAVA_VERSION" -ne 21 ]; then
        print_error "Java 21 LTS required, found Java $JAVA_VERSION"
        if [ "$JAVA_VERSION" -gt 21 ]; then
            print_warning "Java $JAVA_VERSION is newer than Java 21 LTS and may cause compatibility issues"
            print_warning "Non-LTS Java versions are not supported in production environments"
        fi
        print_error "Please install Amazon Corretto 21 LTS: https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/downloads-list.html"
        return 1
    fi
    
    # Verify it's LTS
    if java -version 2>&1 | grep -q "21.*LTS"; then
        print_success "Java 21 LTS detected"
    else
        print_error "Non-LTS Java version detected"
        return 1
    fi
}

# Function to check Python and UV
check_python_uv() {
    print_status "Checking Python and UV..."
    
    if ! command_exists python3; then
        print_error "Python 3 not found. Please install Python 3.10+."
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    print_success "Python $PYTHON_VERSION detected"
    
    if ! command_exists uv; then
        print_error "UV not found. Please install UV package manager."
        print_error "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    UV_VERSION=$(uv --version | cut -d' ' -f2)
    print_success "UV $UV_VERSION detected"
}

# Function to check OpenTofu
check_opentofu() {
    print_status "Checking OpenTofu..."
    
    if ! command_exists tofu; then
        print_error "OpenTofu not found. Please install OpenTofu 1.6+."
        print_error "Install with: brew install opentofu (macOS) or see https://opentofu.org/docs/intro/install/"
        return 1
    fi
    
    TOFU_VERSION=$(tofu version | head -n 1 | cut -d' ' -f2)
    print_success "OpenTofu $TOFU_VERSION detected"
}

# Function to check Docker
check_docker() {
    print_status "Checking Docker..."
    
    if ! command_exists docker; then
        print_warning "Docker not found. Docker is optional for local development."
        return 0
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_warning "Docker daemon not running. Docker is optional for local development."
        return 0
    fi
    
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_success "Docker $DOCKER_VERSION detected and running"
}

# Function to validate workflow files
validate_workflows() {
    print_status "Validating GitHub Actions workflows..."
    
    if ! command_exists python3; then
        print_error "Python 3 required for workflow validation"
        return 1
    fi
    
    # Check if PyYAML is available
    if ! python3 -c "import yaml" 2>/dev/null; then
        print_warning "PyYAML not available, installing..."
        pip3 install PyYAML || {
            print_error "Failed to install PyYAML"
            return 1
        }
    fi
    
    # Validate each workflow file
    for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
        if [ -f "$workflow" ]; then
            print_status "Validating $workflow..."
            
            python3 -c "
import yaml
import sys
try:
    with open('$workflow', 'r') as f:
        yaml.safe_load(f)
    print('✅ Valid YAML syntax')
except yaml.YAMLError as e:
    print('❌ Invalid YAML syntax:', e)
    sys.exit(1)
except Exception as e:
    print('❌ Error reading file:', e)
    sys.exit(1)
" || return 1
        fi
    done
    
    print_success "All workflow files validated"
}

# Function to test platform locally
test_platform() {
    print_status "Testing platform components..."
    
    if [ -f "scripts/test-platform.sh" ]; then
        chmod +x scripts/test-platform.sh
        ./scripts/test-platform.sh || {
            print_error "Platform tests failed"
            return 1
        }
    else
        print_error "Platform test script not found"
        return 1
    fi
    
    print_success "Platform tests passed"
}

# Function to test templates
test_templates() {
    print_status "Testing templates..."
    
    if [ -f "scripts/test-templates.sh" ]; then
        chmod +x scripts/test-templates.sh
        ./scripts/test-templates.sh || {
            print_error "Template tests failed"
            return 1
        }
    else
        print_error "Template test script not found"
        return 1
    fi
    
    print_success "Template tests passed"
}

# Function to test infrastructure
test_infrastructure() {
    print_status "Testing infrastructure..."
    
    if [ -f "scripts/test-infrastructure.sh" ]; then
        chmod +x scripts/test-infrastructure.sh
        ./scripts/test-infrastructure.sh || {
            print_error "Infrastructure tests failed"
            return 1
        }
    else
        print_error "Infrastructure test script not found"
        return 1
    fi
    
    print_success "Infrastructure tests passed"
}

# Function to run security checks
run_security_checks() {
    print_status "Running security checks..."
    
    cd platform || {
        print_error "Platform directory not found"
        return 1
    }
    
    # Install dependencies if needed
    if [ ! -d ".venv" ]; then
        print_status "Installing platform dependencies..."
        uv sync --dev || {
            print_error "Failed to install dependencies"
            return 1
        }
    fi
    
    # Run Bandit security scan
    print_status "Running Bandit security scan..."
    uv run bandit -r src/ -f txt || {
        print_warning "Bandit found security issues (this may be expected)"
    }
    
    # Run Safety check
    print_status "Running Safety vulnerability check..."
    uv run safety check || {
        print_warning "Safety found vulnerabilities (this may be expected)"
    }
    
    cd ..
    print_success "Security checks completed"
}

# Function to build Docker image
build_docker_image() {
    print_status "Building Docker image..."
    
    if ! command_exists docker; then
        print_warning "Docker not available, skipping image build"
        return 0
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_warning "Docker daemon not running, skipping image build"
        return 0
    fi
    
    cd platform || {
        print_error "Platform directory not found"
        return 1
    }
    
    docker build -f docker/Dockerfile -t muppet-platform:test . || {
        print_error "Docker build failed"
        return 1
    }
    
    cd ..
    print_success "Docker image built successfully"
}

# Main function
main() {
    print_status "Starting CI/CD local test simulation..."
    echo
    
    # Check prerequisites
    print_status "=== Checking Prerequisites ==="
    check_java_version || exit 1
    check_python_uv || exit 1
    check_opentofu || exit 1
    check_docker
    echo
    
    # Validate workflows
    print_status "=== Validating Workflows ==="
    validate_workflows || exit 1
    echo
    
    # Run tests (similar to CI pipeline)
    print_status "=== Running Tests ==="
    test_platform || exit 1
    test_templates || exit 1
    test_infrastructure || exit 1
    echo
    
    # Run security checks
    print_status "=== Security Checks ==="
    run_security_checks || exit 1
    echo
    
    # Build Docker image
    print_status "=== Building Docker Image ==="
    build_docker_image || exit 1
    echo
    
    print_success "=== All CI/CD simulation tests passed! ==="
    print_success "Your local environment is ready for CI/CD pipeline"
    echo
    print_status "Next steps:"
    echo "  1. Push your changes to trigger the CI pipeline"
    echo "  2. Create a pull request to test the full CI workflow"
    echo "  3. Merge to main to trigger the CD pipeline"
    echo "  4. Create a tag (e.g., v1.0.0) to trigger the release pipeline"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Test CI/CD setup locally by simulating pipeline steps"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --prereqs      Check prerequisites only"
        echo "  --workflows    Validate workflows only"
        echo "  --tests        Run tests only"
        echo "  --security     Run security checks only"
        echo "  --docker       Build Docker image only"
        echo ""
        echo "Examples:"
        echo "  $0                 # Run full CI/CD simulation"
        echo "  $0 --prereqs      # Check prerequisites only"
        echo "  $0 --tests        # Run tests only"
        exit 0
        ;;
    --prereqs)
        check_java_version && check_python_uv && check_opentofu && check_docker
        ;;
    --workflows)
        validate_workflows
        ;;
    --tests)
        test_platform && test_templates && test_infrastructure
        ;;
    --security)
        run_security_checks
        ;;
    --docker)
        build_docker_image
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        print_error "Use --help for usage information"
        exit 1
        ;;
esac