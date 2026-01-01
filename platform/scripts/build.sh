#!/bin/bash

# Build script for Muppet Platform

set -e

echo "Building Muppet Platform..."

# Build Docker image from parent directory to access templates and terraform-modules
cd ..
docker build -t muppet-platform:local -f platform/docker/Dockerfile .
cd platform

echo "Build complete!"
