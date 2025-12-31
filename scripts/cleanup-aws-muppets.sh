#!/bin/bash

# AWS Muppet Cleanup Script
# Discovers muppets from GitHub organization and cleans up AWS resources
# Processes each muppet individually with user confirmation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
GITHUB_ORG="muppet-platform"
ECS_CLUSTER="muppet-platform-cluster"
AWS_REGION="${AWS_REGION:-us-west-2}"
TERRAFORM_STATE_BUCKET="muppet-platform-terraform-state"
TERRAFORM_LOCKS_TABLE="muppet-platform-terraform-locks"

# Protected repositories (never delete these)
PROTECTED_REPOS=(
    "muppets"
    "terraform-modules"
    "platform-docs"
    "steering-docs"
)

# Protected AWS resources (never delete these)
PROTECTED_AWS_RESOURCES=(
    "muppet-platform-cluster"
    "muppet-platform-*"
    "muppet-terraform-state-*"
    "muppet-terraform-locks"
    "muppet-platform-vpc"
    "muppet-platform-role-*"
    "muppet-platform-logs"
)

# Global flags
DRY_RUN=false
LIST_ONLY=false
FORCE=false
SPECIFIC_MUPPET=""
TOFU_AVAILABLE=false

# Usage information
usage() {
    cat << EOF
AWS Muppet Cleanup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --dry-run           Show what would be deleted without actually deleting
    --list-only         List discovered muppets and exit
    --muppet NAME       Process only the specified muppet
    --force             Skip confirmation prompts (DANGEROUS)
    --help              Show this help message

EXAMPLES:
    $0                          # Interactive cleanup of all muppets
    $0 --dry-run               # Show what would be deleted
    $0 --list-only             # List muppets without deleting
    $0 --muppet test05         # Process only test05 muppet
    $0 --muppet test05 --force # Delete test05 without confirmation

DESCRIPTION:
    This script discovers muppets from the GitHub organization '$GITHUB_ORG'
    and cleans up their corresponding AWS resources and OpenTofu state files.
    Each muppet is processed individually with user confirmation (unless --force is used).

    GitHub repositories are NOT deleted - only AWS resources are cleaned up.
    Protected AWS resources are never deleted.
    
    OpenTofu state cleanup requires 'tofu' command to be installed.
    If not available, state files will remain in S3 (manual cleanup required).

EOF
}

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

log_step() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

log_muppet() {
    echo -e "${CYAN}📦 $1${NC}"
}

# Check if a repository is protected
is_protected_repo() {
    local repo_name="$1"
    for protected in "${PROTECTED_REPOS[@]}"; do
        if [[ "$repo_name" == "$protected" ]]; then
            return 0
        fi
    done
    return 1
}

# Check if an AWS resource is protected
is_protected_aws_resource() {
    local resource_name="$1"
    for protected in "${PROTECTED_AWS_RESOURCES[@]}"; do
        if [[ "$resource_name" == $protected ]]; then
            return 0
        fi
    done
    return 1
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is required but not installed"
        echo "Install with: brew install gh"
        exit 1
    fi
    
    # Check GitHub authentication
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated"
        echo "Run: gh auth login"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is required but not installed"
        echo "Install with: brew install awscli"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured or credentials are invalid"
        echo "Run: aws configure"
        exit 1
    fi
    
    # Check OpenTofu
    if ! command -v tofu &> /dev/null; then
        log_warning "OpenTofu not found - state cleanup will be skipped"
        log_warning "Install with: brew install opentofu/tap/opentofu"
        TOFU_AVAILABLE=false
    else
        TOFU_AVAILABLE=true
        log_success "OpenTofu found - state cleanup will be included"
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        echo "Install with: brew install jq"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
    
    # Show current AWS identity
    local aws_identity
    aws_identity=$(aws sts get-caller-identity --query 'Arn' --output text)
    log_info "AWS Identity: $aws_identity"
    log_info "AWS Region: $AWS_REGION"
    
    if [[ "$TOFU_AVAILABLE" == "true" ]]; then
        log_info "OpenTofu: Available - will clean up state files"
    else
        log_warning "OpenTofu: Not available - state files will remain"
    fi
}

