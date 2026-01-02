#!/bin/bash

# {{muppet_name}} Muppet - Run Script

set -e

echo "🚀 Starting {{muppet_name}} muppet locally..."

# Load environment variables if available
if [ -f .env.local ]; then
    export $(grep -v '^#' .env.local | xargs)
fi

# Set development environment
export MICRONAUT_ENVIRONMENTS=development

# Build if JAR doesn't exist
if [ ! -f build/libs/app.jar ]; then
    echo "📦 Building JAR first..."
    ./gradlew shadowJar
    cp build/libs/*-all.jar build/libs/app.jar
fi

echo "🏃 Starting application..."
java -jar build/libs/app.jar