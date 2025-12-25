#!/bin/bash

# Build script for Muppet Platform

set -e

echo "Building Muppet Platform..."

# Build Docker image
docker build -t muppet-platform:local -f docker/Dockerfile .

echo "Build complete!"
