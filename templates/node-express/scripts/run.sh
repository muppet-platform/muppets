#!/bin/bash

# Node.js Express run script for {{muppet_name}}
set -e

# Default mode
MODE="dev"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|--production)
            MODE="prod"
            shift
            ;;
        --dev|--development)
            MODE="dev"
            shift
            ;;
        --docker)
            MODE="docker"
            shift
            ;;
        --compose)
            MODE="compose"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--dev|--prod|--docker|--compose]"
            echo "  --dev        Run in development mode with hot reload (default)"
            echo "  --prod       Run in production mode (requires build)"
            echo "  --docker     Run with Docker"
            echo "  --compose    Run with Docker Compose (includes LocalStack)"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 Starting {{muppet_name}} in $MODE mode..."

case $MODE in
    "dev")
        echo "📝 Development mode with hot reload"
        echo "🌐 Server will be available at: http://localhost:3000"
        echo "🔍 Health check: http://localhost:3000/health"
        echo "📚 API docs: http://localhost:3000/api/v1"
        echo ""
        echo "Press Ctrl+C to stop the server"
        npm run dev
        ;;
    "prod")
        echo "🏭 Production mode"
        if [ ! -f "dist/app.js" ]; then
            echo "❌ Production build not found. Running build first..."
            ./scripts/build.sh
        fi
        echo "🌐 Server will be available at: http://localhost:3000"
        npm start
        ;;
    "docker")
        echo "🐳 Docker mode"
        echo "Building Docker image..."
        docker build -t {{muppet_name}} .
        echo "Running Docker container..."
        docker run --rm -p 3000:3000 --name {{muppet_name}}-dev {{muppet_name}}
        ;;
    "compose")
        echo "🐳 Docker Compose mode (with LocalStack)"
        if [ ! -f "docker-compose.local.yml" ]; then
            echo "❌ docker-compose.local.yml not found"
            exit 1
        fi
        echo "Starting services with Docker Compose..."
        docker-compose -f docker-compose.local.yml up --build
        ;;
esac