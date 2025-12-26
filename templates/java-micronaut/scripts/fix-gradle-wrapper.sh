#!/bin/bash

# {{muppet_name}} - Fix Gradle Wrapper Script
# This script fixes corrupted Gradle wrapper files, commonly caused by Git binary file issues

set -e

# Parse command line arguments
NUCLEAR_OPTION=false
if [ "$1" = "--nuclear" ] || [ "$1" = "-n" ]; then
    NUCLEAR_OPTION=true
    echo "💥 NUCLEAR OPTION ACTIVATED - Complete reset to template state"
    echo "⚠️  This will overwrite ALL template files with fresh versions"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Nuclear option cancelled"
        exit 1
    fi
    echo ""
fi

if [ "$NUCLEAR_OPTION" = true ]; then
    echo "💥 Executing nuclear option - complete template reset..."
else
    echo "🔧 Fixing Gradle wrapper for {{muppet_name}}..."
fi

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
gradle --version
echo ""

# Nuclear option: Complete reset to template state
if [ "$NUCLEAR_OPTION" = true ]; then
    echo "💥 NUCLEAR OPTION: Resetting to fresh template state..."
    
    # Get muppet name from directory
    MUPPET_NAME=$(basename "$(pwd)")
    
    # Create backup directory with timestamp
    BACKUP_DIR="nuclear-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    echo "📦 Creating complete backup in $BACKUP_DIR..."
    
    # Backup everything that will be replaced
    [ -f "build.gradle" ] && cp "build.gradle" "$BACKUP_DIR/"
    [ -f "gradle.properties" ] && cp "gradle.properties" "$BACKUP_DIR/"
    [ -f "settings.gradle" ] && cp "settings.gradle" "$BACKUP_DIR/"
    [ -d "gradle" ] && cp -r "gradle" "$BACKUP_DIR/"
    [ -f "gradlew" ] && cp "gradlew" "$BACKUP_DIR/"
    [ -f "gradlew.bat" ] && cp "gradlew.bat" "$BACKUP_DIR/"
    [ -f ".gitattributes" ] && cp ".gitattributes" "$BACKUP_DIR/"
    [ -d "scripts" ] && cp -r "scripts" "$BACKUP_DIR/"
    
    echo "🗑️  Removing corrupted files..."
    rm -rf gradle gradlew gradlew.bat .gradle build
    
    echo "📝 Creating fresh build.gradle..."
    cat > build.gradle << EOF
plugins {
    id 'com.github.johnrengelman.shadow' version '7.1.2'
    id 'io.micronaut.application' version '4.4.4'
    id 'jacoco'
}

version = "1.0.0"
group = "com.muppetplatform.${MUPPET_NAME}"

repositories {
    mavenCentral()
}

dependencies {
    // Micronaut Core
    implementation 'io.micronaut:micronaut-http-client'
    implementation 'io.micronaut:micronaut-http-server-netty'
    implementation 'io.micronaut:micronaut-jackson-databind'
    implementation 'io.micronaut.validation:micronaut-validation'
    
    // YAML Configuration
    runtimeOnly 'org.yaml:snakeyaml'
    
    // Metrics and Monitoring
    implementation 'io.micronaut.micrometer:micronaut-micrometer-core'
    implementation 'io.micronaut.micrometer:micronaut-micrometer-registry-cloudwatch'
    
    // Logging
    implementation 'ch.qos.logback:logback-classic'
    implementation 'net.logstash.logback:logstash-logback-encoder:7.4'
    implementation 'ca.pjer:logback-awslogs-appender:1.6.0'
    
    // AWS SDK
    implementation 'software.amazon.awssdk:cloudwatch:2.21.29'
    
    // Testing
    testImplementation 'io.micronaut:micronaut-http-client'
    testImplementation 'io.micronaut.test:micronaut-test-junit5'
    testImplementation 'org.junit.jupiter:junit-jupiter-api'
    testImplementation 'org.junit.jupiter:junit-jupiter-engine'
    testImplementation 'org.mockito:mockito-core'
    
    // Annotation Processing
    annotationProcessor 'io.micronaut:micronaut-http-validation'
    annotationProcessor 'io.micronaut.validation:micronaut-validation-processor'
}

