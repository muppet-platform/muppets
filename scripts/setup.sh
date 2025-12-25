#!/bin/bash

# Muppet Platform - Development Environment Setup
# This script sets up the complete development environment for all components

set -e

echo "🔧 Setting up Muppet Platform development environment..."

# Check prerequisites
echo "1️⃣ Checking prerequisites..."

# Check UV
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ UV installed. Please restart your terminal and run this script again."
    exit 0
fi

# Check OpenTofu
if ! command -v tofu &> /dev/null; then
    echo "❌ OpenTofu not found. Please install from: https://opentofu.org/docs/intro/install/"
    echo "   macOS: brew install opentofu"
    echo "   Linux: curl -fsSL https://get.opentofu.org/install-opentofu.sh | sh"
    exit 1
fi

# Check Java 21
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -ne 21 ]; then
        echo "❌ Java 21 LTS required, found Java $JAVA_VERSION"
        echo "Please install Amazon Corretto 21 LTS:"
        echo "   macOS: brew install --cask corretto21"
        echo "   Linux: Download from https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/downloads-list.html"
        exit 1
    fi
    echo "✅ Java 21 LTS found"
else
    echo "❌ Java not found. Please install Amazon Corretto 21 LTS"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Some features may not work."
    echo "   Please install Docker Desktop or Docker Engine"
else
    echo "✅ Docker found"
fi

# Setup platform service
echo ""
echo "2️⃣ Setting up platform service..."
cd platform
echo "   Installing Python dependencies..."
uv sync
echo "   ✅ Platform service dependencies installed"
cd ..

# Setup templates
echo ""
echo "3️⃣ Setting up templates..."
cd templates/java-micronaut
echo "   Making template scripts executable..."
chmod +x scripts/*.sh
echo "   ✅ Template scripts configured"
cd ../..

# Setup infrastructure modules
echo ""
echo "4️⃣ Setting up infrastructure modules..."
echo "   Initializing OpenTofu modules..."
for module in terraform-modules/*/; do
    if [ -d "$module" ]; then
        echo "   Initializing $(basename "$module")..."
        cd "$module"
        tofu init -backend=false > /dev/null 2>&1 || echo "     ⚠️  Module initialization skipped (no backend)"
        cd - > /dev/null
    fi
done
echo "   ✅ Infrastructure modules initialized"

# Make project scripts executable
echo ""
echo "5️⃣ Setting up project scripts..."
chmod +x scripts/*.sh
echo "   ✅ Project scripts configured"

# Create local environment file if needed
if [ ! -f .env.local ]; then
    echo ""
    echo "6️⃣ Creating local environment configuration..."
    cat > .env.local << 'EOF'
# Muppet Platform Local Development Configuration
# Copy this file and customize for your environment

# Integration mode (mock or real)
INTEGRATION_MODE=mock

# Logging
LOG_LEVEL=INFO

# GitHub (for real mode)
# GITHUB_TOKEN=your_github_token_here
# GITHUB_ORG=your-github-org

# AWS (for real mode)  
# AWS_REGION=us-east-1
# AWS_PROFILE=your-aws-profile
EOF
    echo "   ✅ Created .env.local template"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and customize .env.local for your environment"
echo "  2. Run tests: ./scripts/test-all.sh"
echo "  3. Start platform: make platform-dev"
echo "  4. Read documentation: docs/README.md"
echo ""
echo "Available commands:"
echo "  ./scripts/test-all.sh      - Run all component tests"
echo "  ./scripts/test-platform.sh - Test platform service only"
echo "  ./scripts/test-templates.sh - Test templates only"
echo "  ./scripts/build-all.sh     - Build all components"
echo "  make platform-dev          - Start platform in development mode"