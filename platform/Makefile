# Muppet Platform Development Makefile

.PHONY: help setup build run stop test clean lint format check-deps

# Default target
help:
	@echo "Muppet Platform Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup and Installation:"
	@echo "  setup          Set up local development environment"
	@echo "  check-deps     Check if all dependencies are installed"
	@echo ""
	@echo "Development:"
	@echo "  build          Build Docker image"
	@echo "  run            Start local development environment"
	@echo "  stop           Stop local development environment"
	@echo "  logs           View service logs"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests"
	@echo "  test-cov       Run tests with coverage report"
	@echo "  test-watch     Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  type-check     Run mypy type checking"
	@echo ""
	@echo "Utilities:"
	@echo "  clean          Clean up containers and volumes"
	@echo "  shell          Open shell in platform container"
	@echo "  localstack     Open shell in LocalStack container"

# Setup and Installation
setup:
	@echo "Setting up local development environment..."
	./scripts/setup-local-dev.sh

check-deps:
	@echo "Checking dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Please install Rancher Desktop."; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "❌ UV not found. Please install UV."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "❌ Docker not running. Please start Rancher Desktop."; exit 1; }
	@echo "✅ All dependencies are installed and running"

# Development
build:
	@echo "Building platform..."
	./scripts/build.sh

run: check-deps
	@echo "Starting development environment..."
	./scripts/run.sh

stop:
	@echo "Stopping development environment..."
	./scripts/stop.sh

logs:
	@echo "Viewing service logs..."
	docker-compose -f docker-compose.local.yml logs -f

# Testing
test:
	@echo "Running tests..."
	./scripts/test.sh

test-cov:
	@echo "Running tests with coverage..."
	uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

test-watch:
	@echo "Running tests in watch mode..."
	uv run python -m pytest tests/ -f

# Code Quality
lint:
	@echo "Running linting checks..."
	uv run flake8 src/ tests/
	uv run mypy src/

format:
	@echo "Formatting code..."
	uv run black src/ tests/
	uv run isort src/ tests/

type-check:
	@echo "Running type checks..."
	uv run mypy src/

# Utilities
clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose -f docker-compose.local.yml down -v
	docker system prune -f

shell:
	@echo "Opening shell in platform container..."
	docker-compose -f docker-compose.local.yml exec platform /bin/bash

localstack:
	@echo "Opening shell in LocalStack container..."
	docker-compose -f docker-compose.local.yml exec localstack /bin/bash

# Development workflow shortcuts
dev: build run
	@echo "Development environment is ready!"
	@echo "Platform: http://localhost:8000"
	@echo "LocalStack: http://localhost:4566"

restart: stop run
	@echo "Services restarted!"

# CI-like checks
ci: format lint test
	@echo "All CI checks passed!"