application {
    mainClass = 'com.muppetplatform.${MUPPET_NAME}.Application'
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

micronaut {
    runtime 'netty'
    testRuntime 'junit5'
    processing {
        incremental true
        annotations 'com.muppetplatform.${MUPPET_NAME}.*'
    }
}

tasks.named("test") {
    useJUnitPlatform()
    testLogging {
        events "passed", "skipped", "failed"
    }
}

tasks.named("shadowJar") {
    mergeServiceFiles()
}

jacoco {
    toolVersion = "0.8.8"
}

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        html.required = true
    }
    finalizedBy jacocoTestCoverageVerification
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = 0.80
            }
        }
    }
}

test.finalizedBy jacocoTestReport
EOF

    echo "📝 Creating fresh gradle.properties..."
    cat > gradle.properties << 'EOF'
micronautVersion=4.4.4
EOF

    echo "📝 Creating fresh settings.gradle..."
    cat > settings.gradle << EOF
rootProject.name = "${MUPPET_NAME}"
EOF

    echo "📝 Creating fresh .gitattributes..."
    cat > .gitattributes << 'EOF'
# Prevent Git from corrupting binary files
*.jar binary
*.zip binary
*.tar.gz binary
*.tgz binary
*.war binary
*.ear binary
*.class binary

# Gradle wrapper files are binary
gradle/wrapper/gradle-wrapper.jar binary
gradle/wrapper/gradle-wrapper.properties text eol=lf

# Shell scripts should have LF line endings
*.sh text eol=lf
gradlew text eol=lf

