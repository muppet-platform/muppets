#!/bin/bash

# Java Micronaut Template Verification Script
# Tests template generation, parameter injection, Docker build, and local functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_MUPPET_NAME="test-muppet-$(date +%s)"
TEST_DIR="/tmp/muppet-template-test"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFICATION_PORT=3001

echo -e "${BLUE}🧪 Java Micronaut Template Verification${NC}"
echo "========================================"
echo "Template: $TEMPLATE_DIR"
echo "Test muppet: $TEST_MUPPET_NAME"
echo "Test directory: $TEST_DIR"
echo ""

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Stop any running containers
    if docker ps -q --filter "name=${TEST_MUPPET_NAME}" | grep -q .; then
        echo "Stopping Docker container..."
        docker stop "${TEST_MUPPET_NAME}-test" 2>/dev/null || true
        docker rm "${TEST_MUPPET_NAME}-test" 2>/dev/null || true
    fi
    
    # Remove test images
    if docker images -q "${TEST_MUPPET_NAME}" | grep -q .; then
        echo "Removing Docker images..."
        docker rmi "${TEST_MUPPET_NAME}:latest" 2>/dev/null || true
        docker rmi "${TEST_MUPPET_NAME}:dev" 2>/dev/null || true
    fi
    
    # Remove test directory
    if [ -d "$TEST_DIR" ]; then
        echo "Removing test directory..."
        rm -rf "$TEST_DIR"
    fi
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Set trap for cleanup
trap cleanup EXIT

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local timeout=${2:-30}
    local count=0
    
    echo "Waiting for service at $url..."
    while [ $count -lt $timeout ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Service is ready${NC}"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    
    echo -e "${RED}❌ Service failed to start within ${timeout}s${NC}"
    return 1
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3
    
    echo "Testing $description: $url"
    
    local response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url")
    local status_code="${response: -3}"
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $description: HTTP $status_code${NC}"
        if [ -f /tmp/response.json ]; then
            echo "Response: $(cat /tmp/response.json)"
        fi
        return 0
    else
        echo -e "${RED}❌ $description: Expected HTTP $expected_status, got $status_code${NC}"
        if [ -f /tmp/response.json ]; then
            echo "Response: $(cat /tmp/response.json)"
        fi
        return 1
    fi
}

# Step 1: Prerequisites check
echo -e "${BLUE}📋 Step 1: Checking prerequisites${NC}"

if ! command_exists java; then
    echo -e "${RED}❌ Java not found${NC}"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 21 ]; then
    echo -e "${RED}❌ Java 21+ required, found Java $JAVA_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Java $JAVA_VERSION found${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

if ! command_exists curl; then
    echo -e "${RED}❌ curl not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ curl found${NC}"

# Step 2: Template generation and parameter injection
echo -e "${BLUE}📝 Step 2: Testing template generation and parameter injection${NC}"

