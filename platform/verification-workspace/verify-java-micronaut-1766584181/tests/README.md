# Java Micronaut Template Test Suite

This directory contains automated tests for the Java Micronaut template to ensure it works correctly in containerized environments.

## Test Scripts

### `test-template.sh` - Comprehensive Test Suite
Full end-to-end testing including:
- Java version compatibility check
- Template generation and variable substitution
- Gradle build and dependency resolution
- Unit test execution
- Docker image building
- Container startup and health checks
- API endpoint validation

**Usage:**
```bash
./test-template.sh
```

**Duration:** ~5-10 minutes (includes Docker build)

### `quick-test.sh` - Fast Validation
Quick validation focusing on:
- Template generation
- Gradle build
- JAR creation

**Usage:**
```bash
./quick-test.sh
```

**Duration:** ~1-2 minutes

## Prerequisites

### Required Software
- **Java 21 LTS** (Amazon Corretto recommended)
- **Docker** (for full test suite)
- **curl** (for endpoint testing)

### Java Version Requirements
The tests enforce Java 21 LTS usage as per the platform requirements:
- ✅ Java 21 LTS (Amazon Corretto)
- ❌ Java 22, 23, 24, 25 (non-LTS versions)

If Java 21 LTS is not the default, the tests will automatically use it if installed at:
`/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home`

## Test Coverage

### Template Generation
- Variable substitution (`verify-java-micronaut-1766584181`)
- File structure validation
- Configuration file generation

### Build System
- Gradle wrapper functionality
- Dependency resolution
- Java 21 LTS compatibility
- Shadow JAR creation

### Application Runtime
- Micronaut application startup
- Health endpoint functionality
- API endpoint responses
- Container networking

### Docker Integration
- Multi-stage build process
- Image optimization
- Container security (non-root user)
- Health check configuration

## Continuous Integration

These tests should be run:
- **Before template releases** - Full test suite
- **On template changes** - Quick test minimum
- **Weekly** - Full test suite for regression detection

## Troubleshooting

### Common Issues

**Java Version Errors:**
```bash
# Install Java 21 LTS
brew install --cask corretto@21

# Set JAVA_HOME
export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home
```

**Docker Build Failures:**
- Ensure Docker Desktop/Rancher Desktop is running
- Check available disk space (builds require ~500MB)
- Verify network connectivity for dependency downloads

**Port Conflicts:**
- Full test suite uses port 3001 (configurable in script)
- Ensure port is available before running tests

### Test Logs

Test output includes:
- ✅ Success indicators
- ❌ Error messages with context
- ℹ️ Progress information
- 🧹 Cleanup status

## Maintenance

### Updating Tests
When template changes are made:
1. Update test expectations if needed
2. Run full test suite to validate
3. Update this README if new requirements are added

### Adding New Tests
Follow the existing pattern:
1. Create test function with descriptive name
2. Add logging with appropriate colors
3. Include cleanup in error cases
4. Update main() function to include new test

## Integration with Platform

These tests are designed to be integrated with:
- **Muppet Platform CI/CD** - Automated template validation
- **Template Release Process** - Quality gates
- **Developer Workflows** - Local validation before commits