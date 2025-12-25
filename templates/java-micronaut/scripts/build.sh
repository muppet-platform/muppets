#!/bin/bash

# {{muppet_name}} Muppet - Build Script
# Compiles the application and creates container images

set -e

echo "🏗️  Building {{muppet_name}} muppet..."

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
docker build -t {{muppet_name}}:latest .

# Tag with development tag
docker tag {{muppet_name}}:latest {{muppet_name}}:dev

echo ""
echo "✅ Build complete!"
echo "   JAR: build/libs/{{muppet_name}}-*-all.jar"
echo "   Docker image: {{muppet_name}}:latest"
echo ""
echo "Next steps:"
echo "  - Run './scripts/test.sh' to run tests"
echo "  - Run './scripts/run.sh' to start the application"
echo ""