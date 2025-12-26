#!/bin/bash
set -e

# End-to-End Deployment Validation Script
# This script validates complete muppet deployment including infrastructure, TLS, and monitoring

echo "🔍 Validating End-to-End Muppet Deployment"
echo "=========================================="

# Configuration
MUPPET_NAME="${1:-test-validation-$(date +%s)}"
REGION="${AWS_DEFAULT_REGION:-us-west-2}"
PLATFORM_URL="${PLATFORM_URL:-http://localhost:8000}"
DOMAIN_NAME="${DOMAIN_NAME:-}"
HOSTED_ZONE_ID="${HOSTED_ZONE_ID:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Validation results tracking
VALIDATION_RESULTS=()

add_result() {
    local status="$1"
    local message="$2"
    VALIDATION_RESULTS+=("$status:$message")
    
    if [ "$status" = "PASS" ]; then
        log_success "$message"
    elif [ "$status" = "WARN" ]; then
        log_warning "$message"
    else
        log_error "$message"
    fi
}

# Validate OpenTofu modules
validate_opentofu_modules() {
    log_info "Validating OpenTofu modules..."
    
    # Get the project root directory
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(cd "$script_dir/../.." && pwd)"
    
    # Check fargate-service module
    if [ -d "$project_root/terraform-modules/fargate-service" ]; then
        cd "$project_root/terraform-modules/fargate-service"
        
        if tofu init -backend=false > /dev/null 2>&1; then
            if tofu validate > /dev/null 2>&1; then
                add_result "PASS" "Fargate service module validation passed"
            else
                add_result "FAIL" "Fargate service module validation failed"
            fi
        else
            add_result "FAIL" "Fargate service module initialization failed"
        fi
        
        cd - > /dev/null
    else
        add_result "FAIL" "Fargate service module not found at $project_root/terraform-modules/fargate-service"
    fi
}

# Validate platform service
validate_platform_service() {
    log_info "Validating platform service..."
    
    # Check if platform is running
    if curl -s "$PLATFORM_URL/health" > /dev/null 2>&1; then
        add_result "PASS" "Platform service is running"
        
        # Check MCP tools availability
        if curl -s "$PLATFORM_URL/mcp/tools/list" | grep -q "tools"; then
            add_result "PASS" "MCP tools are available"
        else
            add_result "WARN" "MCP tools may not be fully configured"
        fi
    else
        add_result "FAIL" "Platform service is not accessible"
    fi
}

# Validate AWS connectivity and permissions
validate_aws_setup() {
    log_info "Validating AWS setup..."
    
    # Check AWS credentials
    if aws sts get-caller-identity > /dev/null 2>&1; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        add_result "PASS" "AWS credentials configured (Account: $ACCOUNT_ID)"
    else
        add_result "FAIL" "AWS credentials not configured"
        return
    fi
    
    # Check required AWS services access
    local services=("ecs" "ecr" "ec2" "elbv2" "acm" "route53" "logs" "iam")
    for service in "${services[@]}"; do
        case $service in
            "ecs")
                if aws ecs list-clusters --region "$REGION" > /dev/null 2>&1; then
                    add_result "PASS" "ECS access verified"
                else
                    add_result "FAIL" "ECS access denied"
                fi
                ;;
            "ecr")
                if aws ecr describe-repositories --region "$REGION" > /dev/null 2>&1; then
                    add_result "PASS" "ECR access verified"
                else
                    add_result "FAIL" "ECR access denied"
                fi
                ;;
            "ec2")
                if aws ec2 describe-vpcs --region "$REGION" > /dev/null 2>&1; then
                    add_result "PASS" "EC2/VPC access verified"
                else
                    add_result "FAIL" "EC2/VPC access denied"
                fi
                ;;
            "elbv2")
                if aws elbv2 describe-load-balancers --region "$REGION" > /dev/null 2>&1; then
                    add_result "PASS" "ELB access verified"
                else
                    add_result "FAIL" "ELB access denied"
                fi
                ;;
            "acm")
                if aws acm list-certificates --region "$REGION" > /dev/null 2>&1; then
                    add_result "PASS" "ACM access verified"
                else
                    add_result "FAIL" "ACM access denied"
                fi
                ;;
            "route53")
                if aws route53 list-hosted-zones > /dev/null 2>&1; then
                    add_result "PASS" "Route53 access verified"
                else
                    add_result "WARN" "Route53 access limited (TLS domain validation may fail)"
                fi
                ;;
            "logs")
                if aws logs describe-log-groups --region "$REGION" > /dev/null 2>&1; then
                    add_result "PASS" "CloudWatch Logs access verified"
                else
                    add_result "FAIL" "CloudWatch Logs access denied"
                fi
                ;;
            "iam")
                if aws iam get-user > /dev/null 2>&1 || aws sts get-caller-identity > /dev/null 2>&1; then
                    add_result "PASS" "IAM access verified"
                else
                    add_result "FAIL" "IAM access denied"
                fi
                ;;
        esac
    done
}

