# Monorepo Migration Plan

## Overview

This plan outlines the systematic reorganization of the Muppet Platform into a modular monorepo structure, with component-by-component testing and commits.

## Current State Analysis

```
Current Structure:
├── .kiro/                    # Project Kiro config ✅
├── docs/                     # Project docs ✅
├── platform/                 # Platform service ✅
├── templates/                # Templates ✅
├── terraform-modules/        # Infrastructure ✅
├── steering-docs/            # Steering docs ✅
├── Makefile                  # Root makefile ✅
├── README.md                 # Project README ✅
└── muppet-platform.yaml     # Config file ✅
```

**Status**: Already well-organized! Minor adjustments needed.

## Migration Steps

### Phase 1: Repository Structure Optimization

#### Step 1.1: Create Missing Directories and Files
- [ ] Create `scripts/` directory for project-level scripts
- [ ] Create `.github/` directory for CI/CD workflows
- [ ] Add missing root-level files (CONTRIBUTING.md, CHANGELOG.md, etc.)
- [ ] Enhance existing documentation

#### Step 1.2: Reorganize Root Level Files
- [ ] Move project-level scripts to `scripts/`
- [ ] Ensure proper .gitignore and .gitattributes
- [ ] Create comprehensive root Makefile

### Phase 2: Component Testing and Validation

#### Step 2.1: Platform Service Component
**Directory**: `platform/`
**Test Strategy**:
1. Verify all existing tests pass
2. Test MCP server functionality
3. Test API endpoints
4. Validate Docker build
5. Check dependency management with UV

**Commit**: "feat: validate platform service component"

#### Step 2.2: Java Micronaut Template Component  
**Directory**: `templates/java-micronaut/`
**Test Strategy**:
1. Test template generation
2. Validate Gradle wrapper fixes
3. Test all scripts (init.sh, build.sh, test.sh, etc.)
4. Verify MCP configuration
5. Test verification system

**Commit**: "feat: validate java-micronaut template component"

#### Step 2.3: Infrastructure Modules Component
**Directory**: `terraform-modules/`
**Test Strategy**:
1. Validate OpenTofu module syntax
2. Test module initialization
3. Verify module documentation
4. Check version compatibility

**Commit**: "feat: validate infrastructure modules component"

#### Step 2.4: Steering Documentation Component
**Directory**: `steering-docs/`
**Test Strategy**:
1. Validate documentation structure
2. Test steering file distribution
3. Verify template integration
4. Check documentation completeness

**Commit**: "feat: validate steering documentation component"

### Phase 3: Integration and CI/CD Setup

#### Step 3.1: GitHub Actions Workflows
- [ ] Create component-specific CI workflows
- [ ] Set up cross-component integration tests
- [ ] Configure security scanning
- [ ] Set up automated releases

#### Step 3.2: Project-Level Integration
- [ ] Create root-level build scripts
- [ ] Set up cross-component testing
- [ ] Configure project-wide linting
- [ ] Set up documentation generation

## Detailed Implementation Plan

### Step 1: Create Missing Structure

```bash
# Create missing directories
mkdir -p scripts
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE

# Create project-level scripts
touch scripts/setup.sh
touch scripts/test-all.sh
touch scripts/build-all.sh
touch scripts/clean-all.sh

# Create GitHub templates
touch .github/ISSUE_TEMPLATE/bug_report.md
touch .github/ISSUE_TEMPLATE/feature_request.md
touch .github/pull_request_template.md

# Create missing documentation
touch CONTRIBUTING.md
touch CHANGELOG.md
touch LICENSE
```

### Step 2: Component Validation Scripts

#### Platform Service Validation
```bash
#!/bin/bash
# scripts/test-platform.sh

echo "🧪 Testing Platform Service Component..."

cd platform

# Test 1: Dependencies
echo "1️⃣ Testing dependencies..."
uv sync || exit 1

# Test 2: Unit tests
echo "2️⃣ Running unit tests..."
uv run pytest tests/ -v || exit 1

# Test 3: MCP server
echo "3️⃣ Testing MCP server..."
uv run mcp-server --help || exit 1

# Test 4: API server
echo "4️⃣ Testing API server startup..."
timeout 10s uv run uvicorn src.main:app --host 127.0.0.1 --port 8001 || echo "✅ Server startup test completed"

# Test 5: Docker build
echo "5️⃣ Testing Docker build..."
docker build -t muppet-platform-test . || exit 1
docker rmi muppet-platform-test

echo "✅ Platform service component validated!"
```

#### Template Validation
```bash
#!/bin/bash
# scripts/test-templates.sh

echo "🧪 Testing Templates Component..."

cd templates/java-micronaut

# Test 1: Template structure
echo "1️⃣ Validating template structure..."
[ -f template.yaml ] || exit 1
[ -f build.gradle.template ] || exit 1
[ -d src/ ] || exit 1
[ -d scripts/ ] || exit 1

# Test 2: Scripts execution
echo "2️⃣ Testing template scripts..."
chmod +x scripts/*.sh

# Test init script (dry run)
echo "Testing init script..."
bash -n scripts/init.sh || exit 1

# Test build script (syntax)
echo "Testing build script..."
bash -n scripts/build.sh || exit 1

# Test 3: Gradle wrapper
echo "3️⃣ Testing Gradle wrapper..."
[ -f gradlew ] || exit 1
[ -f gradle/wrapper/gradle-wrapper.jar ] || exit 1

# Test 4: Template verification
echo "4️⃣ Running template verification..."
cd ../../platform
uv run python -m src.verification.cli --template java-micronaut --dry-run || exit 1

echo "✅ Templates component validated!"
```

