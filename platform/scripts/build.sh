#!/bin/bash

# Build script for Muppet Platform

set -e

echo "Building Muppet Platform..."

# Build Docker image from the parent directory to include templates and terraform-modules
cd ..
docker build -t muppet-platform:local -f platform/docker/Dockerfile .

echo "Build complete!"
