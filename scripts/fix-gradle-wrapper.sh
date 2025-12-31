#!/bin/bash

# Fix missing Gradle wrapper JAR in muppet repositories
# This script adds the missing gradle-wrapper.jar file to repositories that are missing it

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ORG="muppet-platform"
TEMPLATE_JAR="templates/java-micronaut/gradle/wrapper/gradle-wrapper.jar"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if template JAR exists
if [[ ! -f "$TEMPLATE_JAR" ]]; then
    log_error "Template Gradle wrapper JAR not found: $TEMPLATE_JAR"
    exit 1
fi

# Get base64 encoded content of the JAR file
log_info "Encoding Gradle wrapper JAR..."
JAR_CONTENT=$(base64 -i "$TEMPLATE_JAR")

# Discover muppet repositories (exclude the main muppets repo)
log_info "Discovering muppet repositories in organization: $ORG"
REPOS=$(gh repo list "$ORG" --limit 1000 --json name | jq -r '.[].name' | grep -v '^muppets$')

if [[ -z "$REPOS" ]]; then
    log_warning "No muppet repositories found"
    exit 0
fi

echo ""
log_info "Found repositories:"
while IFS= read -r repo; do
    echo "  • $repo"
done <<< "$REPOS"
echo ""

# Function to check if gradle-wrapper.jar exists in a repository
check_gradle_wrapper() {
    local repo="$1"
    gh api "repos/$ORG/$repo/contents/gradle/wrapper/gradle-wrapper.jar" &>/dev/null
}

# Function to add gradle-wrapper.jar to a repository
add_gradle_wrapper() {
    local repo="$1"
    
    log_info "Adding Gradle wrapper JAR to $ORG/$repo"
    
    # Create the file using GitHub API
    local response
    response=$(gh api \
        --method PUT \
        "repos/$ORG/$repo/contents/gradle/wrapper/gradle-wrapper.jar" \
        --field message="fix: add missing Gradle wrapper JAR file

This file is required for Gradle builds to work properly in CI/CD.
The file was missing from the initial template generation." \
        --field content="$JAR_CONTENT" \
        --field encoding="base64" 2>&1)
    
    if [[ $? -eq 0 ]]; then
        log_success "Added Gradle wrapper JAR to $repo"
        return 0
    else
        log_error "Failed to add Gradle wrapper JAR to $repo: $response"
        return 1
    fi
}

# Process each repository
fixed_count=0
skipped_count=0
failed_count=0

while IFS= read -r repo; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Processing repository: $ORG/$repo"
    
    # Check if gradle-wrapper.jar already exists
    if check_gradle_wrapper "$repo"; then
        log_success "Gradle wrapper JAR already exists in $repo"
        ((skipped_count++))
    else
        log_warning "Gradle wrapper JAR missing in $repo"
        
        # Add the missing file
        if add_gradle_wrapper "$repo"; then
            ((fixed_count++))
        else
            ((failed_count++))
        fi
    fi
    echo ""
done <<< "$REPOS"

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "📊 Fix Summary:"
echo "├── Repositories processed: $(echo "$REPOS" | wc -l | tr -d ' ')"
echo "├── Fixed: $fixed_count"
echo "├── Already had JAR: $skipped_count"
echo "└── Failed: $failed_count"

if [[ $failed_count -eq 0 ]]; then
    log_success "All repositories are now fixed!"
else
    log_warning "Some repositories failed to be fixed. Check the logs above."
fi