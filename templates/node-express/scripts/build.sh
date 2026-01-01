#!/bin/bash

# Node.js Express build script for {{muppet_name}}
set -e

echo "🔨 Building {{muppet_name}} (Node.js Express)..."

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "❌ Node.js 20 LTS or higher required, found Node.js $NODE_VERSION"
    echo "Please install Node.js 20 LTS: https://nodejs.org/"
    exit 1
fi

# Check npm version
NPM_VERSION=$(npm -v | cut -d'.' -f1)
if [ "$NPM_VERSION" -lt 10 ]; then
    echo "❌ npm 10 or higher required, found npm $(npm -v)"
    echo "Please update npm: npm install -g npm@latest"
    exit 1
fi

echo "✅ Node.js $(node -v) and npm $(npm -v) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Run linting
echo "🔍 Running ESLint..."
npm run lint

# Run type checking
echo "🔍 Running TypeScript compiler..."
npx tsc --noEmit

# Run tests
echo "🧪 Running tests..."
npm run test

# Build the application
echo "🏗️  Building TypeScript..."
npm run build

# Verify build output
if [ ! -f "dist/app.js" ]; then
    echo "❌ Build failed - dist/app.js not found"
    exit 1
fi

echo "✅ Build completed successfully!"
echo "📁 Build output: dist/"
echo "🚀 Ready to run: npm start"