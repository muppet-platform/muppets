#!/bin/bash

# {{muppet_name}} Muppet - Run Script
# Starts the muppet locally for development and testing

set -e

echo "🚀 Starting {{muppet_name}} muppet locally..."

# Load environment variables if available
if [ -f .env.local ]; then
    export $(grep -v '^#' .env.local | xargs)
fi

# Set development environment
export MICRONAUT_ENVIRONMENTS=development

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use"
        echo "Please stop the service using port $port or change the port in .env.local"
        exit 1
    fi
}

# Check if port 3000 is available
check_port 3000

# Option 1: Run with Gradle (development mode with hot reload)
if [ "$1" = "--gradle" ] || [ "$1" = "-g" ]; then
    echo "🏃 Running with Gradle (development mode)..."
    ./gradlew run
    
# Option 2: Run with Docker (production-like)
elif [ "$1" = "--docker" ] || [ "$1" = "-d" ]; then
    echo "🐳 Running with Docker..."
    
    # Build if image doesn't exist
    if ! docker images {{muppet_name}}:latest -q | grep -q .; then
        echo "📦 Building Docker image first..."
        ./scripts/build.sh
    fi
    
    # Create .env.local if it doesn't exist
    if [ ! -f .env.local ]; then
        echo "📝 Creating .env.local file..."
        cat > .env.local << EOF
# Local development environment variables for {{muppet_name}}
MICRONAUT_ENVIRONMENTS=development
MUPPET_NAME={{muppet_name}}
AWS_REGION=us-east-1
ENVIRONMENT=development

# Local development ports
SERVER_PORT=3000

# Logging
LOG_LEVEL=DEBUG
EOF
    fi
    
    # Run container
    docker run --rm \
        -p 3000:3000 \
        --env-file .env.local \
        --name {{muppet_name}}-dev \
        {{muppet_name}}:latest
        
# Option 3: Run with Docker Compose (with dependencies)
elif [ "$1" = "--compose" ] || [ "$1" = "-c" ]; then
    echo "🐙 Running with Docker Compose..."
    
    if [ ! -f docker-compose.local.yml ]; then
        echo "❌ docker-compose.local.yml not found"
        exit 1
    fi
    
    docker-compose -f docker-compose.local.yml up --build
    
# Default: Run JAR directly
else
    echo "☕ Running JAR directly..."
    
    # Build if JAR doesn't exist
    if [ ! -f build/libs/{{muppet_name}}-*-all.jar ]; then
        echo "📦 Building JAR first..."
        ./gradlew shadowJar
    fi
    
    # Find the JAR file
    JAR_FILE=$(find build/libs -name "{{muppet_name}}-*-all.jar" | head -n 1)
    
    if [ -z "$JAR_FILE" ]; then
        echo "❌ JAR file not found"
        exit 1
    fi
    
    echo "🏃 Starting $JAR_FILE..."
    java -jar "$JAR_FILE"
fi

echo ""
echo "Usage: $0 [option]"
echo "Options:"
echo "  (no option)  Run JAR directly (default)"
echo "  --gradle|-g  Run with Gradle (development mode)"
echo "  --docker|-d  Run with Docker"
echo "  --compose|-c Run with Docker Compose"
echo ""