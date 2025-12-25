#!/bin/bash
set -e

echo "🧹 Cleaning up manual test resources..."

# Get AWS account info
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-west-2")

echo "Cleaning up resources in AWS Account: $AWS_ACCOUNT_ID, Region: $AWS_REGION"

# List of test muppet names to clean up
TEST_MUPPETS=(
    "test-manual-muppet"
    "demo-muppet"
    "integration-test-muppet"
)

for muppet in "${TEST_MUPPETS[@]}"; do
    echo "Cleaning up resources for: $muppet"
    
    # Delete ECS service if exists
    if aws ecs describe-services --cluster muppet-platform-cluster --services "$muppet" &> /dev/null; then
        echo "  Deleting ECS service: $muppet"
        aws ecs update-service --cluster muppet-platform-cluster --service "$muppet" --desired-count 0 || true
        aws ecs delete-service --cluster muppet-platform-cluster --service "$muppet" || true
    fi
    
    # Delete ECR repository if exists
    if aws ecr describe-repositories --repository-names "$muppet" &> /dev/null; then
        echo "  Deleting ECR repository: $muppet"
        aws ecr delete-repository --repository-name "$muppet" --force || true
    fi
    
    # Delete Parameter Store parameters
    echo "  Deleting Parameter Store parameters for: $muppet"
    aws ssm delete-parameters-by-path --path "/muppet-platform/$muppet" --recursive || true
    
    # Delete CloudWatch log group
    echo "  Deleting CloudWatch log group: /aws/fargate/$muppet"
    aws logs delete-log-group --log-group-name "/aws/fargate/$muppet" || true
    
    # Delete GitHub repository (if exists and accessible)
    if gh repo view "muppet-platform/$muppet" &> /dev/null; then
        echo "  Deleting GitHub repository: muppet-platform/$muppet"
        gh repo delete "muppet-platform/$muppet" --confirm || true
    fi
done

# Clean up ECS cluster if empty
echo "Checking if ECS cluster can be cleaned up..."
SERVICES=$(aws ecs list-services --cluster muppet-platform-cluster --query 'serviceArns' --output text)
if [[ -z "$SERVICES" || "$SERVICES" == "None" ]]; then
    echo "  ECS cluster is empty, deleting: muppet-platform-cluster"
    aws ecs delete-cluster --cluster muppet-platform-cluster || true
else
    echo "  ECS cluster still has services, keeping it"
fi

echo "✅ Cleanup complete"
