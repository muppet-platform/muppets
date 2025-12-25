#!/bin/bash

# Quick Template Verification Script
# Performs basic verification of template functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚡ Quick Java Micronaut Template Verification${NC}"
echo "============================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists java; then
    echo -e "${RED}❌ Java not found${NC}"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 21 ]; then
    echo -e "${RED}❌ Java 21+ required, found Java $JAVA_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Java $JAVA_VERSION${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Check template structure
echo -e "${BLUE}📁 Checking template structure...${NC}"

required_files=(
    "src/main/java/com/muppetplatform/{{muppet_name}}/Application.java"
    "src/main/java/com/muppetplatform/{{muppet_name}}/controller/HealthController.java"
    "src/main/java/com/muppetplatform/{{muppet_name}}/controller/ApiController.java"
    "build.gradle.template"
    "Dockerfile.template"
    "template.yaml"
    "scripts/init.sh"
    "scripts/build.sh"
    "scripts/run.sh"
    "scripts/test.sh"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        exit 1
    fi
done

# Check template configuration
echo -e "${BLUE}⚙️  Checking template configuration...${NC}"

if grep -q "java_version.*21" template.yaml; then
    echo -e "${GREEN}✅ Java 21 configured in template.yaml${NC}"
else
    echo -e "${RED}❌ Java 21 not configured in template.yaml${NC}"
    exit 1
fi

if grep -q "port.*3000" template.yaml; then
    echo -e "${GREEN}✅ Port 3000 configured in template.yaml${NC}"
else
    echo -e "${RED}❌ Port 3000 not configured in template.yaml${NC}"
    exit 1
fi

if grep -q "amazoncorretto:21" Dockerfile.template; then
    echo -e "${GREEN}✅ Amazon Corretto 21 in Dockerfile template${NC}"
else
    echo -e "${RED}❌ Amazon Corretto 21 not in Dockerfile template${NC}"
    exit 1
fi

if grep -q "JavaVersion.VERSION_21" build.gradle.template; then
    echo -e "${GREEN}✅ Java 21 in build.gradle template${NC}"
else
    echo -e "${RED}❌ Java 21 not in build.gradle template${NC}"
    exit 1
fi

# Check script permissions and syntax
echo -e "${BLUE}📜 Checking scripts...${NC}"

scripts=("init.sh" "build.sh" "run.sh" "test.sh")
for script in "${scripts[@]}"; do
    if [ -f "scripts/$script" ]; then
        # Check if script has shebang
        if head -n 1 "scripts/$script" | grep -q "#!/bin/bash"; then
            echo -e "${GREEN}✅ scripts/$script has proper shebang${NC}"
        else
            echo -e "${RED}❌ scripts/$script missing shebang${NC}"
            exit 1
        fi
        
        # Basic syntax check
        if bash -n "scripts/$script"; then
            echo -e "${GREEN}✅ scripts/$script syntax OK${NC}"
        else
            echo -e "${RED}❌ scripts/$script syntax error${NC}"
            exit 1
        fi
    fi
done

# Check Java source files for template variables
echo -e "${BLUE}☕ Checking Java source files...${NC}"

java_files=(
    "src/main/java/com/muppetplatform/{{muppet_name}}/Application.java"
    "src/main/java/com/muppetplatform/{{muppet_name}}/controller/HealthController.java"
    "src/main/java/com/muppetplatform/{{muppet_name}}/controller/ApiController.java"
)

for java_file in "${java_files[@]}"; do
    if [ -f "$java_file" ]; then
        if grep -q "{{muppet_name}}" "$java_file"; then
            echo -e "${GREEN}✅ $java_file contains template variables${NC}"
        else
            echo -e "${RED}❌ $java_file missing template variables${NC}"
            exit 1
        fi
        
        # Basic Java syntax check (without compilation)
        if grep -q "package com.muppetplatform.{{muppet_name}}" "$java_file"; then
            echo -e "${GREEN}✅ $java_file has correct package structure${NC}"
        else
            echo -e "${RED}❌ $java_file incorrect package structure${NC}"
            exit 1
        fi
    fi
done

# Check health endpoints
echo -e "${BLUE}🏥 Checking health endpoint implementation...${NC}"

health_controller="src/main/java/com/muppetplatform/{{muppet_name}}/controller/HealthController.java"
if grep -q "@Get" "$health_controller" && grep -q "/ready" "$health_controller" && grep -q "/live" "$health_controller"; then
    echo -e "${GREEN}✅ Health endpoints implemented${NC}"
else
    echo -e "${RED}❌ Health endpoints missing or incomplete${NC}"
    exit 1
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 Quick Verification Complete!${NC}"
echo "================================"
echo -e "${GREEN}✅ Prerequisites available${NC}"
echo -e "${GREEN}✅ Template structure valid${NC}"
echo -e "${GREEN}✅ Configuration correct${NC}"
echo -e "${GREEN}✅ Scripts properly formatted${NC}"
echo -e "${GREEN}✅ Java source files valid${NC}"
echo -e "${GREEN}✅ Health endpoints implemented${NC}"
echo ""
echo "Template is ready for full verification with verify-template.sh"
echo ""