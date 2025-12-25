#!/bin/bash

# LocalStack initialization script for Muppet Platform
# This script sets up the required AWS resources in LocalStack

echo "Initializing LocalStack for Muppet Platform..."

# Wait for LocalStack to be ready
awslocal --version || pip install awscli-local

# Create S3 buckets
echo "Creating S3 buckets..."
awslocal s3 mb s3://muppet-platform-artifacts
awslocal s3 mb s3://muppet-platform-terraform-state

# Create Parameter Store parameters
echo "Creating Parameter Store parameters..."
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/fargate-service/version" --value "1.0.0" --type "String"
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/monitoring/version" --value "1.0.0" --type "String"
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/networking/version" --value "1.0.0" --type "String"
awslocal ssm put-parameter --name "/muppet-platform/terraform/modules/ecr/version" --value "1.0.0" --type "String"

# Create ECR repository
echo "Creating ECR repository..."
awslocal ecr create-repository --repository-name muppet-platform/platform

# Create ECS cluster
echo "Creating ECS cluster..."
awslocal ecs create-cluster --cluster-name muppet-platform-local

# Create CloudWatch log groups
echo "Creating CloudWatch log groups..."
awslocal logs create-log-group --log-group-name /muppet-platform/platform
awslocal logs create-log-group --log-group-name /muppet-platform/muppets

echo "LocalStack initialization complete!"