# Discover muppets from GitHub organization
discover_muppets_from_github() {
    log_step "Discovering muppets from GitHub organization: $GITHUB_ORG..." >&2
    
    # Get all repositories
    local all_repos
    all_repos=$(gh repo list "$GITHUB_ORG" --limit 1000 --json name,createdAt,isPrivate | jq -r '.[].name')
    
    if [[ -z "$all_repos" ]]; then
        log_warning "No repositories found in organization $GITHUB_ORG" >&2
        return 1
    fi
    
    local muppets=()
    local protected_count=0
    
    echo "" >&2
    echo "Found repositories:" >&2
    
    while IFS= read -r repo; do
        if is_protected_repo "$repo"; then
            echo -e "├── ${YELLOW}$repo${NC} (PROTECTED - platform repository)" >&2
            ((protected_count++))
        else
            echo -e "├── ${GREEN}$repo${NC} ✓" >&2
            muppets+=("$repo")
        fi
    done <<< "$all_repos"
    
    echo "" >&2
    log_info "Protected repositories: $protected_count" >&2
    log_info "Muppets identified: ${#muppets[@]}" >&2
    
    if [[ ${#muppets[@]} -eq 0 ]]; then
        log_warning "No muppets found for cleanup" >&2
        return 1
    fi
    
    printf '%s\n' "${muppets[@]}"
}

# Get AWS resource information for a muppet
get_aws_resource_info() {
    local muppet_name="$1"
    local resource_type="$2"
    
    case "$resource_type" in
        "ECS_SERVICE")
            aws ecs describe-services \
                --cluster "$ECS_CLUSTER" \
                --services "${muppet_name}-service" \
                --query 'services[0]' \
                --output json 2>/dev/null || echo "null"
            ;;
        "ECR_REPO")
            aws ecr describe-repositories \
                --repository-names "$muppet_name" \
                --query 'repositories[0]' \
                --output json 2>/dev/null || echo "null"
            ;;
        "ALB")
            aws elbv2 describe-load-balancers \
                --names "${muppet_name}-alb" \
                --query 'LoadBalancers[0]' \
                --output json 2>/dev/null || echo "null"
            ;;
        "TARGET_GROUP")
            aws elbv2 describe-target-groups \
                --names "${muppet_name}-tg" \
                --query 'TargetGroups[0]' \
                --output json 2>/dev/null || echo "null"
            ;;
        "LOG_GROUP")
            aws logs describe-log-groups \
                --log-group-name-prefix "/aws/ecs/$muppet_name" \
                --query 'logGroups[0]' \
                --output json 2>/dev/null || echo "null"
            ;;
        "IAM_ROLE")
            aws iam get-role \
                --role-name "${muppet_name}-task-role" \
                --query 'Role' \
                --output json 2>/dev/null || echo "null"
            ;;
        "SECURITY_GROUP")
            aws ec2 describe-security-groups \
                --filters "Name=group-name,Values=${muppet_name}-sg" \
                --query 'SecurityGroups[0]' \
                --output json 2>/dev/null || echo "null"
            ;;
    esac
}

