#!/bin/bash

# Muppet Platform - Master Test Script
# Runs all component tests in the correct order

set -e

echo "🚀 Running all component tests for Muppet Platform..."
echo ""

# Track test results using simple arrays
test_names=()
test_results=()
total_tests=0
passed_tests=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_script="$2"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🧪 $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    total_tests=$((total_tests + 1))
    test_names+=("$test_name")
    
    if $test_script; then
        test_results+=("✅ PASSED")
        passed_tests=$((passed_tests + 1))
        echo ""
        echo "✅ $test_name completed successfully"
    else
        test_results+=("❌ FAILED")
        echo ""
        echo "❌ $test_name failed"
        return 1
    fi
    
    echo ""
}

# Test each component
run_test "Platform Service Component" "./scripts/test-platform.sh"
run_test "Templates Component" "./scripts/test-templates.sh"
run_test "Infrastructure Component" "./scripts/test-infrastructure.sh"

# Test steering documentation (basic check)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Steering Documentation Component"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total_tests=$((total_tests + 1))
test_names+=("Steering Documentation")

if [ -d "steering-docs" ] && [ -f "steering-docs/README.md" ]; then
    echo "✅ Steering documentation structure is valid"
    test_results+=("✅ PASSED")
    passed_tests=$((passed_tests + 1))
else
    echo "❌ Steering documentation structure is invalid"
    test_results+=("❌ FAILED")
fi

echo ""

# Print final results
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TEST RESULTS SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for i in "${!test_names[@]}"; do
    echo "${test_results[$i]} ${test_names[$i]}"
done

echo ""
echo "📈 Overall Results: $passed_tests/$total_tests tests passed"

if [ $passed_tests -eq $total_tests ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED! 🎉"
    echo ""
    echo "✅ Platform Service: Ready for development"
    echo "✅ Templates: Ready for muppet generation"
    echo "✅ Infrastructure: Ready for deployment"
    echo "✅ Documentation: Complete and accessible"
    echo ""
    echo "🚀 The Muppet Platform is ready for use!"
    echo ""
    echo "Next steps:"
    echo "  1. Start platform: make platform-dev"
    echo "  2. Create a muppet: Use the platform API or MCP tools"
    echo "  3. Deploy infrastructure: Follow deployment guides"
    echo "  4. Read documentation: docs/README.md"
    
    exit 0
else
    failed_tests=$((total_tests - passed_tests))
    echo ""
    echo "❌ $failed_tests/$total_tests tests failed"
    echo ""
    echo "Please fix the failing tests before proceeding."
    echo "Check the output above for specific error details."
    
    exit 1
fi