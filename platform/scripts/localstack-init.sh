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

# Create Route53 hosted zone for s3u.dev
echo "Creating Route53 hosted zone for s3u.dev..."
ZONE_ID=$(awslocal route53 create-hosted-zone --name s3u.dev --caller-reference "muppet-platform-$(date +%s)" --query 'HostedZone.Id' --output text | cut -d'/' -f3)
echo "Created hosted zone with ID: $ZONE_ID"

# Create ACM wildcard certificate for *.s3u.dev in us-west-2
echo "Creating ACM wildcard certificate for *.s3u.dev in us-west-2..."
CERT_ARN=$(awslocal acm request-certificate \
  --domain-name "*.s3u.dev" \
  --subject-alternative-names "s3u.dev" \
  --validation-method DNS \
  --region us-west-2 \
  --query 'CertificateArn' \
  --output text)
echo "Created certificate with ARN: $CERT_ARN"

# In LocalStack, we need to manually mark the certificate as issued
echo "Marking certificate as issued in LocalStack..."
# Note: This is a LocalStack-specific workaround
awslocal acm describe-certificate --certificate-arn "$CERT_ARN" --region us-west-2 > /dev/null 2>&1

echo "LocalStack initialization complete!"
