#!/bin/bash

# {{muppet_name}} Muppet - Test Script
# Runs all automated tests for the muppet

set -e

echo "🧪 Running tests for {{muppet_name}} muppet..."

# Load environment variables if available
if [ -f .env.local ]; then
    export $(grep -v '^#' .env.local | xargs)
fi

# Set test environment
export MICRONAUT_ENVIRONMENTS=test

# Run unit tests
echo "🔬 Running unit tests..."
./gradlew test

# Run integration tests if they exist
if [ -d "src/test/java" ] && find src/test/java -name "*IntegrationTest.java" | grep -q .; then
    echo "🔗 Running integration tests..."
    ./gradlew integrationTest
fi

# Generate test report
echo "📊 Generating test reports..."
if ./gradlew tasks --all | grep -q "jacocoTestReport"; then
    ./gradlew jacocoTestReport
    JACOCO_AVAILABLE=true
else
    echo "⚠️  JaCoCo plugin not available, skipping coverage report"
    JACOCO_AVAILABLE=false
fi

echo ""
echo "✅ All tests passed!"
echo ""
echo "Test reports available at:"
echo "  - HTML: build/reports/tests/test/index.html"
if [ "$JACOCO_AVAILABLE" = true ]; then
    echo "  - Coverage: build/reports/jacoco/test/html/index.html"
fi
echo ""