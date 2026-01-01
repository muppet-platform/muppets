# Muppet Platform Makefile
# Common development tasks for the Muppet Platform

.PHONY: help setup clean test build deploy docs

# Default target
help:
	@echo "Muppet Platform Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup          - Set up development environment"
	@echo "  setup-aws      - Configure AWS infrastructure"
	@echo "  setup-github   - Configure GitHub repositories"
	@echo ""
	@echo "Development Commands:"
	@echo "  test           - Run all tests"
	@echo "  test-platform  - Run platform tests"
	@echo "  test-templates - Run template tests"
	@echo "  test-terraform - Run Terraform module tests"
	@echo ""
	@echo "Build Commands:"
	@echo "  build          - Build all components"
	@echo "  build-platform - Build platform service"
	@echo "  build-templates - Build template tools"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  deploy-dev     - Deploy to development environment"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  deploy-prod    - Deploy to production environment"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean          - Clean build artifacts"
	@echo "  docs           - Generate documentation"
	@echo "  lint           - Run linting on all code"

# Setup commands
setup:
	@echo "Setting up Muppet Platform development environment..."
	@echo "This will be implemented as components are developed"

setup-aws:
	@echo "Configuring AWS infrastructure..."
	@echo "1. Ensure AWS CLI is configured"
	@echo "2. Deploy shared ECR registry"
	@echo "3. Set up basic infrastructure"
	cd terraform-modules/ecr && terraform init && terraform plan

setup-github:
	@echo "Configuring GitHub repositories..."
	@echo "1. Create muppet-platform organization"
	@echo "2. Set up repository templates"
	@echo "3. Configure branch protection rules"

# Test commands
test:
	@echo "Running all tests..."
	$(MAKE) test-platform
	$(MAKE) test-templates
	$(MAKE) test-terraform

test-platform:
	@echo "Running platform tests..."
	@echo "Platform tests will be implemented in task 2"

test-templates:
	@echo "Running template tests..."
	@echo "Template tests will be implemented in task 5"

test-terraform:
	@echo "Running Terraform module tests..."
	@echo "Terraform tests will be implemented in task 7"

# Build commands
build:
	@echo "Building all components..."
	$(MAKE) build-platform
	$(MAKE) build-templates

build-platform:
	@echo "Building platform service..."
	@echo "Platform build will be implemented in task 2"

build-templates:
	@echo "Building template tools..."
	@echo "Template tools build will be implemented in task 5"

# Deployment commands
deploy-dev:
	@echo "Deploying to development environment..."
	@echo "Development deployment will be implemented in task 8"

deploy-staging:
	@echo "Deploying to staging environment..."
	@echo "Staging deployment will be implemented in task 15"

deploy-prod:
	@echo "Deploying to production environment..."
	@echo "Production deployment will be implemented in task 15"

# Utility commands
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "target" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".terraform" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true

docs:
	@echo "Generating documentation..."
	@echo "Documentation generation will be implemented as components are developed"

lint:
	@echo "Running linting on all code..."
	@echo "Linting will be implemented as components are developed"

# Terraform specific commands (Legacy - use OpenTofu instead)
terraform-init:
	@echo "Initializing Terraform modules..."
	cd terraform-modules/ecr && terraform init

terraform-plan:
	@echo "Planning Terraform changes..."
	cd terraform-modules/ecr && terraform plan

terraform-apply:
	@echo "Applying Terraform changes..."
	cd terraform-modules/ecr && terraform apply

# OpenTofu commands (Preferred IaC tool)
opentofu-init:
	@echo "Initializing OpenTofu for platform infrastructure..."
	cd platform/terraform && tofu init

opentofu-plan:
	@echo "Planning OpenTofu changes for platform infrastructure..."
	cd platform/terraform && tofu plan

opentofu-apply:
	@echo "Applying OpenTofu changes for platform infrastructure..."
	cd platform/terraform && tofu apply

opentofu-destroy:
	@echo "Destroying OpenTofu infrastructure..."
	cd platform/terraform && tofu destroy

opentofu-validate:
	@echo "Validating OpenTofu configuration..."
	cd platform/terraform && tofu validate

# Docker commands
docker-build:
	@echo "Building Docker images..."
	@echo "Docker builds will be implemented as components are developed"

docker-push:
	@echo "Pushing Docker images to ECR..."
	@echo "Docker push will be implemented as components are developed"