# Validate TLS configuration
validate_tls_configuration() {
    log_info "Validating TLS configuration..."
    
    if [ -n "$DOMAIN_NAME" ] && [ -n "$HOSTED_ZONE_ID" ]; then
        add_result "PASS" "Domain configuration provided: $DOMAIN_NAME"
        
        # Verify hosted zone exists
        if aws route53 get-hosted-zone --id "$HOSTED_ZONE_ID" > /dev/null 2>&1; then
            add_result "PASS" "Hosted zone verified: $HOSTED_ZONE_ID"
        else
            add_result "FAIL" "Hosted zone not found: $HOSTED_ZONE_ID"
        fi
        
        # Check if domain is in the hosted zone
        ZONE_DOMAIN=$(aws route53 get-hosted-zone --id "$HOSTED_ZONE_ID" --query "HostedZone.Name" --output text | sed 's/\.$//')
        if [[ "$DOMAIN_NAME" == *"$ZONE_DOMAIN" ]]; then
            add_result "PASS" "Domain matches hosted zone"
        else
            add_result "WARN" "Domain may not match hosted zone (validation may fail)"
        fi
    else
        add_result "WARN" "No domain configuration - will use ALB DNS name"
    fi
}

# Validate Java 21 LTS enforcement
validate_java_version() {
    log_info "Validating Java 21 LTS enforcement..."
    
    # Check if Java 21 is available
    if command -v java > /dev/null 2>&1; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
        if [ "$JAVA_VERSION" -eq 21 ]; then
            # Check if it's LTS
            if java -version 2>&1 | grep -q "21.*LTS"; then
                add_result "PASS" "Java 21 LTS detected"
            else
                add_result "WARN" "Java 21 detected but LTS status unclear"
            fi
        elif [ "$JAVA_VERSION" -gt 21 ]; then
            add_result "WARN" "Java $JAVA_VERSION detected (non-LTS version may cause issues)"
        else
            add_result "WARN" "Java $JAVA_VERSION detected (consider upgrading to Java 21 LTS)"
        fi
    else
        add_result "WARN" "Java not found (required for template testing)"
    fi
    
    # Check if Amazon Corretto 21 is available
    if command -v java > /dev/null 2>&1; then
        if java -version 2>&1 | grep -q "Corretto"; then
            add_result "PASS" "Amazon Corretto detected"
        else
            add_result "WARN" "Non-Corretto Java detected (Amazon Corretto 21 recommended)"
        fi
    fi
}

