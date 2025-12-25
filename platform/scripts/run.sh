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