#### Infrastructure Validation
```bash
#!/bin/bash
# scripts/test-infrastructure.sh

echo "🧪 Testing Infrastructure Component..."

cd terraform-modules

# Test 1: Module structure
echo "1️⃣ Validating module structure..."
for module in */; do
    echo "Checking module: $module"
    [ -f "$module/main.tf" ] || exit 1
    [ -f "$module/variables.tf" ] || exit 1
    [ -f "$module/outputs.tf" ] || exit 1
    [ -f "$module/README.md" ] || exit 1
done

# Test 2: OpenTofu validation
echo "2️⃣ Testing OpenTofu validation..."
for module in */; do
    echo "Validating module: $module"
    cd "$module"
    tofu init || exit 1
    tofu validate || exit 1
    tofu fmt -check || exit 1
    cd ..
done

echo "✅ Infrastructure component validated!"
```

### Step 3: Root-Level Integration Scripts

#### Master Test Script
```bash
#!/bin/bash
# scripts/test-all.sh

set -e

echo "🚀 Running all component tests..."

# Test each component
./scripts/test-platform.sh
./scripts/test-templates.sh
./scripts/test-infrastructure.sh

echo ""
echo "🎉 All components validated successfully!"
echo ""
echo "Components tested:"
echo "  ✅ Platform Service"
echo "  ✅ Java Micronaut Template"
echo "  ✅ Infrastructure Modules"
echo "  ✅ Steering Documentation"
```

#### Setup Script
```bash
#!/bin/bash
# scripts/setup.sh

echo "🔧 Setting up Muppet Platform development environment..."

# Check prerequisites
echo "1️⃣ Checking prerequisites..."

# Check UV
if ! command -v uv &> /dev/null; then
    echo "❌ UV not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Check OpenTofu
if ! command -v tofu &> /dev/null; then
    echo "❌ OpenTofu not found. Please install from: https://opentofu.org/docs/intro/install/"
    exit 1
fi

# Check Java 21
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -ne 21 ]; then
    echo "❌ Java 21 LTS required, found Java $JAVA_VERSION"
    echo "Please install Amazon Corretto 21 LTS"
    exit 1
fi

# Setup platform
echo "2️⃣ Setting up platform service..."
cd platform
uv sync
cd ..

# Setup templates
echo "3️⃣ Setting up templates..."
cd templates/java-micronaut
chmod +x scripts/*.sh
cd ../..

# Make scripts executable
echo "4️⃣ Setting up project scripts..."
chmod +x scripts/*.sh

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run tests: ./scripts/test-all.sh"
echo "  2. Start platform: make platform-dev"
echo "  3. Read documentation: docs/README.md"
```

## Commit Strategy

### Commit 1: Project Structure
```bash
git add scripts/ .github/ CONTRIBUTING.md CHANGELOG.md LICENSE
git commit -m "feat: add monorepo project structure

- Add project-level scripts directory
- Add GitHub workflows and templates
- Add contributing guidelines and changelog
- Add project license"
```

### Commit 2: Platform Component
```bash
git add platform/
git commit -m "feat: validate and enhance platform service component

- Verify all unit tests pass (36 tests)
- Validate MCP server functionality
- Test API endpoints and Docker build
- Update platform documentation
- Ensure UV dependency management works"
```

### Commit 3: Templates Component
```bash
git add templates/
git commit -m "feat: validate and enhance templates component

- Test Java Micronaut template generation
- Validate Gradle wrapper fixes and nuclear option
- Test all template scripts (init, build, test, fix-gradle-wrapper)
- Verify MCP configuration integration
- Validate template verification system"
```

### Commit 4: Infrastructure Component
```bash
git add terraform-modules/
git commit -m "feat: validate infrastructure modules component

- Validate OpenTofu module syntax and structure
- Test module initialization and validation
- Verify module documentation completeness
- Ensure version compatibility with OpenTofu 1.6+"
```

### Commit 5: Integration
```bash
git add .
git commit -m "feat: complete monorepo integration

- Add cross-component integration tests
- Create master build and test scripts
- Set up project-wide linting and formatting
- Add comprehensive documentation
- Enable component-specific CI/CD workflows"
```

## Testing Checklist

### Pre-Migration Testing
- [ ] All platform tests pass (36 tests)
- [ ] Template verification system works
- [ ] MCP server starts successfully
- [ ] API endpoints respond correctly
- [ ] Gradle wrapper fixes work
- [ ] Infrastructure modules validate

### Post-Migration Testing
- [ ] All component tests pass independently
- [ ] Cross-component integration works
- [ ] Build scripts execute successfully
- [ ] Documentation is complete and accurate
- [ ] CI/CD workflows trigger correctly
- [ ] Security scanning passes

## Risk Mitigation

### Backup Strategy
1. Create full backup before starting migration
2. Use feature branch for migration work
3. Test each component thoroughly before committing
4. Keep rollback plan ready

### Validation Strategy
1. Automated testing at each step
2. Manual verification of critical paths
3. Documentation review and updates
4. Peer review of changes

This plan ensures a systematic, safe migration to the monorepo structure while maintaining full functionality of all components.