#!/bin/bash

# Setup script for Muppet Platform using UV
# This script installs UV and sets up the Python environment

set -e

echo "Setting up Muppet Platform with UV..."

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "UV not found. Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo "UV installed successfully!"
else
    echo "UV is already installed."
fi

# Create virtual environment with Python 3.10+
echo "Creating virtual environment with Python 3.10..."
uv venv --python 3.10

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e ".[dev]"

echo "Setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the MCP server:"
echo "  uv run mcp-server"
echo ""
echo "To run tests:"
echo "  uv run pytest"