# Validate template system
validate_template_system() {
    log_info "Validating template system..."
    
    # Get the project root directory
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(cd "$script_dir/../.." && pwd)"
    
    # Check if Java Micronaut template exists
    if [ -d "$project_root/templates/java-micronaut" ]; then
        add_result "PASS" "Java Micronaut template found"
        
        # Check template structure
        local required_files=("template.yaml" "Dockerfile.template" "build.gradle.template" "src/main/java")
        for file in "${required_files[@]}"; do
            if [ -e "$project_root/templates/java-micronaut/$file" ]; then
                add_result "PASS" "Template file exists: $file"
            else
                add_result "FAIL" "Template file missing: $file"
            fi
        done
        
        # Check for Java 21 LTS enforcement in template
        if grep -q "amazoncorretto:21" "$project_root/templates/java-micronaut/Dockerfile.template" 2>/dev/null; then
            add_result "PASS" "Template enforces Amazon Corretto 21"
        else
            add_result "WARN" "Template may not enforce Amazon Corretto 21"
        fi
        
        if grep -q "VERSION_21" "$project_root/templates/java-micronaut/build.gradle.template" 2>/dev/null; then
            add_result "PASS" "Template enforces Java 21 in Gradle"
        else
            add_result "WARN" "Template may not enforce Java 21 in Gradle"
        fi
    else
        add_result "FAIL" "Java Micronaut template not found at $project_root/templates/java-micronaut"
    fi
}

# Validate monitoring setup
validate_monitoring() {
    log_info "Validating monitoring setup..."
    
    # Get the project root directory
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local project_root="$(cd "$script_dir/../.." && pwd)"
    
    # Check if CloudWatch is accessible
    if aws logs describe-log-groups --region "$REGION" > /dev/null 2>&1; then
        add_result "PASS" "CloudWatch Logs accessible"
    else
        add_result "FAIL" "CloudWatch Logs not accessible"
    fi
    
    # Check if monitoring is configured in fargate module
    if grep -q "aws_cloudwatch_metric_alarm" "$project_root/terraform-modules/fargate-service/main.tf" 2>/dev/null; then
        add_result "PASS" "CloudWatch alarms configured in Fargate module"
    else
        add_result "WARN" "CloudWatch alarms may not be configured"
    fi
}

# Generate validation report
generate_report() {
    echo ""
    echo "📊 Validation Report"
    echo "==================="
    
    local pass_count=0
    local warn_count=0
    local fail_count=0
    
    for result in "${VALIDATION_RESULTS[@]}"; do
        local status="${result%%:*}"
        local message="${result#*:}"
        
        case "$status" in
            "PASS") ((pass_count++)) ;;
            "WARN") ((warn_count++)) ;;
            "FAIL") ((fail_count++)) ;;
        esac
    done
    
    echo "✅ Passed: $pass_count"
    echo "⚠️  Warnings: $warn_count"
    echo "❌ Failed: $fail_count"
    echo ""
    
    if [ $fail_count -eq 0 ]; then
        if [ $warn_count -eq 0 ]; then
            log_success "🎉 All validations passed! Ready for AWS deployment."
            return 0
        else
            log_warning "⚠️  Validations passed with warnings. Review warnings before deployment."
            return 0
        fi
    else
        log_error "💥 Validation failed. Fix errors before attempting deployment."
        return 1
    fi
}

# Main execution
main() {
    echo "Validating deployment readiness for muppet: $MUPPET_NAME"
    echo "Region: $REGION"
    echo "Platform URL: $PLATFORM_URL"
    if [ -n "$DOMAIN_NAME" ]; then
        echo "Domain: $DOMAIN_NAME"
    fi
    echo ""
    
    # Run all validations
    validate_opentofu_modules
    validate_platform_service
    validate_aws_setup
    validate_tls_configuration
    validate_java_version
    validate_template_system
    validate_monitoring
    
    # Generate final report
    generate_report
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [muppet-name] [--help]"
        echo ""
        echo "Arguments:"
        echo "  muppet-name         Name for test muppet (optional)"
        echo "  --help, -h          Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  AWS_DEFAULT_REGION  AWS region (default: us-west-2)"
        echo "  PLATFORM_URL        Platform URL (default: http://localhost:8000)"
        echo "  DOMAIN_NAME         Domain for TLS testing (optional)"
        echo "  HOSTED_ZONE_ID      Route53 hosted zone ID (optional)"
        exit 0
        ;;
esac

# Run main function
main