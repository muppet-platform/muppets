#!/bin/bash

# verify-java-micronaut-1766584237 Muppet - Build Script
# Compiles the application and creates container images

set -e

echo "🏗️  Building verify-java-micronaut-1766584237 muppet..."

# Load environment variables if available
if [ -f .env.local ]; then
    export $(grep -v '^#' .env.local | xargs)
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
./gradlew clean

# Compile and build JAR
echo "📦 Building application JAR..."
./gradlew shadowJar

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t verify-java-micronaut-1766584237:latest .

# Tag with development tag
docker tag verify-java-micronaut-1766584237:latest verify-java-micronaut-1766584237:dev

echo ""
echo "✅ Build complete!"
echo "   JAR: build/libs/verify-java-micronaut-1766584237-*-all.jar"
echo "   Docker image: verify-java-micronaut-1766584237:latest"
echo ""
echo "Next steps:"
echo "  - Run './scripts/test.sh' to run tests"
echo "  - Run './scripts/run.sh' to start the application"
echo ""