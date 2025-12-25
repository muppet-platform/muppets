#!/bin/bash

# Health check script for Muppet Platform local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "Checking Muppet Platform local environment health..."

# Check if services are running
print_status "Checking Docker containers..."
if docker-compose -f docker-compose.local.yml ps | grep -q "Up"; then
    print_success "Docker containers are running"
else
    print_error "Docker containers are not running"
    exit 1
fi

# Check Platform API health
print_status "Checking Platform API health..."
if curl -f -s http://localhost:8000/health/ > /dev/null; then
    print_success "Platform API is healthy"
else
    print_error "Platform API is not responding"
    exit 1
fi

# Check Platform API readiness
print_status "Checking Platform API readiness..."
if curl -f -s http://localhost:8000/health/ready > /dev/null; then
    print_success "Platform API is ready"
else
    print_error "Platform API is not ready"
    exit 1
fi

# Check LocalStack health
print_status "Checking LocalStack health..."
if curl -f -s http://localhost:4566/_localstack/health > /dev/null; then
    print_success "LocalStack is healthy"
else
    print_error "LocalStack is not responding"
    exit 1
fi

# Check API documentation
print_status "Checking API documentation..."
if curl -f -s http://localhost:8000/docs > /dev/null; then
    print_success "API documentation is accessible"
else
    print_error "API documentation is not accessible"
    exit 1
fi

print_success "All health checks passed!"
print_status ""
print_status "Services are running at:"
print_status "  Platform API: http://localhost:8000"
print_status "  API Documentation: http://localhost:8000/docs"
print_status "  LocalStack: http://localhost:4566"
print_status ""
print_status "To view logs: docker-compose -f docker-compose.local.yml logs -f"
print_status "To stop services: docker-compose -f docker-compose.local.yml down"