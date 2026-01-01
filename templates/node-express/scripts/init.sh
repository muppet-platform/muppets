#!/bin/bash

# Node.js Express initialization script for {{muppet_name}}
set -e

echo "🚀 Initializing {{muppet_name}} (Node.js Express) development environment..."

# Check Node.js version
echo "🔍 Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 20 LTS"
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "❌ Node.js 20 LTS or higher required, found Node.js $NODE_VERSION"
    echo "   Please install Node.js 20 LTS: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check npm version
echo "🔍 Checking npm version..."
NPM_VERSION=$(npm -v | cut -d'.' -f1)
if [ "$NPM_VERSION" -lt 10 ]; then
    echo "❌ npm 10 or higher required, found npm $(npm -v)"
    echo "   Please update npm: npm install -g npm@latest"
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p coverage

# Set up environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.local .env
    echo "⚠️  Please review and update .env file with your configuration"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh

# Run initial build to verify setup
echo "🏗️  Running initial build to verify setup..."
npm run build

# Run tests to verify everything works
echo "🧪 Running tests to verify setup..."
npm run test

echo ""
echo "✅ {{muppet_name}} development environment initialized successfully!"
echo ""
echo "🚀 Quick start commands:"
echo "   npm run dev          # Start development server with hot reload"
echo "   npm run build        # Build for production"
echo "   npm run test         # Run tests"
echo "   npm run lint         # Run linting"
echo "   ./scripts/run.sh     # Run with various options"
echo ""
echo "🌐 Development server: http://localhost:3000"
echo "🔍 Health check: http://localhost:3000/health"
echo "📚 API endpoints: http://localhost:3000/api/v1"
echo ""
echo "📖 For more information, see README.md"