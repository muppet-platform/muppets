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

# Format code first to avoid Spotless issues
echo "✨ Formatting code..."
./gradlew spotlessApply

# Compile and build shadow JAR (fat JAR with all dependencies)
echo "📦 Building shadow JAR..."
./gradlew shadowJar --no-daemon

# Find the shadow JAR and copy to predictable name for Docker
echo "📋 Preparing JAR for Docker..."
SHADOW_JAR=$(find build/libs -name "*-all.jar" | head -n 1)

if [ -z "$SHADOW_JAR" ]; then
    echo "❌ Shadow JAR not found. Expected *-all.jar in build/libs/"
    echo "Available files:"
    ls -la build/libs/ || echo "No build/libs directory found"
    exit 1
fi

echo "✅ Found shadow JAR: $SHADOW_JAR"
cp "$SHADOW_JAR" build/libs/app.jar

# Verify the JAR file exists and is valid
echo "🔍 Verifying JAR..."
if [ ! -f "$SHADOW_JAR" ]; then
    echo "❌ Shadow JAR not found: $SHADOW_JAR"
    exit 1
fi

# Quick JAR validation without starting the application
if ! jar tf "$SHADOW_JAR" | grep -q "META-INF/MANIFEST.MF"; then
    echo "❌ JAR appears to be corrupted (no manifest found)"
    exit 1
fi

# Check if main class is in the JAR
if ! jar tf "$SHADOW_JAR" | grep -q "com/muppetplatform/.*/Application.class"; then
    echo "❌ Main Application class not found in JAR"
    exit 1
fi

echo "✅ JAR verification passed"

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t {{muppet_name}}:latest .

# Tag with development tag
docker tag {{muppet_name}}:latest {{muppet_name}}:dev

echo ""
echo "✅ Build complete!"
echo "   Shadow JAR: $SHADOW_JAR"
echo "   Docker JAR: build/libs/app.jar"
echo "   Docker image: {{muppet_name}}:latest"
echo ""
echo "Next steps:"
echo "  - Run './scripts/test.sh' to run tests"
echo "  - Run 'make run' to start on Rancher Desktop"
echo ""