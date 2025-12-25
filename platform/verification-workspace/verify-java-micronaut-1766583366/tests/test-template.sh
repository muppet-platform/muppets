#!/bin/bash

# Java Micronaut Template Test Suite
# Tests template generation, build, and containerized deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_MUPPET_NAME="testtemplate$(date +%s)"
TEST_DIR="/tmp/${TEST_MUPPET_NAME}"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_IMAGE="${TEST_MUPPET_NAME}:test"
CONTAINER_NAME="${TEST_MUPPET_NAME}-container"
LOCALSTACK_CONTAINER="localstack-test"
TEST_PORT=3001

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up test resources...${NC}"
    
    # Stop and remove container if running
    if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
    if docker ps -aq -f name="${CONTAINER_NAME}" | grep -q .; then
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
    
    # Only stop and remove our test LocalStack container (not existing ones like muppet-localstack)
    if docker ps -q -f name="${LOCALSTACK_CONTAINER}" | grep -q .; then
        docker stop "${LOCALSTACK_CONTAINER}" >/dev/null 2>&1 || true
    fi
    if docker ps -aq -f name="${LOCALSTACK_CONTAINER}" | grep -q .; then
        docker rm "${LOCALSTACK_CONTAINER}" >/dev/null 2>&1 || true
    fi
    
    # Remove Docker image
    if docker images -q "${DOCKER_IMAGE}" | grep -q .; then
        docker rmi "${DOCKER_IMAGE}" >/dev/null 2>&1 || true
    fi
    
    # Remove test directory
    if [ -d "${TEST_DIR}" ]; then
        rm -rf "${TEST_DIR}"
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test functions
test_java_version() {
    log_info "Testing Java version compatibility..."
    
    # Check if Java 21 LTS is available
    if ! command -v java >/dev/null 2>&1; then
        log_error "Java not found. Please install Java 21 LTS."
        return 1
    fi
    
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -ne 21 ]; then
        log_warning "Java $JAVA_VERSION detected. Java 21 LTS is recommended."
        log_info "Setting JAVA_HOME to use Java 21 LTS if available..."
        
        # Try to find Java 21 LTS
        if [ -d "/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home" ]; then
            export JAVA_HOME="/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home"
            export PATH="$JAVA_HOME/bin:$PATH"
            log_success "Using Java 21 LTS from $JAVA_HOME"
        else
            log_error "Java 21 LTS not found. Please install Amazon Corretto 21."
            return 1
        fi
    else
        log_success "Java 21 LTS detected"
    fi
}

