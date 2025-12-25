#!/bin/bash

# verify-java-micronaut-1766586224 Muppet - Local Development Environment Setup
# This script sets up the local development environment including Rancher Desktop

set -e

echo "🚀 Setting up local development environment for verify-java-micronaut-1766586224..."

# Check if this is being run in a template directory vs generated muppet
if [ -f "build.gradle.template" ] || [ -f "settings.gradle.template" ]; then
    echo "❌ ERROR: This script is being run in the template directory!"
    echo ""
    echo "This init script should only be run in a generated muppet, not in the template itself."
    echo ""
    echo "To create a muppet from this template:"
    echo "  1. Use the Platform API: POST /api/v1/muppets/"
    echo "  2. Or use the verification CLI: python -m src.verification.cli verify java-micronaut"
    echo ""
    echo "The init script will be automatically available in the generated muppet directory."
    exit 1
fi

# Verify we're in a generated muppet (should have build.gradle, not build.gradle.template)
if [ ! -f "build.gradle" ] || [ ! -f "settings.gradle" ]; then
    echo "❌ ERROR: Missing Gradle build files!"
    echo ""
    echo "This directory doesn't appear to be a properly generated muppet."
    echo "Expected files: build.gradle, settings.gradle"
    echo ""
    echo "Please ensure you're running this script in a generated muppet directory."
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

OS=$(detect_os)
echo "📋 Detected OS: $OS"

# Check for Java 21 LTS (Amazon Corretto preferred)
echo "☕ Checking Java installation..."
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    
    # Check for exact Java 21 LTS
    if [ "$JAVA_VERSION" -eq 21 ]; then
        # Verify it's LTS
        if java -version 2>&1 | grep -q "21.*LTS"; then
            echo "✅ Java 21 LTS found"
            
            # Check if JAVA_HOME is set correctly
            if [ -n "$JAVA_HOME" ]; then
                echo "✅ JAVA_HOME is set: $JAVA_HOME"
            else
                echo "⚠️  JAVA_HOME not set"
                echo "Please set JAVA_HOME and update PATH:"
                case $OS in
                    macos)
                        echo "  export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home"
                        echo "  export PATH=\$JAVA_HOME/bin:\$PATH"
                        echo ""
                        echo "Add these lines to your ~/.zshrc or ~/.bash_profile:"
                        echo "  echo 'export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home' >> ~/.zshrc"
                        echo "  echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.zshrc"
                        echo "  source ~/.zshrc"
                        ;;
                    linux)
                        echo "  export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto"
                        echo "  export PATH=\$JAVA_HOME/bin:\$PATH"
                        echo ""
                        echo "Add these lines to your ~/.bashrc or ~/.profile:"
                        echo "  echo 'export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto' >> ~/.bashrc"
                        echo "  echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.bashrc"
                        echo "  source ~/.bashrc"
                        ;;
                    windows)
                        echo "  Set JAVA_HOME to C:\\Program Files\\Amazon Corretto\\jdk21.x.x_xx"
                        echo "  Add %JAVA_HOME%\\bin to your PATH"
                        ;;
                esac
                echo ""
                echo "After setting JAVA_HOME and PATH, restart your terminal and run this script again."
            fi
        else
            echo "⚠️  Java 21 found but LTS not confirmed"
            echo "Please ensure you're using Amazon Corretto 21 LTS"
        fi
    elif [ "$JAVA_VERSION" -lt 21 ]; then
        echo "❌ Java 21 LTS required, found Java $JAVA_VERSION"
        echo "Please install Amazon Corretto 21 LTS: https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/downloads-list.html"
        case $OS in
            macos)
                echo "For macOS:"
                echo "  brew install --cask corretto21"
                echo ""
                echo "Then set JAVA_HOME and PATH:"
                echo "  export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home"
                echo "  export PATH=\$JAVA_HOME/bin:\$PATH"
                echo ""
                echo "Add to your shell profile:"
                echo "  echo 'export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home' >> ~/.zshrc"
                echo "  echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.zshrc"
                ;;
            linux)
                echo "For Linux:"
                echo "  Download from AWS Corretto downloads page"
                echo ""
                echo "Then set JAVA_HOME and PATH:"
                echo "  export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto"
                echo "  export PATH=\$JAVA_HOME/bin:\$PATH"
                echo ""
                echo "Add to your shell profile:"
                echo "  echo 'export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto' >> ~/.bashrc"
                echo "  echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.bashrc"
                ;;
        esac
        exit 1
    else
        echo "🚨 WARNING: Java $JAVA_VERSION detected (newer than Java 21 LTS)"
        echo "   Non-LTS Java versions (22, 23, 24, 25+) are not supported"
        echo "   This may cause build failures with Gradle plugins and Micronaut"
        echo "   Please downgrade to Java 21 LTS for stability"
        echo ""
        echo "To fix this:"
        case $OS in
            macos)
                echo "  1. Install Java 21 LTS: brew install --cask corretto21"
                echo "  2. Set JAVA_HOME: export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home"
                echo "  3. Update PATH: export PATH=\$JAVA_HOME/bin:\$PATH"
                echo "  4. Add to shell profile:"
                echo "     echo 'export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home' >> ~/.zshrc"
                echo "     echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.zshrc"
                ;;
            linux)
                echo "  1. Install Java 21 LTS from AWS Corretto downloads"
                echo "  2. Set JAVA_HOME: export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto"
                echo "  3. Update PATH: export PATH=\$JAVA_HOME/bin:\$PATH"
                echo "  4. Add to shell profile:"
                echo "     echo 'export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto' >> ~/.bashrc"
                echo "     echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.bashrc"
                ;;
        esac
        echo "  5. Restart your terminal and try again"
        exit 1
    fi