# Batch files should have CRLF line endings
*.bat text eol=crlf
gradlew.bat text eol=crlf
EOF

    echo "🔄 Generating fresh Gradle wrapper..."
    gradle wrapper --gradle-version 8.10.2 --distribution-type bin
    chmod +x ./gradlew
    
    echo "🧪 Testing nuclear reset..."
    if ./gradlew --version >/dev/null 2>&1; then
        echo "✅ Nuclear reset successful!"
        echo ""
        echo "Gradle wrapper details:"
        ./gradlew --version | head -n 3
        echo ""
        
        # Test build configuration
        if ./gradlew tasks --quiet >/dev/null 2>&1; then
            echo "✅ Build configuration is valid"
        else
            echo "⚠️  Build configuration may have issues"
        fi
        
        echo ""
        echo "💥 Nuclear option completed successfully!"
        echo "📦 Backup created in: $BACKUP_DIR"
        echo "🎉 Your muppet has been reset to a fresh template state"
        echo ""
        echo "You can now run: ./gradlew build"
        exit 0
    else
        echo "❌ Nuclear reset failed!"
        echo "📦 Restoring from backup..."
        
        # Restore from backup
        cp -r "$BACKUP_DIR"/* ./ 2>/dev/null || true
        
        echo "❌ Nuclear option failed, backup restored"
        exit 1
    fi
fi

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

# Check if build.gradle is compatible
echo "🔍 Checking build.gradle compatibility..."
if ! gradle tasks --quiet >/dev/null 2>&1; then
    echo "⚠️  build.gradle appears to be incompatible with current Gradle version"
    echo "📝 Temporarily replacing build.gradle with minimal version for wrapper generation..."
    
    # Backup the current build.gradle
    cp build.gradle build.gradle.original
    
    # Create minimal build.gradle for wrapper generation
    cat > build.gradle << 'EOF'
plugins {
    id 'java'
}

repositories {
    mavenCentral()
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}
EOF
fi

# Generate new wrapper
echo "🔄 Generating new Gradle wrapper..."
if ! gradle wrapper --gradle-version 8.10.2 --distribution-type bin; then
    echo "❌ Failed to generate Gradle wrapper"
    echo ""
    echo "Debugging information:"
    echo "- Current directory: $(pwd)"
    echo "- Java version: $(java -version 2>&1 | head -n 1)"
    echo "- Gradle version: $(gradle --version | head -n 1)"
    echo ""
    echo "Common causes:"
    echo "1. Network connectivity issues downloading Gradle"
    echo "2. Java version incompatibility"
    echo "3. Corrupted Gradle installation"
    echo "4. Permission issues"
    echo ""
    
    # Restore original build.gradle if we modified it
    if [ -f "build.gradle.original" ]; then
        echo "📝 Restoring original build.gradle..."
        mv build.gradle.original build.gradle
    fi
    
    exit 1
fi

# Restore original build.gradle if we modified it
if [ -f "build.gradle.original" ]; then
    echo "📝 Restoring original build.gradle..."
    mv build.gradle.original build.gradle
fi

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
    
    # Check if build.gradle needs updating
    if [ -f "build.gradle.original" ]; then
        echo "🔄 Updating build.gradle to current template version..."
        
        # Get muppet name from directory or use default
        MUPPET_NAME=$(basename "$(pwd)")
        
        # Create updated build.gradle with current template
        cat > build.gradle << EOF
plugins {
    id 'com.github.johnrengelman.shadow' version '7.1.2'
    id 'io.micronaut.application' version '4.4.4'
    id 'jacoco'
}

version = "1.0.0"
group = "com.muppetplatform.\${MUPPET_NAME}"

repositories {
    mavenCentral()
}

dependencies {
    // Micronaut Core
    implementation 'io.micronaut:micronaut-http-client'
    implementation 'io.micronaut:micronaut-http-server-netty'
    implementation 'io.micronaut:micronaut-jackson-databind'
    implementation 'io.micronaut.validation:micronaut-validation'
    
    // YAML Configuration
    runtimeOnly 'org.yaml:snakeyaml'
    
    // Metrics and Monitoring
    implementation 'io.micronaut.micrometer:micronaut-micrometer-core'
    implementation 'io.micronaut.micrometer:micronaut-micrometer-registry-cloudwatch'
    
    // Logging
    implementation 'ch.qos.logback:logback-classic'
    implementation 'net.logstash.logback:logstash-logback-encoder:7.4'
    implementation 'ca.pjer:logback-awslogs-appender:1.6.0'
    
    // AWS SDK
    implementation 'software.amazon.awssdk:cloudwatch:2.21.29'
    
    // Testing
    testImplementation 'io.micronaut:micronaut-http-client'
    testImplementation 'io.micronaut.test:micronaut-test-junit5'
    testImplementation 'org.junit.jupiter:junit-jupiter-api'
    testImplementation 'org.junit.jupiter:junit-jupiter-engine'
    testImplementation 'org.mockito:mockito-core'
    
    // Annotation Processing
    annotationProcessor 'io.micronaut:micronaut-http-validation'
    annotationProcessor 'io.micronaut.validation:micronaut-validation-processor'
}

application {
    mainClass = 'com.muppetplatform.\${MUPPET_NAME}.Application'
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

micronaut {
    runtime 'netty'
    testRuntime 'junit5'
    processing {
        incremental true
        annotations 'com.muppetplatform.\${MUPPET_NAME}.*'
    }
}

tasks.named("test") {
    useJUnitPlatform()
    testLogging {
        events "passed", "skipped", "failed"
    }
}

tasks.named("shadowJar") {
    mergeServiceFiles()
}

jacoco {
    toolVersion = "0.8.8"
}

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        html.required = true
    }
    finalizedBy jacocoTestCoverageVerification
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = 0.80
            }
        }
    }
}

test.finalizedBy jacocoTestReport
EOF
        
        echo "✅ Updated build.gradle to current template version"
        rm -f build.gradle.original
    fi
    
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
    
    # Test that the build configuration works
    echo "🧪 Testing build configuration..."
    if ./gradlew tasks --quiet >/dev/null 2>&1; then
        echo "✅ Build configuration is valid"
    else
        echo "⚠️  Build configuration may have issues, but wrapper is functional"
    fi
    
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
echo ""
echo "💡 Tip: If you continue having issues, try the nuclear option:"
echo "   bash scripts/fix-gradle-wrapper.sh --nuclear"
echo "   This will reset your muppet to a fresh template state"