test_template_generation() {
    log_info "Testing template generation..."
    
    # Create test directory
    mkdir -p "${TEST_DIR}"
    cd "${TEST_DIR}"
    
    # Copy template files and substitute variables
    cp -r "${TEMPLATE_DIR}"/* .
    
    # Remove test directory to avoid recursion
    rm -rf tests/
    
    # Substitute template variables
    find . -type f -name "*.template" | while read -r file; do
        new_file="${file%.template}"
        sed "s/verify-java-micronaut-1766583366/${TEST_MUPPET_NAME}/g" "$file" > "$new_file"
        rm "$file"
    done
    
    # Substitute in other files
    find . -type f \( -name "*.java" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" -o -name "Dockerfile" \) -exec sed -i.bak "s/verify-java-micronaut-1766583366/${TEST_MUPPET_NAME}/g" {} \;
    find . -name "*.bak" -delete
    
    log_success "Template generated successfully"
}

test_gradle_build() {
    log_info "Testing Gradle build..."
    
    cd "${TEST_DIR}"
    
    # Make gradlew executable
    chmod +x gradlew
    
    # Test Gradle version
    ./gradlew --version
    
    # Clean and build shadowJar explicitly (needed for Docker)
    ./gradlew clean shadowJar --no-daemon
    
    # Verify JAR was created
    if [ ! -f "build/libs/${TEST_MUPPET_NAME}-1.0.0-all.jar" ]; then
        log_error "Shadow JAR not found"
        return 1
    fi
    
    log_success "Gradle build completed successfully"
}

test_unit_tests() {
    log_info "Testing unit tests..."
    
    cd "${TEST_DIR}"
    
    # Run tests
    ./gradlew test --no-daemon
    
    # Check test results
    if ls build/test-results/test/TEST-*.xml 1> /dev/null 2>&1; then
        log_success "Unit tests passed"
    else
        log_error "Test results not found"
        return 1
    fi
}

test_docker_build() {
    log_info "Testing Docker build..."
    
    cd "${TEST_DIR}"
    
    # Build Docker image
    docker build -t "${DOCKER_IMAGE}" .
    
    # Verify image was created
    if ! docker images -q "${DOCKER_IMAGE}" | grep -q .; then
        log_error "Docker image not found"
        return 1
    fi
    
    log_success "Docker image built successfully"
}

test_localstack_setup() {
    log_info "Setting up LocalStack for AWS services..."
    
    # First, check if existing LocalStack is running on port 4566
    if curl -s http://localhost:4566/_localstack/health >/dev/null 2>&1; then
        log_info "Found existing LocalStack running on port 4566, reusing..."
        export LOCALSTACK_PORT=4566
        return 0
    fi
    
    # Check for existing LocalStack containers (like muppet-localstack)
    EXISTING_LOCALSTACK=$(docker ps -q -f ancestor=localstack/localstack | head -1)
    if [ -n "$EXISTING_LOCALSTACK" ]; then
        # Get the container name and port mapping
        CONTAINER_NAME=$(docker inspect --format='{{.Name}}' "$EXISTING_LOCALSTACK" | sed 's/\///')
        LOCALSTACK_PORT=$(docker port "$EXISTING_LOCALSTACK" 4566/tcp | cut -d: -f2)
        
        if [ -n "$LOCALSTACK_PORT" ]; then
            log_info "Found existing LocalStack container '$CONTAINER_NAME' on port $LOCALSTACK_PORT, reusing..."
            export LOCALSTACK_PORT
            return 0
        fi
    fi
    
    # Check if our test LocalStack container exists and remove it
    if docker ps -aq -f name="${LOCALSTACK_CONTAINER}" | grep -q .; then
        log_info "Removing existing test LocalStack container..."
        docker rm -f "${LOCALSTACK_CONTAINER}" >/dev/null 2>&1 || true
    fi
    
    # Start new LocalStack container for testing
    log_info "Starting new LocalStack container for testing..."
    local LOCALSTACK_PORT=4567
    
    docker run -d \
        --name "${LOCALSTACK_CONTAINER}" \
        -p ${LOCALSTACK_PORT}:4566 \
        -e SERVICES=cloudwatch \
        -e DEBUG=1 \
        localstack/localstack:latest
    
    # Wait for LocalStack to be ready
    log_info "Waiting for LocalStack to be ready on port ${LOCALSTACK_PORT}..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:${LOCALSTACK_PORT}/_localstack/health | grep -q '"cloudwatch": "available"'; then
            break
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "LocalStack failed to start"
        docker logs "${LOCALSTACK_CONTAINER}"
        return 1
    fi
    
    # Store the port for later use
    export LOCALSTACK_PORT
    log_success "LocalStack is ready on port ${LOCALSTACK_PORT}"
}

test_container_startup() {
    log_info "Testing container startup..."
    
    # Determine LocalStack endpoint based on the port we're using
    local LOCALSTACK_ENDPOINT
    if [ "${LOCALSTACK_PORT}" = "4566" ]; then
        # Using existing LocalStack on standard port
        LOCALSTACK_ENDPOINT="http://host.docker.internal:4566"
        log_info "Using existing LocalStack on standard port 4566"
    else
        # Using our test LocalStack on alternative port
        LOCALSTACK_ENDPOINT="http://host.docker.internal:${LOCALSTACK_PORT}"
        log_info "Using test LocalStack on port ${LOCALSTACK_PORT}"
    fi
    
    log_info "Using LocalStack endpoint: ${LOCALSTACK_ENDPOINT}"
    
    # Start container with AWS configuration pointing to LocalStack
    docker run -d \
        -p "${TEST_PORT}:3000" \
        -e "AWS_ACCESS_KEY_ID=test" \
        -e "AWS_SECRET_ACCESS_KEY=test" \
        -e "AWS_REGION=us-east-1" \
        -e "AWS_ENDPOINT_OVERRIDE=${LOCALSTACK_ENDPOINT}" \
        --name "${CONTAINER_NAME}" \
        "${DOCKER_IMAGE}"
    
    # Wait for container to start and check if it's running
    log_info "Waiting for container to start..."
    sleep 15
    
    # Check if container is running
    if ! docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        log_error "Container failed to start"
        log_info "Container logs:"
        docker logs "${CONTAINER_NAME}" 2>/dev/null || true
        return 1
    fi
    
    # Wait a bit more for the application to fully start
    log_info "Waiting for application to start..."
    sleep 10
    
    log_success "Container started successfully"
}

test_health_endpoints() {
    log_info "Testing health endpoints..."
    
    # Wait for application to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:${TEST_PORT}/health" >/dev/null 2>&1; then
            break
        fi
        log_info "Attempt $attempt/$max_attempts: Waiting for application to be ready..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Application failed to start within expected time"
        docker logs "${CONTAINER_NAME}" 2>/dev/null || true
        return 1
    fi
    
    # Test health endpoint
    if ! curl -f -s "http://localhost:${TEST_PORT}/health" >/dev/null; then
        log_error "Health endpoint failed"
        return 1
    fi
    
    # Test API endpoint
    if ! curl -f -s "http://localhost:${TEST_PORT}/api" >/dev/null; then
        log_error "API endpoint failed"
        return 1
    fi
    
    # Test readiness endpoint
    if ! curl -f -s "http://localhost:${TEST_PORT}/health/ready" >/dev/null; then
        log_error "Ready endpoint failed"
        return 1
    fi
    
    # Test liveness endpoint
    if ! curl -f -s "http://localhost:${TEST_PORT}/health/live" >/dev/null; then
        log_error "Live endpoint failed"
        return 1
    fi
    
    log_success "All health endpoints working"
}

test_api_responses() {
    log_info "Testing API responses..."
    
    # Test health response format
    HEALTH_RESPONSE=$(curl -s "http://localhost:${TEST_PORT}/health")
    if ! echo "$HEALTH_RESPONSE" | grep -q '"status":"UP"'; then
        log_error "Invalid health response: $HEALTH_RESPONSE"
        return 1
    fi
    
    # Test API response format
    API_RESPONSE=$(curl -s "http://localhost:${TEST_PORT}/api")
    if ! echo "$API_RESPONSE" | grep -q "\"service\":\"${TEST_MUPPET_NAME}\""; then
        log_error "Invalid API response: $API_RESPONSE"
        return 1
    fi
    
    log_success "API responses are correct"
}

# Main test execution
main() {
    echo -e "${BLUE}🧪 Starting Java Micronaut Template Test Suite${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    # Run tests in sequence
    test_java_version
    test_template_generation
    test_gradle_build
    test_unit_tests
    test_docker_build
    test_localstack_setup
    test_container_startup
    test_health_endpoints
    test_api_responses
    
    echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
    echo -e "${GREEN}Template is ready for production use.${NC}"
}

# Run main function
main "$@"