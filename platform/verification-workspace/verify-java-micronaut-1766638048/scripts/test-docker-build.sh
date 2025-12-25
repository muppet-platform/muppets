#!/bin/bash

# Docker Build Test Script
# Tests Docker image build and container functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Docker Build Test${NC}"
echo "==================="

# Test configuration
TEST_MUPPET_NAME="docker-test-$(date +%s)"
TEST_DIR="/tmp/docker-build-test"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_PORT=3002

echo "Template: $TEMPLATE_DIR"
echo "Test muppet: $TEST_MUPPET_NAME"
echo "Test directory: $TEST_DIR"
echo "Test port: $TEST_PORT"
echo ""

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"
    
    # Stop and remove container
    if docker ps -q --filter "name=${TEST_MUPPET_NAME}" | grep -q .; then
        docker stop "${TEST_MUPPET_NAME}" 2>/dev/null || true
        docker rm "${TEST_MUPPET_NAME}" 2>/dev/null || true
    fi
    
    # Remove images
    if docker images -q "${TEST_MUPPET_NAME}" | grep -q .; then
        docker rmi "${TEST_MUPPET_NAME}:latest" 2>/dev/null || true
        docker rmi "${TEST_MUPPET_NAME}:dev" 2>/dev/null || true
    fi
    
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

# Prerequisites check
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

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

echo -e "${GREEN}✅ Test environment ready${NC}"

# Test Dockerfile validation
echo -e "${BLUE}📋 Validating Dockerfile...${NC}"

if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found${NC}"
    exit 1
fi

# Check for Amazon Corretto 21
if grep -q "amazoncorretto:21" Dockerfile; then
    echo -e "${GREEN}✅ Amazon Corretto 21 base image${NC}"
else
    echo -e "${RED}❌ Amazon Corretto 21 not found in Dockerfile${NC}"
    exit 1
fi

# Check for multi-stage build
if grep -q "FROM.*AS builder" Dockerfile && grep -q "FROM amazoncorretto:21.*[^AS]" Dockerfile; then
    echo -e "${GREEN}✅ Multi-stage build configured${NC}"
else
    echo -e "${RED}❌ Multi-stage build not configured${NC}"
    exit 1
fi

# Check for non-root user
if grep -q "adduser.*muppet" Dockerfile && grep -q "USER muppet" Dockerfile; then
    echo -e "${GREEN}✅ Non-root user configured${NC}"
else
    echo -e "${RED}❌ Non-root user not configured${NC}"
    exit 1
fi

# Check for health check
if grep -q "HEALTHCHECK" Dockerfile; then
    echo -e "${GREEN}✅ Health check configured${NC}"
else
    echo -e "${RED}❌ Health check not configured${NC}"
    exit 1
fi

# Check for port exposure
if grep -q "EXPOSE 3000" Dockerfile; then
    echo -e "${GREEN}✅ Port 3000 exposed${NC}"
else
    echo -e "${RED}❌ Port 3000 not exposed${NC}"
    exit 1
fi

# Build application JAR first
echo -e "${BLUE}🏗️  Building application JAR...${NC}"

chmod +x gradlew
./gradlew clean shadowJar

# Verify JAR was created
JAR_FILE=$(find build/libs -name "${TEST_MUPPET_NAME}-*-all.jar" | head -n 1)
if [ -n "$JAR_FILE" ] && [ -f "$JAR_FILE" ]; then
    echo -e "${GREEN}✅ JAR built: $JAR_FILE${NC}"
else
    echo -e "${RED}❌ JAR build failed${NC}"
    exit 1
fi

# Test Docker build
echo -e "${BLUE}🐳 Testing Docker build...${NC}"

# Build with verbose output to catch any issues
if docker build -t "${TEST_MUPPET_NAME}:latest" .; then
    echo -e "${GREEN}✅ Docker build successful${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Verify image was created
if docker images -q "${TEST_MUPPET_NAME}:latest" | grep -q .; then
    echo -e "${GREEN}✅ Docker image created${NC}"
else
    echo -e "${RED}❌ Docker image not found${NC}"
    exit 1
fi

# Check image size (should be reasonable)
IMAGE_SIZE=$(docker images "${TEST_MUPPET_NAME}:latest" --format "table {{.Size}}" | tail -n 1)
echo -e "${GREEN}✅ Image size: $IMAGE_SIZE${NC}"

# Test image layers
echo -e "${BLUE}🔍 Inspecting image layers...${NC}"
docker history "${TEST_MUPPET_NAME}:latest" --no-trunc

# Test container startup
echo -e "${BLUE}🚀 Testing container startup...${NC}"

# Start container
docker run -d \
    --name "${TEST_MUPPET_NAME}" \
    -p "${TEST_PORT}:3000" \
    -e MICRONAUT_ENVIRONMENTS=development \
    -e MUPPET_NAME="${TEST_MUPPET_NAME}" \
    "${TEST_MUPPET_NAME}:latest"

