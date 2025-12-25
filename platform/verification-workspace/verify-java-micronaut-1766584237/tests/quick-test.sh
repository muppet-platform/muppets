#!/bin/bash

# Quick Java Micronaut Template Test
# Fast validation of template functionality

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Test configuration
TEST_NAME="quicktest$(date +%s)"
TEST_DIR="/tmp/${TEST_NAME}"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Cleanup
cleanup() {
    [ -d "${TEST_DIR}" ] && rm -rf "${TEST_DIR}"
}
trap cleanup EXIT

main() {
    log_info "Quick template test starting..."
    
    # Setup Java 21 LTS if needed
    if command -v java >/dev/null 2>&1; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
        if [ "$JAVA_VERSION" -ne 21 ] && [ -d "/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home" ]; then
            export JAVA_HOME="/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home"
            export PATH="$JAVA_HOME/bin:$PATH"
        fi
    fi
    
    # Generate template
    mkdir -p "${TEST_DIR}"
    cd "${TEST_DIR}"
    cp -r "${TEMPLATE_DIR}"/* .
    rm -rf tests/
    
    # Substitute variables
    find . -name "*.template" | while read -r file; do
        sed "s/verify-java-micronaut-1766584237/${TEST_NAME}/g" "$file" > "${file%.template}"
        rm "$file"
    done
    find . -type f \( -name "*.java" -o -name "*.yml" -o -name "Dockerfile" \) -exec sed -i.bak "s/verify-java-micronaut-1766584237/${TEST_NAME}/g" {} \;
    find . -name "*.bak" -delete
    
    log_success "Template generated"
    
    # Test build
    chmod +x gradlew
    ./gradlew clean build --no-daemon -q
    
    log_success "Build completed"
    
    # Verify JAR
    if [ -f "build/libs/${TEST_NAME}-1.0.0-all.jar" ]; then
        log_success "JAR created successfully"
    else
        log_error "JAR not found"
        exit 1
    fi
    
    log_success "Quick test passed!"
}

main "$@"