else
    echo "❌ Java not found"
    echo "Please install Amazon Corretto 21 LTS: https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/downloads-list.html"
    case $OS in
        macos)
            echo "For macOS:"
            echo "  brew install --cask corretto21"
            echo ""
            echo "Then set JAVA_HOME and PATH:"
            echo "  export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home"
            echo "  export PATH=\$JAVA_HOME/bin:\$PATH"
            echo ""
            echo "Add to your shell profile:"
            echo "  echo 'export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home' >> ~/.zshrc"
            echo "  echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.zshrc"
            echo "  source ~/.zshrc"
            ;;
        linux)
            echo "For Linux:"
            echo "  Download from AWS Corretto downloads page"
            echo ""
            echo "Then set JAVA_HOME and PATH:"
            echo "  export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto"
            echo "  export PATH=\$JAVA_HOME/bin:\$PATH"
            echo ""
            echo "Add to your shell profile:"
            echo "  echo 'export JAVA_HOME=/usr/lib/jvm/java-21-amazon-corretto' >> ~/.bashrc"
            echo "  echo 'export PATH=\$JAVA_HOME/bin:\$PATH' >> ~/.bashrc"
            echo "  source ~/.bashrc"
            ;;
        windows)
            echo "For Windows:"
            echo "  Download MSI installer from AWS"
            echo ""
            echo "Then set environment variables:"
            echo "  Set JAVA_HOME to C:\\Program Files\\Amazon Corretto\\jdk21.x.x_xx"
            echo "  Add %JAVA_HOME%\\bin to your PATH"
            ;;
    esac
    exit 1
fi

# Check for Docker/Rancher Desktop
echo "🐳 Checking Docker installation..."
if command_exists docker; then
    echo "✅ Docker found"
    if [ -z "$SKIP_DOCKER_CHECK" ] && ! docker info >/dev/null 2>&1; then
        echo "❌ Docker daemon not running"
        echo "Please start Docker or Rancher Desktop"
        exit 1
    fi
else
    echo "❌ Docker not found"
    echo "Please install Rancher Desktop: https://rancherdesktop.io/"
    case $OS in
        macos)
            echo "For macOS: brew install --cask rancher"
            ;;
        linux)
            echo "For Linux: Download from https://github.com/rancher-sandbox/rancher-desktop/releases"
            ;;
        windows)
            echo "For Windows: Download from https://github.com/rancher-sandbox/rancher-desktop/releases"
            ;;
    esac
    exit 1
fi

# Check for Docker Compose
echo "🐙 Checking Docker Compose..."
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    echo "✅ Docker Compose found"
else
    echo "❌ Docker Compose not found"
    echo "Please install Docker Compose or use Rancher Desktop which includes it"
    exit 1
fi

