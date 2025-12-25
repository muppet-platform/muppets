#!/bin/bash

# Java Micronaut Template Build Test
# Tests template generation and build without Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_MUPPET_NAME="testbuild$(date +%s)"
TEST_DIR="/tmp/${TEST_MUPPET_NAME}"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up test resources...${NC}"
    
    # Remove test directory
    if [ -d "${TEST_DIR}" ]; then
        rm -rf "${TEST_DIR}"
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test functions
test_java_version() {
    log_info "Testing Java version compatibility..."
    
    # Check if Java 21 LTS is available
    if ! command -v java >/dev/null 2>&1; then
        log_error "Java not found. Please install Java 21 LTS."
        return 1
    fi
    
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -ne 21 ]; then
        log_warning "Java $JAVA_VERSION detected. Java 21 LTS is recommended."
        log_info "Setting JAVA_HOME to use Java 21 LTS if available..."
        
        # Try to find Java 21 LTS
        if [ -d "/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home" ]; then
            export JAVA_HOME="/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home"
            export PATH="$JAVA_HOME/bin:$PATH"
            log_success "Using Java 21 LTS from $JAVA_HOME"
        else
            log_error "Java 21 LTS not found. Please install Amazon Corretto 21."
            return 1
        fi
    else
        log_success "Java 21 LTS detected"
    fi
}

test_template_generation() {
    log_info "Testing template generation..."
    
    # Create test directory
    mkdir -p "${TEST_DIR}"
    cd "${TEST_DIR}"
    
    # Copy template files and substitute variables
    cp -r "${TEMPLATE_DIR}"/* .
    
    # Remove test directory to avoid recursion
    rm -rf tests/
    
    # Substitute template variables
    find . -type f -name "*.template" | while read -r file; do
        new_file="${file%.template}"
        sed "s/verify-java-micronaut-1766584237/${TEST_MUPPET_NAME}/g" "$file" > "$new_file"
        rm "$file"
    done
    
    # Substitute in other files
    find . -type f \( -name "*.java" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" -o -name "Dockerfile" \) -exec sed -i.bak "s/verify-java-micronaut-1766584237/${TEST_MUPPET_NAME}/g" {} \;
    find . -name "*.bak" -delete
    
    log_success "Template generated successfully"
}

test_gradle_build() {
    log_info "Testing Gradle build..."
    
    cd "${TEST_DIR}"
    
    # Make gradlew executable
    chmod +x gradlew
    
    # Test Gradle version
    ./gradlew --version
    
    # Clean and build
    ./gradlew clean build --no-daemon
    
    # Verify JAR was created
    if [ ! -f "build/libs/${TEST_MUPPET_NAME}-1.0.0-all.jar" ]; then
        log_error "Shadow JAR not found"
        return 1
    fi
    
    log_success "Gradle build completed successfully"
}

test_unit_tests() {
    log_info "Testing unit tests..."
    
    cd "${TEST_DIR}"
    
    # Run tests
    ./gradlew test --no-daemon
    
    # Check test results
    if ls build/test-results/test/TEST-*.xml 1> /dev/null 2>&1; then
        log_success "Unit tests passed"
    else
        log_error "Test results not found"
        return 1
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}🧪 Starting Java Micronaut Template Build Test${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    # Run tests in sequence
    test_java_version
    test_template_generation
    test_gradle_build
    test_unit_tests
    
    echo -e "${GREEN}🎉 All build tests passed successfully!${NC}"
    echo -e "${GREEN}Template build process is working correctly.${NC}"
}

# Run main function
main "$@"