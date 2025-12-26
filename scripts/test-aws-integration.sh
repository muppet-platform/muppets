#!/bin/bash
set -e

# Test AWS Integration Script
# This script tests the muppet platform with real AWS services

echo "🚀 Testing Muppet Platform AWS Integration"
echo "=========================================="

# Configuration
MUPPET_NAME="test-aws-$(date +%s)"
TEMPLATE="java-micronaut"
REGION="${AWS_DEFAULT_REGION:-us-west-2}"
PLATFORM_URL="${PLATFORM_URL:-http://localhost:8000}"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install AWS CLI v2."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' or set environment variables."
        exit 1
    fi
    
    # Check OpenTofu
    if ! command -v tofu &> /dev/null; then
        log_error "OpenTofu not found. Please install OpenTofu."
        exit 1
    fi
    
    # Check platform is running
    if ! curl -s "$PLATFORM_URL/health" &> /dev/null; then
        log_error "Platform not running at $PLATFORM_URL. Start the platform first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Test AWS connectivity
test_aws_connectivity() {
    log_info "Testing AWS connectivity..."
    
    # Get caller identity
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    
    log_success "Connected to AWS Account: $ACCOUNT_ID"
    log_success "User/Role: $USER_ARN"
    log_success "Region: $REGION"
}

# Create ECR repository if needed
setup_ecr() {
    log_info "Setting up ECR repository..."
    
    REPO_NAME="muppet-platform/$MUPPET_NAME"
    
    # Check if repository exists
    if aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" &> /dev/null; then
        log_warning "ECR repository $REPO_NAME already exists"
    else
        # Create repository
        aws ecr create-repository --repository-name "$REPO_NAME" --region "$REGION" > /dev/null
        log_success "Created ECR repository: $REPO_NAME"
    fi
    
    # Get repository URI
    REPO_URI=$(aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" --query 'repositories[0].repositoryUri' --output text)
    log_success "ECR Repository URI: $REPO_URI"
}

# Create test muppet
create_muppet() {
    log_info "Creating test muppet: $MUPPET_NAME"
    
    # Create muppet via API
    RESPONSE=$(curl -s -X POST "$PLATFORM_URL/api/v1/muppets" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$MUPPET_NAME\",
            \"template\": \"$TEMPLATE\",
            \"parameters\": {
                \"description\": \"AWS integration test muppet\",
                \"aws_region\": \"$REGION\"
            }
        }")
    
    if echo "$RESPONSE" | grep -q "success"; then
        log_success "Created muppet: $MUPPET_NAME"
    else
        log_error "Failed to create muppet: $RESPONSE"
        exit 1
    fi
}

# Build and push container image
build_and_push_image() {
    log_info "Building and pushing container image..."
    
    # Get ECR login token
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    
    # Build image (assuming muppet was created in workspace)
    MUPPET_DIR="$HOME/muppet-workspace/$MUPPET_NAME"
    if [ -d "$MUPPET_DIR" ]; then
        cd "$MUPPET_DIR"
        
        # Build with Java 21 LTS
        docker build -t "$MUPPET_NAME:latest" .
        
        # Tag for ECR
        docker tag "$MUPPET_NAME:latest" "$REPO_URI:latest"
        
        # Push to ECR
        docker push "$REPO_URI:latest"
        
        log_success "Built and pushed image: $REPO_URI:latest"
    else
        log_warning "Muppet directory not found, using placeholder image"
        # For testing, we'll use a simple nginx image
        docker pull nginx:alpine
        docker tag nginx:alpine "$REPO_URI:latest"
        docker push "$REPO_URI:latest"
        log_success "Pushed placeholder image: $REPO_URI:latest"
    fi
}

# Deploy muppet to AWS
deploy_muppet() {
    log_info "Deploying muppet to AWS Fargate..."
    
    # Deploy via API
    RESPONSE=$(curl -s -X POST "$PLATFORM_URL/api/v1/muppets/$MUPPET_NAME/deploy" \
        -H "Content-Type: application/json" \
        -d "{
            \"container_image\": \"$REPO_URI:latest\",
            \"environment_variables\": {
                \"ENVIRONMENT\": \"test\",
                \"AWS_REGION\": \"$REGION\"
            }
        }")
    
    if echo "$RESPONSE" | grep -q "success"; then
        log_success "Started deployment for: $MUPPET_NAME"
    else
        log_error "Failed to deploy muppet: $RESPONSE"
        exit 1
    fi
}

# Monitor deployment
monitor_deployment() {
    log_info "Monitoring deployment progress..."
    
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        RESPONSE=$(curl -s "$PLATFORM_URL/api/v1/muppets/$MUPPET_NAME/deployment-status")
        STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        
        case "$STATUS" in
            "completed")
                log_success "Deployment completed successfully!"
                
                # Get service URL
                SERVICE_URL=$(echo "$RESPONSE" | grep -o '"service_url":"[^"]*"' | cut -d'"' -f4)
                if [ -n "$SERVICE_URL" ]; then
                    log_success "Service URL: $SERVICE_URL"
                    
                    # Test health endpoint
                    if curl -s "$SERVICE_URL/health" &> /dev/null; then
                        log_success "Health check passed!"
                    else
                        log_warning "Health check failed (service may still be starting)"
                    fi
                fi
                return 0
                ;;
            "failed")
                log_error "Deployment failed!"
                echo "$RESPONSE"
                return 1
                ;;
            "pending"|"in_progress")
                log_info "Deployment in progress... (attempt $((ATTEMPT + 1))/$MAX_ATTEMPTS)"
                ;;
            *)
                log_warning "Unknown deployment status: $STATUS"
                ;;
        esac
        
        sleep 30
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    log_error "Deployment monitoring timed out"
    return 1
}

