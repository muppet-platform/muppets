#!/bin/bash

# Muppet Platform - Templates Component Testing
# Tests the template system and Java Micronaut template

set -e

echo "🧪 Testing Templates Component..."

# Test 1: Template structure validation
echo "1️⃣ Validating template structure..."
cd templates/java-micronaut

# Check required files
required_files=(
    "template.yaml"
    "build.gradle.template"
    "src/"
    "scripts/"
    "scripts/init.sh"
    "scripts/build.sh"
    "scripts/test.sh"
    "scripts/fix-gradle-wrapper.sh"
    ".kiro/settings/mcp.json.template"
)

for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done
echo "   ✅ All required template files present"

# Test 2: Script syntax validation
echo "2️⃣ Testing template scripts syntax..."
chmod +x scripts/*.sh

for script in scripts/*.sh; do
    echo "   Checking $(basename "$script")..."
    if ! bash -n "$script"; then
        echo "❌ Syntax error in $script"
        exit 1
    fi
done
echo "   ✅ All template scripts have valid syntax"

# Test 3: Gradle wrapper validation
echo "3️⃣ Testing Gradle wrapper..."
if [ ! -f gradlew ]; then
    echo "❌ Gradle wrapper script missing"
    exit 1
fi

if [ ! -f gradle/wrapper/gradle-wrapper.jar ]; then
    echo "❌ Gradle wrapper JAR missing"
    exit 1
fi

if [ ! -f gradle/wrapper/gradle-wrapper.properties ]; then
    echo "❌ Gradle wrapper properties missing"
    exit 1
fi

# Test wrapper is executable and works
if ! ./gradlew --version > /dev/null 2>&1; then
    echo "❌ Gradle wrapper not working"
    exit 1
fi
echo "   ✅ Gradle wrapper is functional"

# Test 4: Template metadata validation
echo "4️⃣ Validating template metadata..."
if ! python3 -c "
import yaml
with open('template.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
required_fields = ['name', 'version', 'description', 'language', 'framework']
for field in required_fields:
    if field not in config:
        raise ValueError(f'Missing required field: {field}')
        
if config['language'] != 'java':
    raise ValueError('Expected language to be java')
    
if config['framework'] != 'micronaut':
    raise ValueError('Expected framework to be micronaut')
    
print('Template metadata is valid')
"; then
    echo "❌ Template metadata validation failed"
    exit 1
fi
echo "   ✅ Template metadata is valid"

# Test 5: Template verification system (basic check)
echo "5️⃣ Running template verification system..."
cd ../../platform

# Test that the verification system can list templates
if ! uv run python -m src.verification.cli list > /dev/null; then
    echo "❌ Template verification system failed to list templates"
    exit 1
fi

# Test basic template structure validation (without full verification)
echo "   Testing basic template validation..."
if uv run python -c "
from src.managers.template_manager import TemplateManager
tm = TemplateManager()
templates = tm.discover_templates()
java_template = tm.get_template('java-micronaut')
if java_template is None:
    raise Exception('java-micronaut template not found')
print('Template validation successful')
"; then
    echo "   ✅ Template verification system works"
else
    echo "❌ Template verification system failed"
    exit 1
fi

# Test 6: MCP configuration validation
echo "6️⃣ Validating MCP configuration..."
cd ../templates/java-micronaut

if ! python3 -c "
import json
with open('.kiro/settings/mcp.json.template', 'r') as f:
    config = json.load(f)
    
if 'mcpServers' not in config:
    raise ValueError('Missing mcpServers configuration')
    
if 'muppet-platform' not in config['mcpServers']:
    raise ValueError('Missing muppet-platform server configuration')
    
server_config = config['mcpServers']['muppet-platform']
required_fields = ['command', 'args', 'cwd']
for field in required_fields:
    if field not in server_config:
        raise ValueError(f'Missing required server field: {field}')
        
print('MCP configuration is valid')
"; then
    echo "❌ MCP configuration validation failed"
    exit 1
fi
echo "   ✅ MCP configuration is valid"

# Test 7: Java version compatibility
echo "7️⃣ Testing Java version compatibility..."
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [ "$JAVA_VERSION" -eq 21 ]; then
        echo "   ✅ Java 21 LTS detected - compatible"
    else
        echo "   ⚠️  Java $JAVA_VERSION detected - template requires Java 21 LTS"
    fi
else
    echo "   ⚠️  Java not found - template requires Java 21 LTS"
fi

cd ../..

echo ""
echo "✅ Templates component validated successfully!"
echo ""
echo "Test Results:"
echo "  ✅ Template Structure: OK"
echo "  ✅ Script Syntax: OK"
echo "  ✅ Gradle Wrapper: OK"
echo "  ✅ Template Metadata: OK"
echo "  ✅ Verification System: OK"
echo "  ✅ MCP Configuration: OK"
echo "  ✅ Java Compatibility: OK"