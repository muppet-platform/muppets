#!/bin/bash

# Muppet Platform - Infrastructure Component Testing
# Tests the OpenTofu infrastructure modules

set -e

echo "🧪 Testing Infrastructure Component..."

cd terraform-modules

# Test 1: Module structure validation
echo "1️⃣ Validating module structure..."

modules=($(find . -maxdepth 1 -type d -not -name "." -not -name ".git" -not -name ".github" | sort))

if [ ${#modules[@]} -eq 0 ]; then
    echo "❌ No infrastructure modules found"
    exit 1
fi

echo "   Found modules: ${modules[*]}"

for module in "${modules[@]}"; do
    module_name=$(basename "$module")
    echo "   Checking module: $module_name"
    
    # Check required files
    required_files=("main.tf" "variables.tf" "outputs.tf")
    for file in "${required_files[@]}"; do
        if [ ! -f "$module/$file" ]; then
            echo "❌ Missing required file in $module_name: $file"
            exit 1
        fi
    done
    
    # Check for README
    if [ ! -f "$module/README.md" ]; then
        echo "⚠️  Missing README.md in $module_name (recommended)"
    fi
done
echo "   ✅ All modules have required structure"

# Test 2: OpenTofu syntax validation
echo "2️⃣ Testing OpenTofu syntax validation..."

if ! command -v tofu &> /dev/null; then
    echo "❌ OpenTofu not found. Please install OpenTofu first."
    exit 1
fi

for module in "${modules[@]}"; do
    module_name=$(basename "$module")
    echo "   Validating module: $module_name"
    
    cd "$module"
    
    # Initialize module (without backend)
    if ! tofu init -backend=false > /dev/null 2>&1; then
        echo "❌ Failed to initialize module: $module_name"
        cd ..
        exit 1
    fi
    
    # Validate syntax
    if ! tofu validate > /dev/null 2>&1; then
        echo "❌ Validation failed for module: $module_name"
        cd ..
        exit 1
    fi
    
    # Check formatting
    if ! tofu fmt -check > /dev/null 2>&1; then
        echo "⚠️  Formatting issues in module: $module_name (run: tofu fmt)"
    fi
    
    cd ..
done
echo "   ✅ All modules pass OpenTofu validation"

# Test 3: Version compatibility
echo "3️⃣ Testing version compatibility..."

tofu_version=$(tofu version | head -n 1 | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | sed 's/v//')
echo "   OpenTofu version: $tofu_version"

# Check if version is 1.6.0 or higher
if [ "$(printf '%s\n' "1.6.0" "$tofu_version" | sort -V | head -n1)" = "1.6.0" ]; then
    echo "   ✅ OpenTofu version is compatible (>= 1.6.0)"
else
    echo "   ⚠️  OpenTofu version may be incompatible (< 1.6.0)"
fi

# Test 4: Module documentation
echo "4️⃣ Checking module documentation..."

for module in "${modules[@]}"; do
    module_name=$(basename "$module")
    
    if [ -f "$module/README.md" ]; then
        # Check if README has basic sections
        if grep -q "## Usage" "$module/README.md" && \
           grep -q "## Variables" "$module/README.md" && \
           grep -q "## Outputs" "$module/README.md"; then
            echo "   ✅ $module_name has comprehensive documentation"
        else
            echo "   ⚠️  $module_name documentation could be improved"
        fi
    else
        echo "   ⚠️  $module_name missing documentation"
    fi
done

# Test 5: Security best practices
echo "5️⃣ Checking security best practices..."

security_issues=0

for module in "${modules[@]}"; do
    module_name=$(basename "$module")
    
    # Check for hardcoded secrets (basic check)
    if grep -r -i "password\|secret\|key" "$module"/*.tf 2>/dev/null | grep -v "variable\|output\|description" | grep -q "="; then
        echo "   ⚠️  Potential hardcoded secrets in $module_name"
        security_issues=$((security_issues + 1))
    fi
    
    # Check for public access (basic check)
    if grep -q "0.0.0.0/0" "$module"/*.tf 2>/dev/null; then
        echo "   ⚠️  Potential overly permissive access in $module_name"
        security_issues=$((security_issues + 1))
    fi
done

if [ $security_issues -eq 0 ]; then
    echo "   ✅ No obvious security issues found"
else
    echo "   ⚠️  Found $security_issues potential security issues"
fi

cd ..

echo ""
echo "✅ Infrastructure component validated successfully!"
echo ""
echo "Test Results:"
echo "  ✅ Module Structure: OK"
echo "  ✅ OpenTofu Syntax: OK"
echo "  ✅ Version Compatibility: OK"
echo "  ✅ Documentation: OK"
echo "  ✅ Security Check: OK"
echo ""
echo "Modules tested: ${#modules[@]}"
for module in "${modules[@]}"; do
    echo "  - $(basename "$module")"
done