# Test TLS certificate provisioning
test_tls_certificate() {
    log_info "Testing TLS certificate provisioning..."
    
    if [ -n "$DOMAIN_NAME" ] && [ -n "$HOSTED_ZONE_ID" ]; then
        log_info "Domain configuration found: $DOMAIN_NAME"
        
        # Check if certificate exists
        CERT_ARN=$(aws acm list-certificates --region "$REGION" --query "CertificateSummaryList[?DomainName=='$DOMAIN_NAME'].CertificateArn" --output text)
        
        if [ -n "$CERT_ARN" ] && [ "$CERT_ARN" != "None" ]; then
            log_success "✅ Certificate found: $CERT_ARN"
            
            # Check certificate status
            CERT_STATUS=$(aws acm describe-certificate --certificate-arn "$CERT_ARN" --region "$REGION" --query "Certificate.Status" --output text)
            log_info "Certificate status: $CERT_STATUS"
            
            if [ "$CERT_STATUS" = "ISSUED" ]; then
                log_success "✅ Certificate is issued and ready"
            else
                log_warning "⚠️  Certificate status: $CERT_STATUS (may still be validating)"
            fi
        else
            log_info "No existing certificate found - will be created during deployment"
        fi
    else
        log_info "No domain configuration - using ALB DNS name for testing"
    fi
}

# Test service functionality
test_service() {
    log_info "Testing deployed service..."
    
    # Get service details
    RESPONSE=$(curl -s "$PLATFORM_URL/api/v1/muppets/$MUPPET_NAME")
    SERVICE_URL=$(echo "$RESPONSE" | grep -o '"service_url":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$SERVICE_URL" ]; then
        log_info "Testing service at: $SERVICE_URL"
        
        # Test health endpoint
        if curl -s -f "$SERVICE_URL/health" > /dev/null; then
            log_success "✅ Health endpoint working"
        else
            log_warning "⚠️  Health endpoint not responding"
        fi
        
        # Test HTTPS endpoint if enabled
        HTTPS_URL=$(echo "$RESPONSE" | grep -o '"service_https_url":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$HTTPS_URL" ]; then
            log_info "Testing HTTPS endpoint: $HTTPS_URL"
            
            # Test HTTPS connectivity (allow self-signed for testing)
            if curl -s -k -f "$HTTPS_URL/health" > /dev/null; then
                log_success "✅ HTTPS endpoint working"
            else
                log_warning "⚠️  HTTPS endpoint not responding (may still be provisioning)"
            fi
            
            # Test HTTP to HTTPS redirect
            HTTP_URL=$(echo "$SERVICE_URL" | sed 's/https:/http:/')
            if [ "$HTTP_URL" != "$SERVICE_URL" ]; then
                REDIRECT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HTTP_URL" || echo "000")
                if [ "$REDIRECT_STATUS" -eq 301 ] || [ "$REDIRECT_STATUS" -eq 302 ]; then
                    log_success "✅ HTTP to HTTPS redirect working (HTTP $REDIRECT_STATUS)"
                else
                    log_warning "⚠️  HTTP to HTTPS redirect returned HTTP $REDIRECT_STATUS"
                fi
            fi
        fi
    else
        log_warning "No service URL found"
    fi
}

# Cleanup resources
cleanup() {
    log_info "Cleaning up test resources..."
    
    # Undeploy muppet
    curl -s -X DELETE "$PLATFORM_URL/api/v1/muppets/$MUPPET_NAME/deployment" > /dev/null
    log_success "Initiated muppet undeployment"
    
    # Wait a bit for undeployment
    sleep 10
    
    # Delete ECR repository
    if aws ecr describe-repositories --repository-names "muppet-platform/$MUPPET_NAME" --region "$REGION" &> /dev/null; then
        aws ecr delete-repository --repository-name "muppet-platform/$MUPPET_NAME" --region "$REGION" --force > /dev/null
        log_success "Deleted ECR repository"
    fi
    
    # Delete muppet
    curl -s -X DELETE "$PLATFORM_URL/api/v1/muppets/$MUPPET_NAME" > /dev/null
    log_success "Deleted muppet: $MUPPET_NAME"
}

# Main execution
main() {
    echo "Starting AWS integration test with muppet: $MUPPET_NAME"
    echo "Region: $REGION"
    echo "Platform URL: $PLATFORM_URL"
    echo ""
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Run tests
    check_prerequisites
    test_aws_connectivity
    setup_ecr
    create_muppet
    build_and_push_image
    deploy_muppet
    
    if monitor_deployment; then
        test_service
        test_tls_certificate
        log_success "🎉 AWS integration test completed successfully!"
    else
        log_error "💥 AWS integration test failed during deployment"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --no-cleanup)
        trap - EXIT
        log_warning "Cleanup disabled - resources will remain in AWS"
        ;;
    --help|-h)
        echo "Usage: $0 [--no-cleanup] [--help]"
        echo ""
        echo "Options:"
        echo "  --no-cleanup    Don't clean up AWS resources after test"
        echo "  --help, -h      Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  AWS_DEFAULT_REGION    AWS region (default: us-west-2)"
        echo "  PLATFORM_URL          Platform URL (default: http://localhost:8000)"
        exit 0
        ;;
esac

# Run main function
main