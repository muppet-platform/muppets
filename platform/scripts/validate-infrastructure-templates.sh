#!/bin/bash
# Validate all infrastructure templates
# This script ensures templates are syntactically correct and can generate valid OpenTofu

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$PLATFORM_DIR/infrastructure-templates"
TEMP_DIR="/tmp/muppet-platform-template-validation"

echo "🔍 Validating Infrastructure Templates"
echo "Templates directory: $TEMPLATES_DIR"

# Check if templates directory exists
if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "❌ Templates directory not found: $TEMPLATES_DIR"
    exit 1
fi

# Check if OpenTofu is installed
if ! command -v tofu &> /dev/null; then
    echo "❌ OpenTofu not found. Please install OpenTofu 1.6+"
    echo "   Installation: https://opentofu.org/docs/intro/install/"
    exit 1
fi

echo "✅ OpenTofu found: $(tofu version | head -n1)"

# Clean up any previous validation
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Function to validate a template set
validate_template_set() {
    local language=$1
    local test_dir="$TEMP_DIR/$language"
    
    echo ""
    echo "🧪 Testing $language templates..."
    
    mkdir -p "$test_dir"
    
    # Generate test infrastructure using Python template processor
    cd "$PLATFORM_DIR"
    
    python3 -c "
import sys
sys.path.append('.')
from src.managers.infrastructure_template_processor import InfrastructureTemplateProcessor
from pathlib import Path

processor = InfrastructureTemplateProcessor()

# Test metadata
template_metadata = {
    'name': 'test-template',
    'version': '1.0.0',
    'description': 'Test template',
    'language': '$language',
    'framework': 'test-framework',
    'port': 3000,
    'java_version': '21',
    'java_distribution': 'amazon-corretto',
    'framework_version': '4.0.4',
    'build_tool': 'gradle',
    'features': ['health_checks', 'metrics']
}

# Test variables
variables = {
    'aws_region': 'us-west-2',
    'environment': 'development'
}

try:
    processor.generate_infrastructure(
        template_metadata,
        'test-muppet',
        Path('$test_dir'),
        variables
    )
    print('✅ Template generation successful')
except Exception as e:
    print(f'❌ Template generation failed: {e}')
    sys.exit(1)
"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate $language templates"
        return 1
    fi
    
    # Validate generated OpenTofu
    cd "$test_dir/terraform"
    
    if [ ! -f "main.tf" ]; then
        echo "❌ main.tf not generated for $language"
        return 1
    fi
    
    echo "📋 Generated files:"
    ls -la
    
    # Initialize OpenTofu (this validates provider configuration)
    echo "🔧 Initializing OpenTofu..."
    if ! tofu init -backend=false > /dev/null 2>&1; then
        echo "❌ OpenTofu init failed for $language"
        echo "OpenTofu init output:"
        tofu init -backend=false
        return 1
    fi
    
    # Validate OpenTofu syntax
    echo "✅ Validating OpenTofu syntax..."
    if ! tofu validate > /dev/null 2>&1; then
        echo "❌ OpenTofu validation failed for $language"
        echo "OpenTofu validation output:"
        tofu validate
        return 1
    fi
    
    # Check formatting
    echo "📝 Checking OpenTofu formatting..."
    if ! tofu fmt -check > /dev/null 2>&1; then
        echo "⚠️  OpenTofu formatting issues found for $language"
        echo "Run 'tofu fmt' to fix formatting"
        # Don't fail on formatting issues, just warn
    fi
    
    echo "✅ $language templates validated successfully"
    return 0
}

# Validate each language template set
languages=("java")  # Add more languages as templates are created
failed_validations=0

for lang in "${languages[@]}"; do
    if ! validate_template_set "$lang"; then
        failed_validations=$((failed_validations + 1))
    fi
done

# Clean up
echo ""
echo "🧹 Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Summary
echo ""
echo "📊 Validation Summary:"
if [ $failed_validations -eq 0 ]; then
    echo "✅ All template validations passed!"
    echo "🎉 Infrastructure templates are ready for use"
else
    echo "❌ $failed_validations template validation(s) failed"
    echo "🔧 Please fix the issues above before using templates"
    exit 1
fi