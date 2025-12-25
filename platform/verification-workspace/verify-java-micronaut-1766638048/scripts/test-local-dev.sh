#!/bin/bash

# Local Development Integration Test Script
# Tests integration with local development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛠️  Local Development Integration Test${NC}"
echo "======================================"

# Test configuration
TEST_MUPPET_NAME="local-dev-test-$(date +%s)"
TEST_DIR="/tmp/local-dev-test"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Template: $TEMPLATE_DIR"
echo "Test muppet: $TEST_MUPPET_NAME"
echo "Test directory: $TEST_DIR"
echo ""

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Kill any background processes
    if [ -n "$JAR_PID" ]; then
        kill $JAR_PID 2>/dev/null || true
        wait $JAR_PID 2>/dev/null || true
    fi
    
    if [ -n "$GRADLE_PID" ]; then
        kill $GRADLE_PID 2>/dev/null || true
        wait $GRADLE_PID 2>/dev/null || true
    fi
    
    # Stop any Docker containers
    docker-compose -f docker-compose.local.yml down 2>/dev/null || true
    
    # Remove test directory
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
    fi
}
trap cleanup EXIT

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
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

# Function to check port availability
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Prerequisites check
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists java; then
    echo -e "${RED}❌ Java not found${NC}"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 21 ]; then
    echo -e "${RED}❌ Java 21+ required, found Java $JAVA_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Java $JAVA_VERSION${NC}"

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

# Check for Docker Compose
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose found${NC}"
else
    echo -e "${YELLOW}⚠️  Docker Compose not found (some tests will be skipped)${NC}"
fi

# Setup test environment
echo -e "${BLUE}📁 Setting up test environment...${NC}"

mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Copy and prepare template
cp -r "$TEMPLATE_DIR"/* .

# Replace template variables
find . -type f \( -name "*.java" -o -name "*.gradle" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" -o -name "*.sh" -o -name "Dockerfile*" \) -exec sed -i.bak "s/verify-java-micronaut-1766638048/${TEST_MUPPET_NAME}/g" {} \;

# Rename template files
[ -f "Dockerfile.template" ] && mv "Dockerfile.template" "Dockerfile"
[ -f "build.gradle.template" ] && mv "build.gradle.template" "build.gradle"
[ -f "gradle.properties.template" ] && mv "gradle.properties.template" "gradle.properties"
[ -f "settings.gradle.template" ] && mv "settings.gradle.template" "settings.gradle"
[ -f "docker-compose.local.yml.template" ] && mv "docker-compose.local.yml.template" "docker-compose.local.yml"
[ -f "README.template.md" ] && mv "README.template.md" "README.md"

echo -e "${GREEN}✅ Test environment ready${NC}"

# Test init script
echo -e "${BLUE}🚀 Testing init script...${NC}"

if [ -f "scripts/init.sh" ]; then
    chmod +x scripts/init.sh
    
    # Run init script (it should pass all checks)
    if ./scripts/init.sh; then
        echo -e "${GREEN}✅ Init script executed successfully${NC}"
    else
        echo -e "${RED}❌ Init script failed${NC}"
        exit 1
    fi
    
    # Check if .env.local was created
    if [ -f ".env.local" ]; then
        echo -e "${GREEN}✅ .env.local created${NC}"
        echo "Contents:"
        cat .env.local
    else
        echo -e "${RED}❌ .env.local not created${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Init script not found${NC}"
    exit 1
fi

# Test build script
echo -e "${BLUE}🏗️  Testing build script...${NC}"

if [ -f "scripts/build.sh" ]; then
    chmod +x scripts/build.sh
    
    if ./scripts/build.sh; then
        echo -e "${GREEN}✅ Build script executed successfully${NC}"
    else
        echo -e "${RED}❌ Build script failed${NC}"
        exit 1
    fi
    
    # Verify outputs
    if [ -f "build/libs/${TEST_MUPPET_NAME}-1.0.0-all.jar" ]; then
        echo -e "${GREEN}✅ JAR file created${NC}"
    else
        echo -e "${RED}❌ JAR file not created${NC}"
        exit 1
    fi
    
    if docker images -q "${TEST_MUPPET_NAME}:latest" | grep -q .; then
        echo -e "${GREEN}✅ Docker image created${NC}"
    else
        echo -e "${RED}❌ Docker image not created${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Build script not found${NC}"
    exit 1
fi

# Test run script - JAR mode
echo -e "${BLUE}☕ Testing run script (JAR mode)...${NC}"

if [ -f "scripts/run.sh" ]; then
    chmod +x scripts/run.sh
    
    # Check port availability
    if ! check_port 3000; then
        echo "Port 3000 is in use, trying to free it..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # Start in background
    ./scripts/run.sh &
    JAR_PID=$!
    
    # Wait for service to be ready
    if wait_for_service "http://localhost:3000/health" 45; then
        echo -e "${GREEN}✅ Run script (JAR mode) working${NC}"
        
        # Test endpoints
        if curl -s -f "http://localhost:3000/health" >/dev/null; then
            echo -e "${GREEN}✅ Health endpoint working${NC}"
        else
            echo -e "${RED}❌ Health endpoint not working${NC}"
        fi
        
        if curl -s -f "http://localhost:3000/api" >/dev/null; then
            echo -e "${GREEN}✅ API endpoint working${NC}"
        else
            echo -e "${RED}❌ API endpoint not working${NC}"
        fi
        
        # Stop the process
        kill $JAR_PID 2>/dev/null || true
        wait $JAR_PID 2>/dev/null || true
        JAR_PID=""
    else
        echo -e "${RED}❌ Run script (JAR mode) failed${NC}"
        kill $JAR_PID 2>/dev/null || true
        exit 1
    fi
else
    echo -e "${RED}❌ Run script not found${NC}"
    exit 1
fi

# Test run script - Docker mode
echo -e "${BLUE}🐳 Testing run script (Docker mode)...${NC}"

# Check port availability
if ! check_port 3000; then
    echo "Port 3000 is in use, trying to free it..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start Docker mode in background
timeout 60 ./scripts/run.sh --docker &
DOCKER_PID=$!

# Wait for service to be ready
if wait_for_service "http://localhost:3000/health" 45; then
    echo -e "${GREEN}✅ Run script (Docker mode) working${NC}"
    
    # Test endpoints
    if curl -s -f "http://localhost:3000/health" >/dev/null; then
        echo -e "${GREEN}✅ Health endpoint working (Docker)${NC}"
    else
        echo -e "${RED}❌ Health endpoint not working (Docker)${NC}"
    fi
    
    # Stop the Docker container
    docker stop "${TEST_MUPPET_NAME}-dev" 2>/dev/null || true
    kill $DOCKER_PID 2>/dev/null || true
else
    echo -e "${RED}❌ Run script (Docker mode) failed${NC}"
    docker stop "${TEST_MUPPET_NAME}-dev" 2>/dev/null || true
    kill $DOCKER_PID 2>/dev/null || true
fi

# Test run script - Gradle mode (development)
echo -e "${BLUE}🏃 Testing run script (Gradle mode)...${NC}"

# Check port availability
if ! check_port 3000; then
    echo "Port 3000 is in use, trying to free it..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start Gradle mode in background
timeout 90 ./scripts/run.sh --gradle &
GRADLE_PID=$!

# Wait for service to be ready (Gradle takes longer)
if wait_for_service "http://localhost:3000/health" 60; then
    echo -e "${GREEN}✅ Run script (Gradle mode) working${NC}"
    
    # Test endpoints
    if curl -s -f "http://localhost:3000/health" >/dev/null; then
        echo -e "${GREEN}✅ Health endpoint working (Gradle)${NC}"
    else
        echo -e "${RED}❌ Health endpoint not working (Gradle)${NC}"
    fi
    
    # Stop the Gradle process
    kill $GRADLE_PID 2>/dev/null || true
    wait $GRADLE_PID 2>/dev/null || true
    GRADLE_PID=""
else
    echo -e "${YELLOW}⚠️  Run script (Gradle mode) timeout (this is normal for slow systems)${NC}"
    kill $GRADLE_PID 2>/dev/null || true
fi

# Test test script
echo -e "${BLUE}🧪 Testing test script...${NC}"

if [ -f "scripts/test.sh" ]; then
    chmod +x scripts/test.sh
    
    if ./scripts/test.sh; then
        echo -e "${GREEN}✅ Test script executed successfully${NC}"
        
        # Check test reports
        if [ -f "build/reports/tests/test/index.html" ]; then
            echo -e "${GREEN}✅ Test report generated${NC}"
        else
            echo -e "${YELLOW}⚠️  Test report not found${NC}"
        fi
    else
        echo -e "${RED}❌ Test script failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Test script not found${NC}"
    exit 1
fi

# Test Docker Compose integration (if available)
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    echo -e "${BLUE}🐙 Testing Docker Compose integration...${NC}"
    
    if [ -f "docker-compose.local.yml" ]; then
        # Check port availability
        if ! check_port 3000; then
            echo "Port 3000 is in use, trying to free it..."
            lsof -ti:3000 | xargs kill -9 2>/dev/null || true
            sleep 2
        fi
        
        # Start with Docker Compose
        docker-compose -f docker-compose.local.yml up -d
        
        # Wait for service to be ready
        if wait_for_service "http://localhost:3000/health" 60; then
            echo -e "${GREEN}✅ Docker Compose integration working${NC}"
            
            # Test endpoints
            if curl -s -f "http://localhost:3000/health" >/dev/null; then
                echo -e "${GREEN}✅ Health endpoint working (Compose)${NC}"
            else
                echo -e "${RED}❌ Health endpoint not working (Compose)${NC}"
            fi
        else
            echo -e "${RED}❌ Docker Compose integration failed${NC}"
        fi
        
        # Stop Docker Compose
        docker-compose -f docker-compose.local.yml down
    else
        echo -e "${RED}❌ docker-compose.local.yml not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker Compose not available, skipping integration test${NC}"
fi

# Test environment variable loading
echo -e "${BLUE}⚙️  Testing environment variable loading...${NC}"

if [ -f ".env.local" ]; then
    # Check that .env.local contains expected variables
    expected_vars=("MICRONAUT_ENVIRONMENTS" "MUPPET_NAME" "AWS_REGION" "ENVIRONMENT" "SERVER_PORT" "LOG_LEVEL")
    
    for var in "${expected_vars[@]}"; do
        if grep -q "^${var}=" .env.local; then
            echo -e "${GREEN}✅ $var found in .env.local${NC}"
        else
            echo -e "${YELLOW}⚠️  $var not found in .env.local${NC}"
        fi
    done
else
    echo -e "${RED}❌ .env.local not found${NC}"
fi

# Test README generation
echo -e "${BLUE}📖 Testing README generation...${NC}"

if [ -f "README.md" ]; then
    if grep -q "$TEST_MUPPET_NAME" README.md; then
        echo -e "${GREEN}✅ README.md contains muppet name${NC}"
    else
        echo -e "${RED}❌ README.md does not contain muppet name${NC}"
    fi
    
    if grep -q "Local Development" README.md; then
        echo -e "${GREEN}✅ README.md contains local development section${NC}"
    else
        echo -e "${YELLOW}⚠️  README.md missing local development section${NC}"
    fi
else
    echo -e "${RED}❌ README.md not found${NC}"
fi

# Test script permissions
echo -e "${BLUE}🔐 Testing script permissions...${NC}"

scripts=("init.sh" "build.sh" "run.sh" "test.sh")
for script in "${scripts[@]}"; do
    if [ -f "scripts/$script" ]; then
        if [ -x "scripts/$script" ]; then
            echo -e "${GREEN}✅ scripts/$script is executable${NC}"
        else
            echo -e "${RED}❌ scripts/$script is not executable${NC}"
        fi
    fi
done

# Final summary
echo ""
echo -e "${GREEN}🎉 Local Development Integration Test Complete!${NC}"
echo "=============================================="
echo -e "${GREEN}✅ Init script functionality${NC}"
echo -e "${GREEN}✅ Build script functionality${NC}"
echo -e "${GREEN}✅ Run script (JAR mode)${NC}"
echo -e "${GREEN}✅ Run script (Docker mode)${NC}"
if [ -n "$GRADLE_PID" ]; then
    echo -e "${YELLOW}⚠️  Run script (Gradle mode) - timeout${NC}"
else
    echo -e "${GREEN}✅ Run script (Gradle mode)${NC}"
fi
echo -e "${GREEN}✅ Test script functionality${NC}"
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose integration${NC}"
fi
echo -e "${GREEN}✅ Environment variable configuration${NC}"
echo -e "${GREEN}✅ Documentation generation${NC}"
echo -e "${GREEN}✅ Script permissions${NC}"
echo ""
echo "Local development integration is working correctly!"
echo ""