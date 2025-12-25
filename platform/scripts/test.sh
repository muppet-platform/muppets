#!/bin/bash

# Test script for Muppet Platform

set -e

echo "Running Muppet Platform tests..."

# Run tests with UV
uv run python -m pytest tests/ -v

echo "Tests complete!"
