#!/bin/bash

# Muppet Instantiation Verification Script
# Wrapper script for running the muppet verification system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

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

# Help function
show_help() {
    cat << EOF
Muppet Instantiation Verification Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    verify <template>     Verify a specific template
    verify-all           Verify all available templates
    list                 List available templates
    help                 Show this help message

OPTIONS:
    --verbose, -v        Enable verbose output
    --output, -o FILE    Save results to JSON file
    --no-cleanup         Don't cleanup verification workspace
    --custom-params JSON Custom parameters as JSON string

EXAMPLES:
    # Verify Java Micronaut template
    $0 verify java-micronaut

    # Verify all templates with verbose output
    $0 verify-all --verbose

    # Verify with custom parameters
    $0 verify java-micronaut --custom-params '{"environment": "test"}'

    # List available templates
    $0 list

    # Verify and save results
    $0 verify java-micronaut --output results.json

EOF
}

# Check if Python is available
check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not found"
        exit 1
    fi
}

# Check if we're in the right directory
check_directory() {
    if [ ! -f "${PLATFORM_DIR}/src/verification/cli.py" ]; then
        log_error "Verification CLI not found. Please run from platform directory."
        exit 1
    fi
}

# Set up Python path
setup_python_path() {
    export PYTHONPATH="${PLATFORM_DIR}:${PYTHONPATH}"
    cd "${PLATFORM_DIR}"
}

# Main function
main() {
    # Check prerequisites
    check_python
    check_directory
    setup_python_path
    
    # If no arguments, show help
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Handle help command
    if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    log_info "Starting Muppet Instantiation Verification System"
    log_info "Platform directory: ${PLATFORM_DIR}"
    
    # Run the Python CLI with all arguments using uv
    uv run python -m src.verification.cli "$@"
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Verification completed successfully"
    else
        log_error "Verification failed with exit code $exit_code"
    fi
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"