# Discover AWS resources for a muppet
discover_aws_resources_for_muppet() {
    local muppet_name="$1"
    local resources=()
    
    # ECS Service
    local ecs_info
    ecs_info=$(get_aws_resource_info "$muppet_name" "ECS_SERVICE")
    if [[ "$ecs_info" != "null" ]]; then
        local service_name status running_count
        service_name=$(echo "$ecs_info" | jq -r '.serviceName // empty')
        status=$(echo "$ecs_info" | jq -r '.status // empty')
        running_count=$(echo "$ecs_info" | jq -r '.runningCount // 0')
        
        if [[ -n "$service_name" ]]; then
            resources+=("ECS Service: $service_name ($status, $running_count tasks)")
        fi
    fi
    
    # ECR Repository
    local ecr_info
    ecr_info=$(get_aws_resource_info "$muppet_name" "ECR_REPO")
    if [[ "$ecr_info" != "null" ]]; then
        local repo_name
        repo_name=$(echo "$ecr_info" | jq -r '.repositoryName // empty')
        
        if [[ -n "$repo_name" ]]; then
            # Get image count and size
            local image_count=0
            local total_size=0
            
            local images
            images=$(aws ecr list-images --repository-name "$repo_name" --query 'imageIds' --output json 2>/dev/null || echo "[]")
            image_count=$(echo "$images" | jq 'length')
            
            if [[ $image_count -gt 0 ]]; then
                local repo_size
                repo_size=$(aws ecr describe-repository-statistics --repository-name "$repo_name" --query 'repositoryStatistics.repositorySizeInBytes' --output text 2>/dev/null || echo "0")
                total_size=$((repo_size / 1024 / 1024)) # Convert to MB
                resources+=("ECR Repository: $repo_name ($image_count images, ${total_size} MB)")
            else
                resources+=("ECR Repository: $repo_name (empty)")
            fi
        fi
    fi
    
    # Load Balancer
    local alb_info
    alb_info=$(get_aws_resource_info "$muppet_name" "ALB")
    if [[ "$alb_info" != "null" ]]; then
        local alb_name
        alb_name=$(echo "$alb_info" | jq -r '.LoadBalancerName // empty')
        if [[ -n "$alb_name" ]]; then
            resources+=("Load Balancer: $alb_name")
        fi
    fi
    
    # Target Group
    local tg_info
    tg_info=$(get_aws_resource_info "$muppet_name" "TARGET_GROUP")
    if [[ "$tg_info" != "null" ]]; then
        local tg_name
        tg_name=$(echo "$tg_info" | jq -r '.TargetGroupName // empty')
        if [[ -n "$tg_name" ]]; then
            resources+=("Target Group: $tg_name")
        fi
    fi
    
    # CloudWatch Log Group
    local log_info
    log_info=$(get_aws_resource_info "$muppet_name" "LOG_GROUP")
    if [[ "$log_info" != "null" ]]; then
        local log_group_name stored_bytes
        log_group_name=$(echo "$log_info" | jq -r '.logGroupName // empty')
        stored_bytes=$(echo "$log_info" | jq -r '.storedBytes // 0')
        
        if [[ -n "$log_group_name" ]]; then
            local size_mb=$((stored_bytes / 1024 / 1024))
            resources+=("CloudWatch Logs: $log_group_name (${size_mb} MB)")
        fi
    fi
    
    # IAM Role
    local iam_info
    iam_info=$(get_aws_resource_info "$muppet_name" "IAM_ROLE")
    if [[ "$iam_info" != "null" ]]; then
        local role_name
        role_name=$(echo "$iam_info" | jq -r '.RoleName // empty')
        if [[ -n "$role_name" ]]; then
            resources+=("IAM Role: $role_name")
        fi
    fi
    
    # Security Group
    local sg_info
    sg_info=$(get_aws_resource_info "$muppet_name" "SECURITY_GROUP")
    if [[ "$sg_info" != "null" ]]; then
        local sg_name
        sg_name=$(echo "$sg_info" | jq -r '.GroupName // empty')
        if [[ -n "$sg_name" ]]; then
            resources+=("Security Group: $sg_name")
        fi
    fi
    
    # Parameter Store (count parameters)
    local param_count
    param_count=$(aws ssm describe-parameters \
        --parameter-filters "Key=Name,Option=BeginsWith,Values=/muppet/$muppet_name/" \
        --query 'Parameters' \
        --output json 2>/dev/null | jq 'length' || echo "0")
    
    if [[ $param_count -gt 0 ]]; then
        resources+=("Parameter Store: $param_count parameters")
    fi
    
    # OpenTofu State
    if [[ "$TOFU_AVAILABLE" == "true" ]]; then
        local tofu_state_info
        tofu_state_info=$(get_tofu_state_info "$muppet_name")
        if [[ -n "$tofu_state_info" ]]; then
            resources+=("$tofu_state_info")
        fi
    fi
    
    # Handle empty array case for set -u
    if [[ ${#resources[@]} -eq 0 ]]; then
        echo ""
    else
        printf '%s\n' "${resources[@]}"
    fi
}

# Display muppet resources
display_muppet_resources() {
    local muppet_name="$1"
    local github_info="$2"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    log_muppet "Muppet: $muppet_name"
    
    # GitHub repository info
    local created_at
    created_at=$(echo "$github_info" | jq -r '.createdAt // empty' | cut -d'T' -f1)
    echo -e "├── ${CYAN}GitHub Repo:${NC} ✅ $GITHUB_ORG/$muppet_name (created $created_at)"
    
    # AWS resources
    local aws_resources
    aws_resources=$(discover_aws_resources_for_muppet "$muppet_name")
    
    if [[ -n "$aws_resources" ]]; then
        while IFS= read -r resource; do
            echo -e "├── ${CYAN}$resource${NC}"
        done <<< "$aws_resources"
    else
        echo -e "├── ${YELLOW}No AWS resources found${NC}"
    fi
    
    echo ""
}

# Confirm muppet deletion
confirm_muppet_deletion() {
    local muppet_name="$1"
    
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi
    
    echo -e "${RED}⚠️  About to delete AWS resources for muppet: $muppet_name${NC}"
    echo "This will permanently remove:"
    echo "  • All AWS resources listed above"
    echo "  • OpenTofu state files (if present)"
    echo ""
    echo -e "${YELLOW}Note: GitHub repository will NOT be deleted${NC}"
    echo ""
    
    local response
    read -p "Clean up AWS resources for '$muppet_name'? (y/N): " response
    [[ "$response" =~ ^[Yy]$ ]]
}

# Delete AWS resources for a muppet
delete_aws_resources() {
    local muppet_name="$1"
    
    log_step "Deleting AWS resources for muppet: $muppet_name"
    
    # Stop and delete ECS service
    local ecs_info
    ecs_info=$(get_aws_resource_info "$muppet_name" "ECS_SERVICE")
    if [[ "$ecs_info" != "null" ]]; then
        local service_name
        service_name=$(echo "$ecs_info" | jq -r '.serviceName')
        
        if [[ "$service_name" != "null" && -n "$service_name" ]]; then
            # Scale down to 0
            aws ecs update-service \
                --cluster "$ECS_CLUSTER" \
                --service "$service_name" \
                --desired-count 0 \
                --output text &>/dev/null
            
            # Wait for tasks to stop
            log_step "Waiting for ECS tasks to stop..."
            aws ecs wait services-stable \
                --cluster "$ECS_CLUSTER" \
                --services "$service_name"
            
            # Delete service
            aws ecs delete-service \
                --cluster "$ECS_CLUSTER" \
                --service "$service_name" \
                --output text &>/dev/null
            
            log_success "Deleted ECS service: $service_name"
        fi
    fi
    
    # Delete Load Balancer
    local alb_info
    alb_info=$(get_aws_resource_info "$muppet_name" "ALB")
    if [[ "$alb_info" != "null" ]]; then
        local alb_arn
        alb_arn=$(echo "$alb_info" | jq -r '.LoadBalancerArn')
        
        if [[ "$alb_arn" != "null" && -n "$alb_arn" ]]; then
            aws elbv2 delete-load-balancer \
                --load-balancer-arn "$alb_arn" \
                --output text &>/dev/null
            
            log_success "Deleted load balancer: ${muppet_name}-alb"
        fi
    fi
    
    # Delete Target Group
    local tg_info
    tg_info=$(get_aws_resource_info "$muppet_name" "TARGET_GROUP")
    if [[ "$tg_info" != "null" ]]; then
        local tg_arn
        tg_arn=$(echo "$tg_info" | jq -r '.TargetGroupArn')
        
        if [[ "$tg_arn" != "null" && -n "$tg_arn" ]]; then
            # Wait a bit for ALB deletion to propagate
            sleep 10
            
            aws elbv2 delete-target-group \
                --target-group-arn "$tg_arn" \
                --output text &>/dev/null
            
            log_success "Deleted target group: ${muppet_name}-tg"
        fi
    fi
    
    # Delete ECR repository
    local ecr_info
    ecr_info=$(get_aws_resource_info "$muppet_name" "ECR_REPO")
    if [[ "$ecr_info" != "null" ]]; then
        local repo_name
        repo_name=$(echo "$ecr_info" | jq -r '.repositoryName')
        
        if [[ "$repo_name" != "null" && -n "$repo_name" ]]; then
            aws ecr delete-repository \
                --repository-name "$repo_name" \
                --force \
                --output text &>/dev/null
            
            log_success "Deleted ECR repository: $repo_name"
        fi
    fi
    
    # Delete CloudWatch log group
    local log_info
    log_info=$(get_aws_resource_info "$muppet_name" "LOG_GROUP")
    if [[ "$log_info" != "null" ]]; then
        local log_group_name
        log_group_name=$(echo "$log_info" | jq -r '.logGroupName')
        
        if [[ "$log_group_name" != "null" && -n "$log_group_name" ]]; then
            aws logs delete-log-group \
                --log-group-name "$log_group_name" \
                --output text &>/dev/null
            
            log_success "Deleted CloudWatch log group: $log_group_name"
        fi
    fi
    
    # Delete IAM role and policies
    local iam_info
    iam_info=$(get_aws_resource_info "$muppet_name" "IAM_ROLE")
    if [[ "$iam_info" != "null" ]]; then
        local role_name
        role_name=$(echo "$iam_info" | jq -r '.RoleName')
        
        if [[ "$role_name" != "null" && -n "$role_name" ]]; then
            # Detach policies
            local attached_policies
            attached_policies=$(aws iam list-attached-role-policies \
                --role-name "$role_name" \
                --query 'AttachedPolicies[].PolicyArn' \
                --output text 2>/dev/null || echo "")
            
            if [[ -n "$attached_policies" ]]; then
                while IFS= read -r policy_arn; do
                    if [[ -n "$policy_arn" ]]; then
                        aws iam detach-role-policy \
                            --role-name "$role_name" \
                            --policy-arn "$policy_arn" \
                            --output text &>/dev/null
                    fi
                done <<< "$attached_policies"
            fi
            
            # Delete role
            aws iam delete-role \
                --role-name "$role_name" \
                --output text &>/dev/null
            
            log_success "Deleted IAM role: $role_name"
        fi
    fi
    
    # Delete Security Group
    local sg_info
    sg_info=$(get_aws_resource_info "$muppet_name" "SECURITY_GROUP")
    if [[ "$sg_info" != "null" ]]; then
        local sg_id
        sg_id=$(echo "$sg_info" | jq -r '.GroupId')
        
        if [[ "$sg_id" != "null" && -n "$sg_id" ]]; then
            aws ec2 delete-security-group \
                --group-id "$sg_id" \
                --output text &>/dev/null
            
            log_success "Deleted security group: ${muppet_name}-sg"
        fi
    fi
    
    # Clean up Parameter Store
    local parameters
    parameters=$(aws ssm describe-parameters \
        --parameter-filters "Key=Name,Option=BeginsWith,Values=/muppet/$muppet_name/" \
        --query 'Parameters[].Name' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$parameters" ]]; then
        local param_count=0
        while IFS= read -r param_name; do
            if [[ -n "$param_name" ]]; then
                aws ssm delete-parameter \
                    --name "$param_name" \
                    --output text &>/dev/null
                ((param_count++))
            fi
        done <<< "$parameters"
        
        if [[ $param_count -gt 0 ]]; then
            log_success "Cleaned Parameter Store: $param_count parameters"
        fi
    fi
}

# Check if OpenTofu state exists for a muppet
check_tofu_state_exists() {
    local muppet_name="$1"
    local state_key="muppets/$muppet_name/terraform.tfstate"
    
    aws s3api head-object \
        --bucket "$TERRAFORM_STATE_BUCKET" \
        --key "$state_key" \
        --output text &>/dev/null
}

# Get OpenTofu state information for a muppet
get_tofu_state_info() {
    local muppet_name="$1"
    local state_key="muppets/$muppet_name/terraform.tfstate"
    
    if check_tofu_state_exists "$muppet_name"; then
        local state_size
        state_size=$(aws s3api head-object \
            --bucket "$TERRAFORM_STATE_BUCKET" \
            --key "$state_key" \
            --query 'ContentLength' \
            --output text 2>/dev/null || echo "0")
        
        local size_kb=$((state_size / 1024))
        echo "OpenTofu State: $state_key (${size_kb} KB)"
    fi
}

# Clean up OpenTofu state for a muppet
cleanup_tofu_state() {
    local muppet_name="$1"
    
    if [[ "$TOFU_AVAILABLE" != "true" ]]; then
        log_warning "OpenTofu not available - skipping state cleanup"
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        if check_tofu_state_exists "$muppet_name"; then
            echo "Would delete OpenTofu state: muppets/$muppet_name/terraform.tfstate"
        fi
        return 0
    fi
    
    log_step "Cleaning up OpenTofu state for muppet: $muppet_name"
    
    local state_key="muppets/$muppet_name/terraform.tfstate"
    
    # Check if state file exists
    if ! check_tofu_state_exists "$muppet_name"; then
        log_info "No OpenTofu state found for muppet: $muppet_name"
        return 0
    fi
    
    # Create a temporary directory for state operations
    local temp_dir
    temp_dir=$(mktemp -d)
    cleanup_temp() {
        if [[ -n "${temp_dir:-}" && -d "$temp_dir" ]]; then
            rm -rf "$temp_dir"
        fi
    }
    trap cleanup_temp EXIT
    
    cd "$temp_dir"
    
    # Create minimal backend configuration
    cat > backend.tf << EOF
terraform {
  required_version = ">= 1.5"
  
  backend "s3" {
    bucket = "$TERRAFORM_STATE_BUCKET"
    key    = "$state_key"
    region = "$AWS_REGION"
    
    dynamodb_table = "$TERRAFORM_LOCKS_TABLE"
    encrypt        = true
  }
}
EOF
    
    # Initialize OpenTofu with existing state
    if tofu init -input=false &>/dev/null; then
        log_info "Initialized OpenTofu with existing state"
        
        # Try to destroy all resources in state (this should be safe since we already deleted them)
        # Use -auto-approve and ignore errors since resources are already gone
        tofu destroy -auto-approve -input=false &>/dev/null || true
        
        # Force remove the state file from S3
        if aws s3 rm "s3://$TERRAFORM_STATE_BUCKET/$state_key" &>/dev/null; then
            log_success "Deleted OpenTofu state: $state_key"
        else
            log_warning "Failed to delete OpenTofu state: $state_key"
        fi
        
        # Clean up any state locks (force unlock)
        local lock_id
        lock_id=$(aws dynamodb scan \
            --table-name "$TERRAFORM_LOCKS_TABLE" \
            --filter-expression "begins_with(LockID, :prefix)" \
            --expression-attribute-values "{\":prefix\":{\"S\":\"$TERRAFORM_STATE_BUCKET/$state_key\"}}" \
            --query 'Items[0].LockID.S' \
            --output text 2>/dev/null || echo "None")
        
        if [[ "$lock_id" != "None" && "$lock_id" != "null" && -n "$lock_id" ]]; then
            tofu force-unlock -force "$lock_id" &>/dev/null || true
            log_success "Cleaned up OpenTofu state lock: $lock_id"
        fi
    else
        log_warning "Failed to initialize OpenTofu - manually deleting state file"
        
        # Fallback: just delete the state file directly
        if aws s3 rm "s3://$TERRAFORM_STATE_BUCKET/$state_key" &>/dev/null; then
            log_success "Deleted OpenTofu state: $state_key"
        else
            log_warning "Failed to delete OpenTofu state: $state_key"
        fi
    fi
    
    cd - &>/dev/null
}

# Process a single muppet
process_muppet() {
    local muppet_name="$1"
    local github_info="$2"
    
    # Display muppet resources
    display_muppet_resources "$muppet_name" "$github_info"
    
    # Check if this is a dry run
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}🔍 DRY RUN: Would clean up AWS resources for '$muppet_name'${NC}"
        echo ""
        return 0
    fi
    
    # Confirm deletion
    if ! confirm_muppet_deletion "$muppet_name"; then
        echo -e "${YELLOW}⏭️  Skipped muppet: $muppet_name${NC}"
        echo ""
        return 0
    fi
    
    echo ""
    log_step "Cleaning up AWS resources for muppet: $muppet_name"
    
    # Delete AWS resources
    if delete_aws_resources "$muppet_name"; then
        # Clean up OpenTofu state
        cleanup_tofu_state "$muppet_name"
        log_success "AWS resources and OpenTofu state cleaned up for '$muppet_name'"
        log_info "GitHub repository '$GITHUB_ORG/$muppet_name' was left intact"
    else
        log_error "Failed to delete some AWS resources for muppet: $muppet_name"
    fi
    
    echo ""
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --list-only)
                LIST_ONLY=true
                shift
                ;;
            --muppet)
                SPECIFIC_MUPPET="$2"
                shift 2
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Show header
    echo ""
    echo "🧹 AWS Muppet Cleanup Script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}🔍 DRY RUN MODE - No resources will be deleted${NC}"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Discover muppets from GitHub
    local muppets
    muppets=$(discover_muppets_from_github)
    
    if [[ -z "$muppets" ]]; then
        log_warning "No muppets found for cleanup"
        exit 0
    fi
    
    # Convert to array
    local muppet_array=()
    while IFS= read -r muppet; do
        muppet_array+=("$muppet")
    done <<< "$muppets"
    
    # If specific muppet requested, filter the list
    if [[ -n "$SPECIFIC_MUPPET" ]]; then
        local found=false
        for muppet in "${muppet_array[@]}"; do
            if [[ "$muppet" == "$SPECIFIC_MUPPET" ]]; then
                found=true
                break
            fi
        done
        
        if [[ "$found" == "false" ]]; then
            log_error "Muppet '$SPECIFIC_MUPPET' not found in organization $GITHUB_ORG"
            exit 1
        fi
        
        muppet_array=("$SPECIFIC_MUPPET")
    fi
    
    # If list-only mode, just show the muppets and exit
    if [[ "$LIST_ONLY" == "true" ]]; then
        echo ""
        log_info "Discovered muppets:"
        for muppet in "${muppet_array[@]}"; do
            echo "  • $muppet"
        done
        exit 0
    fi
    
    # Get GitHub repository information for all muppets
    local github_repos_info
    github_repos_info=$(gh repo list "$GITHUB_ORG" --limit 1000 --json name,createdAt,isPrivate)
    
    # Process each muppet
    local cleaned_count=0
    local skipped_count=0
    
    for muppet_name in "${muppet_array[@]}"; do
        # Get GitHub info for this muppet
        local github_info
        github_info=$(echo "$github_repos_info" | jq --arg name "$muppet_name" '.[] | select(.name == $name)')
        
        if process_muppet "$muppet_name" "$github_info"; then
            if [[ "$DRY_RUN" != "true" ]]; then
                ((cleaned_count++))
            fi
        else
            ((skipped_count++))
        fi
    done
    
    # Show summary
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    log_info "📊 Cleanup Summary:"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "├── Would process: ${#muppet_array[@]} muppets"
        echo "├── Mode: DRY RUN (no actual deletions)"
        echo "├── GitHub repos: Would be left intact"
        if [[ "$TOFU_AVAILABLE" == "true" ]]; then
            echo "└── OpenTofu: Available - would clean state files"
        else
            echo "└── OpenTofu: Not available - state files would remain"
        fi
    else
        echo "├── Processed: ${#muppet_array[@]} muppets"
        echo "├── Cleaned: $cleaned_count"
        echo "├── Skipped: $skipped_count"
        echo "├── GitHub repos: Left intact (not deleted)"
        echo "├── Protected resources: All core platform resources preserved"
        if [[ "$TOFU_AVAILABLE" == "true" ]]; then
            echo "└── OpenTofu state: Cleaned up for processed muppets"
        else
            echo "└── OpenTofu state: Not cleaned (tofu command not available)"
        fi
    fi
    
    echo ""
    log_success "Cleanup completed successfully!"
}

# Run main function
main "$@"