# Make scripts executable
echo "🔧 Setting up scripts..."
chmod +x scripts/*.sh

# Create local environment file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating local environment file..."
    cat > .env.local << EOF
# Local development environment variables for verify-java-micronaut-1766586224
MICRONAUT_ENVIRONMENTS=development
MUPPET_NAME=verify-java-micronaut-1766586224
AWS_REGION=us-east-1
ENVIRONMENT=development

# Local development ports
SERVER_PORT=3000

# Logging
LOG_LEVEL=DEBUG
EOF
    echo "✅ Created .env.local"
else
    echo "✅ .env.local already exists"
fi

# Test Gradle wrapper
echo "🏗️  Testing Gradle wrapper..."
if [ -f "./gradlew" ]; then
    chmod +x ./gradlew
    
    # Test if Gradle wrapper works
    echo "Testing Gradle wrapper..."
    if ./gradlew --version >/dev/null 2>&1; then
        echo "✅ Gradle wrapper ready"
        # Show Gradle version for confirmation
        ./gradlew --version | head -n 3
    else
        echo "❌ Gradle wrapper failed to execute"
        echo ""
        echo "This usually indicates one of these issues:"
        echo "  1. Corrupted gradle-wrapper.jar file"
        echo "  2. Missing or invalid gradle-wrapper.properties"
        echo "  3. Network connectivity issues downloading Gradle"
        echo "  4. Java version compatibility issues"
        echo ""
        echo "Attempting to diagnose the issue..."
        
        # Check if wrapper jar exists and is valid
        if [ -f "gradle/wrapper/gradle-wrapper.jar" ]; then
            echo "✅ gradle-wrapper.jar exists"
            if file gradle/wrapper/gradle-wrapper.jar | grep -q "Zip archive"; then
                echo "✅ gradle-wrapper.jar appears to be a valid ZIP archive"
            else
                echo "❌ gradle-wrapper.jar appears to be corrupted"
                echo "The file should be a ZIP archive but isn't recognized as one."
            fi
        else
            echo "❌ gradle-wrapper.jar is missing"
        fi
        
        # Check wrapper properties
        if [ -f "gradle/wrapper/gradle-wrapper.properties" ]; then
            echo "✅ gradle-wrapper.properties exists"
            echo "Gradle distribution URL: $(grep distributionUrl gradle/wrapper/gradle-wrapper.properties)"
        else
            echo "❌ gradle-wrapper.properties is missing"
        fi
        
        # Show the actual error
        echo ""
        echo "Gradle wrapper error output:"
        echo "----------------------------------------"
        ./gradlew --version 2>&1 || true
        echo "----------------------------------------"
        echo ""
        
        # Check if we have gradle installed globally to regenerate wrapper
        if command_exists gradle; then
            echo "🔧 Attempting to regenerate Gradle wrapper..."
            gradle wrapper --gradle-version 8.5
            chmod +x ./gradlew
            
            # Test again
            if ./gradlew --version >/dev/null 2>&1; then
                echo "✅ Gradle wrapper regenerated successfully"
            else
                echo "❌ Failed to regenerate Gradle wrapper"
                echo ""
                echo "Manual fix required:"
                echo "  1. Delete the gradle/wrapper directory: rm -rf gradle/wrapper"
                echo "  2. Regenerate wrapper: gradle wrapper --gradle-version 8.5"
                echo "  3. Make executable: chmod +x ./gradlew"
                echo "  4. Test: ./gradlew --version"
                exit 1
            fi
        else
            echo "❌ No global Gradle installation found to regenerate wrapper"
            echo ""
            echo "To fix this issue:"
            echo "  1. Install Gradle globally:"
            case $OS in
                macos)
                    echo "     brew install gradle"
                    ;;
                linux)
                    echo "     Download from https://gradle.org/install/"
                    echo "     Or: sudo apt install gradle (Ubuntu/Debian)"
                    ;;
                windows)
                    echo "     Download from https://gradle.org/install/"
                    echo "     Or: choco install gradle"
                    ;;
            esac
            echo "  2. Regenerate wrapper: gradle wrapper --gradle-version 8.5"
            echo "  3. Make executable: chmod +x ./gradlew"
            echo "  4. Test: ./gradlew --version"
            echo ""
            echo "Alternatively, you can copy the wrapper files from a working Gradle project."
            exit 1
        fi
    fi
else
    echo "❌ Gradle wrapper script (gradlew) not found"
    echo ""
    echo "This indicates the muppet was not generated properly from the template."
    echo "The gradlew script should be copied from the template during generation."
    echo ""
    if command_exists gradle; then
        echo "🔧 Creating Gradle wrapper..."
        gradle wrapper --gradle-version 8.5
        chmod +x ./gradlew
        echo "✅ Gradle wrapper created"
    else
        echo "Please install Gradle first to create the wrapper:"
        case $OS in
            macos)
                echo "  brew install gradle"
                ;;
            linux)
                echo "  Download from https://gradle.org/install/"
                echo "  Or: sudo apt install gradle (Ubuntu/Debian)"
                ;;
            windows)
                echo "  Download from https://gradle.org/install/"
                echo "  Or: choco install gradle"
                ;;
        esac
        echo ""
        echo "After installing Gradle, run:"
        echo "  gradle wrapper --gradle-version 8.5"
        echo "  chmod +x ./gradlew"
        exit 1
    fi
fi

echo ""
echo "🎉 Local development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run './scripts/build.sh' to build the application"
echo "  2. Run './scripts/test.sh' to run tests"
echo "  3. Run './scripts/run.sh' to start the application locally"
echo "  4. Visit http://localhost:3000/health to verify it's running"
echo ""