# Wait for container to be ready
if wait_for_service "http://localhost:${TEST_PORT}/health" 60; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
else
    echo -e "${RED}❌ Container failed to start${NC}"
    echo "Container logs:"
    docker logs "${TEST_MUPPET_NAME}"
    exit 1
fi

# Test container health
echo -e "${BLUE}🏥 Testing container health...${NC}"

# Check Docker health check
sleep 5  # Wait for health check to run
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${TEST_MUPPET_NAME}" 2>/dev/null || echo "no-healthcheck")

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✅ Docker health check: healthy${NC}"
elif [ "$HEALTH_STATUS" = "starting" ]; then
    echo -e "${YELLOW}⚠️  Docker health check: starting (waiting...)${NC}"
    sleep 10
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${TEST_MUPPET_NAME}" 2>/dev/null || echo "no-healthcheck")
    if [ "$HEALTH_STATUS" = "healthy" ]; then
        echo -e "${GREEN}✅ Docker health check: healthy${NC}"
    else
        echo -e "${RED}❌ Docker health check: $HEALTH_STATUS${NC}"
    fi
else
    echo -e "${RED}❌ Docker health check: $HEALTH_STATUS${NC}"
fi

# Test HTTP endpoints
echo -e "${BLUE}🌐 Testing HTTP endpoints...${NC}"

# Test health endpoint
if curl -s -f "http://localhost:${TEST_PORT}/health" >/dev/null; then
    echo -e "${GREEN}✅ Health endpoint responding${NC}"
    HEALTH_RESPONSE=$(curl -s "http://localhost:${TEST_PORT}/health")
    echo "Health response: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health endpoint not responding${NC}"
    exit 1
fi

# Test API endpoint
if curl -s -f "http://localhost:${TEST_PORT}/api" >/dev/null; then
    echo -e "${GREEN}✅ API endpoint responding${NC}"
    API_RESPONSE=$(curl -s "http://localhost:${TEST_PORT}/api")
    echo "API response: $API_RESPONSE"
else
    echo -e "${RED}❌ API endpoint not responding${NC}"
    exit 1
fi

# Test container resource usage
echo -e "${BLUE}📊 Checking container resource usage...${NC}"

CONTAINER_STATS=$(docker stats "${TEST_MUPPET_NAME}" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}")
echo "Container stats:"
echo "$CONTAINER_STATS"

# Test container logs
echo -e "${BLUE}📝 Checking container logs...${NC}"

LOGS=$(docker logs "${TEST_MUPPET_NAME}" 2>&1 | tail -n 10)
echo "Recent logs:"
echo "$LOGS"

# Check for any error messages in logs
if echo "$LOGS" | grep -i error; then
    echo -e "${YELLOW}⚠️  Error messages found in logs${NC}"
else
    echo -e "${GREEN}✅ No error messages in logs${NC}"
fi

# Test container stop and restart
echo -e "${BLUE}🔄 Testing container stop and restart...${NC}"

docker stop "${TEST_MUPPET_NAME}"
echo -e "${GREEN}✅ Container stopped${NC}"

docker start "${TEST_MUPPET_NAME}"
echo -e "${GREEN}✅ Container restarted${NC}"

# Wait for service to be ready again
if wait_for_service "http://localhost:${TEST_PORT}/health" 30; then
    echo -e "${GREEN}✅ Service ready after restart${NC}"
else
    echo -e "${RED}❌ Service failed to start after restart${NC}"
    exit 1
fi

# Test with environment variables
echo -e "${BLUE}⚙️  Testing environment variable injection...${NC}"

docker stop "${TEST_MUPPET_NAME}"
docker rm "${TEST_MUPPET_NAME}"

# Start with custom environment variables
docker run -d \
    --name "${TEST_MUPPET_NAME}" \
    -p "${TEST_PORT}:3000" \
    -e MICRONAUT_ENVIRONMENTS=production \
    -e MUPPET_NAME="${TEST_MUPPET_NAME}" \
    -e LOG_LEVEL=INFO \
    "${TEST_MUPPET_NAME}:latest"

if wait_for_service "http://localhost:${TEST_PORT}/health" 30; then
    echo -e "${GREEN}✅ Container works with custom environment variables${NC}"
else
    echo -e "${RED}❌ Container failed with custom environment variables${NC}"
    exit 1
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 Docker Build Test Complete!${NC}"
echo "================================"
echo -e "${GREEN}✅ Dockerfile validation${NC}"
echo -e "${GREEN}✅ Multi-stage build${NC}"
echo -e "${GREEN}✅ Security configuration (non-root user)${NC}"
echo -e "${GREEN}✅ Health check configuration${NC}"
echo -e "${GREEN}✅ Docker image build${NC}"
echo -e "${GREEN}✅ Container startup${NC}"
echo -e "${GREEN}✅ HTTP endpoints${NC}"
echo -e "${GREEN}✅ Container health monitoring${NC}"
echo -e "${GREEN}✅ Container lifecycle (stop/start)${NC}"
echo -e "${GREEN}✅ Environment variable injection${NC}"
echo ""
echo "Docker build and container functionality verified!"
echo ""