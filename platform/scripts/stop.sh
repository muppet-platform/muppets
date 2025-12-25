#!/bin/bash

# Stop script for Muppet Platform local development

set -e

echo "Stopping Muppet Platform local development environment..."

# Stop services
docker-compose -f docker-compose.local.yml down

echo "Services stopped!"
