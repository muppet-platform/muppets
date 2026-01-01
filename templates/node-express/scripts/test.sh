#!/bin/bash

# Node.js Express test script for {{muppet_name}}
set -e

echo "🧪 Running tests for {{muppet_name}} (Node.js Express)..."

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies first..."
    npm ci
fi

# Run linting first
echo "🔍 Running ESLint..."
npm run lint

# Run type checking
echo "🔍 Running TypeScript compiler check..."
npx tsc --noEmit

# Run tests with coverage
echo "🧪 Running Jest tests with coverage..."
npm run test:coverage

# Check coverage thresholds
echo "📊 Checking coverage thresholds..."
if [ -f "coverage/lcov-report/index.html" ]; then
    echo "📈 Coverage report generated: coverage/lcov-report/index.html"
fi

# Run format check
echo "💅 Checking code formatting..."
npm run format:check

echo "✅ All tests passed!"
echo ""
echo "📊 Coverage Summary:"
echo "   - Branches: 70%+ required"
echo "   - Functions: 70%+ required" 
echo "   - Lines: 70%+ required"
echo "   - Statements: 70%+ required"
echo ""
echo "📁 Coverage report: coverage/lcov-report/index.html"