# Create test directory
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Copy template files and inject parameters
echo "Copying template files..."
cp -r "$TEMPLATE_DIR"/* .

# Function to replace template variables
replace_template_vars() {
    local file=$1
    if [ -f "$file" ]; then
        sed -i.bak "s/verify-java-micronaut-1766638048/${TEST_MUPPET_NAME}/g" "$file"
        rm -f "${file}.bak"
    fi
}

# Replace template variables in all files
echo "Injecting parameters..."
find . -type f \( -name "*.java" -o -name "*.gradle" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" -o -name "*.sh" -o -name "Dockerfile*" \) -exec bash -c 'replace_template_vars "$0"' {} \;

# Rename template files
if [ -f "Dockerfile.template" ]; then
    mv "Dockerfile.template" "Dockerfile"
fi
if [ -f "build.gradle.template" ]; then
    mv "build.gradle.template" "build.gradle"
fi
if [ -f "gradle.properties.template" ]; then
    mv "gradle.properties.template" "gradle.properties"
fi
if [ -f "settings.gradle.template" ]; then
    mv "settings.gradle.template" "settings.gradle"
fi
if [ -f "docker-compose.local.yml.template" ]; then
    mv "docker-compose.local.yml.template" "docker-compose.local.yml"
fi
if [ -f "README.template.md" ]; then
    mv "README.template.md" "README.md"
fi

echo -e "${GREEN}✅ Template generation and parameter injection complete${NC}"

# Verify key files exist
echo "Verifying generated files..."
required_files=(
    "src/main/java/com/muppetplatform/${TEST_MUPPET_NAME}/Application.java"
    "src/main/java/com/muppetplatform/${TEST_MUPPET_NAME}/controller/HealthController.java"
    "src/main/java/com/muppetplatform/${TEST_MUPPET_NAME}/controller/ApiController.java"
    "build.gradle"
    "Dockerfile"
    "gradlew"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        exit 1
    fi
done

# Step 3: Build verification
echo -e "${BLUE}🏗️  Step 3: Testing build process${NC}"

# Make gradlew executable
chmod +x gradlew

# Test Gradle wrapper
echo "Testing Gradle wrapper..."
./gradlew --version
echo -e "${GREEN}✅ Gradle wrapper working${NC}"

# Clean and build
echo "Building application..."
./gradlew clean shadowJar

# Verify JAR was created
JAR_FILE=$(find build/libs -name "${TEST_MUPPET_NAME}-*-all.jar" | head -n 1)
if [ -n "$JAR_FILE" ] && [ -f "$JAR_FILE" ]; then
    echo -e "${GREEN}✅ JAR built successfully: $JAR_FILE${NC}"
else
    echo -e "${RED}❌ JAR build failed${NC}"
    exit 1
fi

# Step 4: Docker build verification
echo -e "${BLUE}🐳 Step 4: Testing Docker build${NC}"

echo "Building Docker image..."
docker build -t "${TEST_MUPPET_NAME}:latest" .

# Verify image was created
if docker images -q "${TEST_MUPPET_NAME}:latest" | grep -q .; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker image build failed${NC}"
    exit 1
fi

# Step 5: Container startup and health check
echo -e "${BLUE}🚀 Step 5: Testing container startup and health endpoints${NC}"

# Start container in background
echo "Starting Docker container..."
docker run -d \
    --name "${TEST_MUPPET_NAME}-test" \
    -p "${VERIFICATION_PORT}:3000" \
    -e MICRONAUT_ENVIRONMENTS=development \
    -e MUPPET_NAME="${TEST_MUPPET_NAME}" \
    "${TEST_MUPPET_NAME}:latest"

# Wait for container to be ready
if wait_for_service "http://localhost:${VERIFICATION_PORT}/health" 60; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
else
    echo -e "${RED}❌ Container failed to start${NC}"
    echo "Container logs:"
    docker logs "${TEST_MUPPET_NAME}-test"
    exit 1
fi

# Step 6: API endpoint testing
echo -e "${BLUE}🔍 Step 6: Testing API endpoints${NC}"

# Test health endpoint
test_endpoint "http://localhost:${VERIFICATION_PORT}/health" 200 "Health endpoint"

# Test readiness endpoint
test_endpoint "http://localhost:${VERIFICATION_PORT}/health/ready" 200 "Readiness endpoint"

# Test liveness endpoint
test_endpoint "http://localhost:${VERIFICATION_PORT}/health/live" 200 "Liveness endpoint"

# Test API endpoint
test_endpoint "http://localhost:${VERIFICATION_PORT}/api" 200 "API endpoint"

# Step 7: Local development integration test
echo -e "${BLUE}🛠️  Step 7: Testing local development integration${NC}"

# Stop the Docker container
docker stop "${TEST_MUPPET_NAME}-test"
docker rm "${TEST_MUPPET_NAME}-test"

# Test init script
echo "Testing init script..."
if [ -f "scripts/init.sh" ]; then
    chmod +x scripts/init.sh
    # Run init script in non-interactive mode
    echo -e "${GREEN}✅ Init script exists and is executable${NC}"
else
    echo -e "${RED}❌ Init script not found${NC}"
    exit 1
fi

# Test build script
echo "Testing build script..."
if [ -f "scripts/build.sh" ]; then
    chmod +x scripts/build.sh
    ./scripts/build.sh
    echo -e "${GREEN}✅ Build script executed successfully${NC}"
else
    echo -e "${RED}❌ Build script not found${NC}"
    exit 1
fi

# Test run script with JAR mode (non-blocking)
echo "Testing run script (JAR mode)..."
if [ -f "scripts/run.sh" ]; then
    chmod +x scripts/run.sh
    
    # Start in background
    ./scripts/run.sh &
    RUN_PID=$!
    
    # Wait for service to be ready
    if wait_for_service "http://localhost:3000/health" 30; then
        echo -e "${GREEN}✅ Run script (JAR mode) working${NC}"
        
        # Test endpoints again
        test_endpoint "http://localhost:3000/health" 200 "Health endpoint (JAR mode)"
        test_endpoint "http://localhost:3000/api" 200 "API endpoint (JAR mode)"
        
        # Stop the process
        kill $RUN_PID 2>/dev/null || true
        wait $RUN_PID 2>/dev/null || true
    else
        echo -e "${RED}❌ Run script (JAR mode) failed${NC}"
        kill $RUN_PID 2>/dev/null || true
        exit 1
    fi
else
    echo -e "${RED}❌ Run script not found${NC}"
    exit 1
fi

# Step 8: Test script verification
echo -e "${BLUE}🧪 Step 8: Testing test script${NC}"

if [ -f "scripts/test.sh" ]; then
    chmod +x scripts/test.sh
    ./scripts/test.sh
    echo -e "${GREEN}✅ Test script executed successfully${NC}"
else
    echo -e "${RED}❌ Test script not found${NC}"
    exit 1
fi

# Step 9: Configuration validation
echo -e "${BLUE}⚙️  Step 9: Validating configuration${NC}"

# Check Java version in build.gradle
if grep -q "JavaVersion.VERSION_21" build.gradle; then
    echo -e "${GREEN}✅ Java 21 configured in build.gradle${NC}"
else
    echo -e "${RED}❌ Java 21 not configured in build.gradle${NC}"
    exit 1
fi

# Check port configuration
if grep -q "3000" src/main/resources/application.yml 2>/dev/null || grep -q "SERVER_PORT=3000" .env.local 2>/dev/null; then
    echo -e "${GREEN}✅ Port 3000 configured${NC}"
else
    echo -e "${YELLOW}⚠️  Port 3000 configuration not found (using default)${NC}"
fi

# Check Amazon Corretto in Dockerfile
if grep -q "amazoncorretto:21" Dockerfile; then
    echo -e "${GREEN}✅ Amazon Corretto 21 configured in Dockerfile${NC}"
else
    echo -e "${RED}❌ Amazon Corretto 21 not configured in Dockerfile${NC}"
    exit 1
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 Template Verification Complete!${NC}"
echo "========================================"
echo -e "${GREEN}✅ Template generation and parameter injection${NC}"
echo -e "${GREEN}✅ Gradle build process${NC}"
echo -e "${GREEN}✅ Docker image build${NC}"
echo -e "${GREEN}✅ Container startup and health checks${NC}"
echo -e "${GREEN}✅ API endpoint functionality${NC}"
echo -e "${GREEN}✅ Local development scripts${NC}"
echo -e "${GREEN}✅ Test execution${NC}"
echo -e "${GREEN}✅ Configuration validation${NC}"
echo ""
echo "The Java Micronaut template is ready for production use!"
echo ""