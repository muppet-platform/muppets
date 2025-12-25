#!/bin/bash

# {{muppet_name}} - Fix Gradle Wrapper Script
# This script fixes corrupted Gradle wrapper files, commonly caused by Git binary file issues

set -e

echo "🔧 Fixing Gradle wrapper for {{muppet_name}}..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in the right directory
if [ ! -f "build.gradle" ]; then
    echo "❌ Error: build.gradle not found"
    echo "Please run this script from the root of your muppet project"
    exit 1
fi

# Check for global Gradle installation
if ! command_exists gradle; then
    echo "❌ Error: Global Gradle installation required"
    echo ""
    echo "Please install Gradle first:"
    case "$(uname -s)" in
        Darwin*) 
            echo "  brew install gradle"
            ;;
        Linux*)  
            echo "  Download from https://gradle.org/install/"
            echo "  Or: sudo apt install gradle (Ubuntu/Debian)"
            ;;
        CYGWIN*|MINGW*|MSYS*) 
            echo "  Download from https://gradle.org/install/"
            echo "  Or: choco install gradle"
            ;;
    esac
    exit 1
fi

echo "✅ Found global Gradle installation"

# Backup existing wrapper if it exists
if [ -d "gradle/wrapper" ]; then
    echo "📦 Backing up existing wrapper to gradle/wrapper.backup"
    rm -rf gradle/wrapper.backup
    mv gradle/wrapper gradle/wrapper.backup
fi

if [ -f "gradlew" ]; then
    echo "📦 Backing up existing gradlew script"
    mv gradlew gradlew.backup
fi

if [ -f "gradlew.bat" ]; then
    echo "📦 Backing up existing gradlew.bat script"
    mv gradlew.bat gradlew.bat.backup
fi

# Generate new wrapper
echo "🔄 Generating new Gradle wrapper..."
gradle wrapper --gradle-version 8.5

# Make gradlew executable
chmod +x ./gradlew

# Test the new wrapper
echo "🧪 Testing new Gradle wrapper..."
if ./gradlew --version >/dev/null 2>&1; then
    echo "✅ Gradle wrapper fixed successfully!"
    echo ""
    echo "Gradle wrapper details:"
    ./gradlew --version | head -n 3
    echo ""
    
    # Clean up backups
    if [ -d "gradle/wrapper.backup" ]; then
        echo "🗑️  Removing backup files..."
        rm -rf gradle/wrapper.backup
    fi
    if [ -f "gradlew.backup" ]; then
        rm -f gradlew.backup
    fi
    if [ -f "gradlew.bat.backup" ]; then
        rm -f gradlew.bat.backup
    fi
    
    echo "✅ Gradle wrapper is now working correctly"
    echo ""
    echo "To prevent this issue in the future:"
    echo "  - Ensure your .gitattributes file includes: *.jar binary"
    echo "  - Use 'git config core.autocrlf false' on Windows"
    echo "  - Avoid editing binary files with text editors"
    
else
    echo "❌ Failed to fix Gradle wrapper"
    echo ""
    echo "Restoring backup files..."
    
    # Restore backups
    if [ -d "gradle/wrapper.backup" ]; then
        rm -rf gradle/wrapper
        mv gradle/wrapper.backup gradle/wrapper
    fi
    if [ -f "gradlew.backup" ]; then
        rm -f gradlew
        mv gradlew.backup gradlew
    fi
    if [ -f "gradlew.bat.backup" ]; then
        rm -f gradlew.bat
        mv gradlew.bat.backup gradlew.bat
    fi
    
    echo "❌ Could not fix the Gradle wrapper automatically"
    echo "Please check your Java installation and network connectivity"
    exit 1
fi

echo ""
echo "🎉 Gradle wrapper fix completed successfully!"
echo "You can now run: ./gradlew build"