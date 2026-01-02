#!/bin/bash

# {{muppet_name}} Muppet - Local Development Environment Setup

set -e

echo "🚀 Setting up local development environment for {{muppet_name}}..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Java 21 LTS
echo "☕ Checking Java installation..."
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -eq 21 ]; then
        echo "✅ Java 21 LTS found"
    else
        echo "❌ Java 21 LTS required, found Java $JAVA_VERSION"
        echo "Please install Amazon Corretto 21 LTS"
        exit 1
    fi
else
    echo "❌ Java not found"
    echo "Please install Amazon Corretto 21 LTS"
    exit 1
fi

# Check for Docker
echo "🐳 Checking Docker installation..."
if command_exists docker; then
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker found and running"
    else
        echo "❌ Docker daemon not running"
        echo "Please start Docker or Rancher Desktop"
        exit 1
    fi
else
    echo "❌ Docker not found"
    echo "Please install Rancher Desktop"
    exit 1
fi

# Test Gradle wrapper
echo "🏗️  Testing Gradle wrapper..."
if [ -f "./gradlew" ]; then
    chmod +x ./gradlew
    if ./gradlew --version >/dev/null 2>&1; then
        echo "✅ Gradle wrapper ready"
    else
        echo "❌ Gradle wrapper failed"
        exit 1
    fi
else
    echo "❌ Gradle wrapper script not found"
    exit 1
fi

# Create local environment file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating local environment file..."
    cat > .env.local << EOF
# Local development environment variables for {{muppet_name}}
MICRONAUT_ENVIRONMENTS=development
MUPPET_NAME={{muppet_name}}
SERVER_PORT=3000
LOG_LEVEL=DEBUG
EOF
    echo "✅ Created .env.local"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  make build    # Build the application"
echo "  make test     # Run tests"
echo "  make run      # Start the application"
echo ""