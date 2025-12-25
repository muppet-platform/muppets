#!/bin/bash

# verify-java-micronaut-1766584181 Muppet - Test Script
# Runs all automated tests for the muppet

set -e

echo "🧪 Running tests for verify-java-micronaut-1766584181 muppet..."

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
./gradlew jacocoTestReport

echo ""
echo "✅ All tests passed!"
echo ""
echo "Test reports available at:"
echo "  - HTML: build/reports/tests/test/index.html"
echo "  - Coverage: build/reports/jacoco/test/html/index.html"
echo ""