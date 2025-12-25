# Muppet Instantiation Verification System

The Muppet Instantiation Verification System is an automated testing framework that validates muppet templates by creating test instances and verifying all aspects of the generation process.

## Overview

This system addresses the critical need to ensure that muppet templates work correctly before they are used by developers. It provides comprehensive validation of:

1. **Template Generation** - Verifies that templates can be instantiated successfully
2. **Parameter Injection** - Validates that template parameters are correctly injected into generated files
3. **Variable Replacement** - Ensures all template variables ({{variable}}) are properly replaced
4. **Build Process** - Tests that generated code compiles and builds successfully
5. **Artifact Creation** - Verifies that expected build artifacts are created
6. **Script Verification** - Validates that all development scripts exist, are executable, and work correctly

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Muppet Verification System                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Template        │  │ Generation      │  │ Build           │  │
│  │ Validation      │  │ Verification    │  │ Verification    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Parameter       │  │ Variable        │  │ Artifact        │  │
│  │ Injection       │  │ Replacement     │  │ Validation      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐                                            │
│  │ Script          │                                            │
│  │ Verification    │                                            │
│  └─────────────────┘                                            │
├─────────────────────────────────────────────────────────────────┤
│                    Template Manager                             │
├─────────────────────────────────────────────────────────────────┤
│                    File System                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### MuppetVerificationSystem

The main orchestrator that coordinates all verification steps:

```python
from src.verification.muppet_verification import MuppetVerificationSystem

# Create verification system
verification_system = MuppetVerificationSystem()

# Verify a specific template
result = verification_system.verify_template("java-micronaut")

# Verify all templates
results = verification_system.verify_all_templates()
```

### VerificationConfig

Configuration class that controls verification behavior:

```python
from src.verification.muppet_verification import VerificationConfig

config = VerificationConfig(
    test_muppet_prefix="verify",
    cleanup_on_success=True,
    cleanup_on_failure=False,
    build_timeout_seconds=300,
    java_version_required="21",
    test_parameters={
        'aws_region': 'us-west-2',
        'environment': 'verification',
        'custom_param': 'test_value_123'
    }
)
```

### VerificationResult

Detailed result object containing all verification outcomes:

```python
# Access verification results
print(f"Success: {result.success}")
print(f"Duration: {result.duration_seconds} seconds")
print(f"Generated files: {len(result.generated_files)}")
print(f"Build artifacts: {result.build_artifacts}")
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")

# Convert to dictionary for serialization
result_dict = result.to_dict()
```

## Usage

### Command Line Interface

The verification system provides a comprehensive CLI:

```bash
# Verify a specific template
./platform/scripts/verify-muppet-instantiation.sh verify java-micronaut

# Verify all templates
./platform/scripts/verify-muppet-instantiation.sh verify-all

# List available templates
./platform/scripts/verify-muppet-instantiation.sh list

# Verify with custom parameters
./platform/scripts/verify-muppet-instantiation.sh verify java-micronaut \
  --custom-params '{"environment": "test", "custom_param": "value"}'

# Verify and save results to file
./platform/scripts/verify-muppet-instantiation.sh verify java-micronaut \
  --output verification-results.json

# Verbose output with workspace preservation
./platform/scripts/verify-muppet-instantiation.sh verify java-micronaut \
  --verbose --no-cleanup
```

### Python API

Use the verification system programmatically:

```python
from src.verification.muppet_verification import (
    MuppetVerificationSystem, 
    VerificationConfig
)

# Create custom configuration
config = VerificationConfig(
    cleanup_on_success=False,  # Preserve workspace for inspection
    test_parameters={
        'custom_param': 'my_test_value'
    }
)

# Initialize verification system
verification_system = MuppetVerificationSystem(config=config)

# Verify template
result = verification_system.verify_template(
    template_name="java-micronaut",
    custom_parameters={"environment": "staging"}
)

# Check results
if result.success:
    print("✅ Template verification passed!")
    print(f"Generated {len(result.generated_files)} files")
    print(f"Build completed in {result.duration_seconds:.2f} seconds")
else:
    print("❌ Template verification failed!")
    for error in result.errors:
        print(f"  Error: {error}")
```

## Verification Process

### Step 1: Template Validation

- Verifies template exists and is discoverable
- Validates template metadata (template.yaml)
- Checks template structure and required files

### Step 2: Test Muppet Generation

- Creates unique test muppet name with timestamp
- Generates muppet code from template using TemplateManager
- Collects list of all generated files
- Records injected parameters for later verification

### Step 3: Parameter Injection Verification

- Verifies that all test parameters appear in generated files
- Checks both default parameters and custom parameters
- Validates muppet name injection across all relevant files

### Step 4: Variable Replacement Verification

- Scans all generated files for unreplaced {{variable}} patterns
- Reports any template variables that weren't properly substituted
- Checks multiple file types: .java, .yml, .gradle, .md, etc.

### Step 5: Build Process Verification

- **Java Micronaut Templates:**
  - Checks Java version compatibility (Java 21 LTS required)
  - Runs Gradle build process: clean, compileJava, test, shadowJar
  - Captures build output and error messages
  - Validates build completion within timeout

- **Other Templates:**
  - Template-specific build processes can be added
  - Currently logs warning for unsupported template types

### Step 6: Build Artifact Verification

- Verifies expected build artifacts were created
- **Java Micronaut Expected Artifacts:**
  - `build/libs/{muppet_name}-1.0.0-all.jar`
  - `build/classes/java/main/`
  - `build/test-results/test/`

### Step 7: Development Script Verification

The verification system performs comprehensive validation of all development scripts in the generated muppet:

#### Static Analysis
- **Existence Check**: Verifies all expected scripts are present
- **Permission Check**: Ensures scripts are executable
- **Syntax Validation**: Basic shell script syntax checking
- **Variable Replacement**: Confirms all template variables are properly replaced
- **Help Documentation**: Checks for usage/help information

#### Functional Testing (Optional)
When enabled with `--functional-tests`, the system can execute safe scripts to verify they work correctly:

```bash
# Enable functional testing
python -m src.verification.cli verify java-micronaut --functional-tests

# Or via shell script
./platform/scripts/verify-muppet-instantiation.sh verify java-micronaut --functional-tests
```

**Safe Scripts for Functional Testing:**
- `quick-verify.sh` - Basic verification script
- `test-parameter-injection.sh` - Parameter injection validation

**Security Note:** Only pre-approved safe scripts are executed during functional testing to prevent side effects.

#### Expected Scripts (Java Micronaut)
The system verifies the presence and functionality of these 9 scripts:
1. `build.sh` - Build the application
2. `test.sh` - Run tests
3. `run.sh` - Run the application
4. `init.sh` - Initialize the project
5. `quick-verify.sh` - Quick verification checks
6. `test-docker-build.sh` - Test Docker build process
7. `test-local-dev.sh` - Test local development setup
8. `test-parameter-injection.sh` - Test parameter injection
9. `verify-template.sh` - Template verification

## Configuration Options

### Test Parameters

Default test parameters injected into templates:

```python
test_parameters = {
    'aws_region': 'us-west-2',
    'environment': 'verification',
    'custom_param': 'test_value_123'
}
```

### File Patterns for Variable Checking

Files checked for unreplaced variables:

```python
variable_check_patterns = [
    '**/*.java',
    '**/*.yml',
    '**/*.yaml', 
    '**/*.md',
    '**/*.gradle',
    '**/*.properties',
    'Dockerfile'
]
```

### Expected Build Artifacts

Template-specific expected artifacts:

```python
expected_artifacts = {
    'java-micronaut': [
        'build/libs/{muppet_name}-1.0.0-all.jar',
        'build/classes/java/main/',
        'build/test-results/test/'
    ]
}
```

## Integration with CI/CD

### GitHub Actions Integration

```yaml
name: Template Verification
on:
  push:
    paths: ['templates/**']
  pull_request:
    paths: ['templates/**']

jobs:
  verify-templates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Java 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd platform
          pip install -r requirements.txt
      
      - name: Verify all templates
        run: |
          ./platform/scripts/verify-muppet-instantiation.sh verify-all \
            --output template-verification-results.json
      
      - name: Upload verification results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: template-verification-results
          path: template-verification-results.json
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run template verification before commits that modify templates
if git diff --cached --name-only | grep -q "^templates/"; then
    echo "Template files modified, running verification..."
    ./platform/scripts/verify-muppet-instantiation.sh verify-all
    if [ $? -ne 0 ]; then
        echo "Template verification failed. Commit aborted."
        exit 1
    fi
fi
```

## Error Handling and Troubleshooting

### Common Issues

#### Java Version Problems

```
Error: Java 22 detected. Java 21 LTS is recommended.
```

**Solution:**
```bash
# Install Java 21 LTS
brew install --cask corretto@21

# Set JAVA_HOME
export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home
```

#### Build Timeout

```
Error: Build command timed out: ./gradlew shadowJar
```

**Solution:**
```python
# Increase timeout in configuration
config = VerificationConfig(
    build_timeout_seconds=600  # 10 minutes
)
```

#### Missing Build Artifacts

```
Error: Missing build artifact: build/libs/test-muppet-1.0.0-all.jar
```

**Solution:**
- Check Gradle build configuration
- Verify shadowJar plugin is properly configured
- Ensure build process completed successfully

#### Unreplaced Variables

```
Error: Unreplaced variable: src/Application.java: muppet_name
```

**Solution:**
- Check template file has proper {{muppet_name}} syntax
- Verify TemplateManager variable replacement logic
- Ensure template.yaml includes required variables

### Debugging Tips

1. **Use --no-cleanup flag** to preserve verification workspace:
   ```bash
   ./platform/scripts/verify-muppet-instantiation.sh verify java-micronaut --no-cleanup
   ```

2. **Enable verbose output** for detailed information:
   ```bash
   ./platform/scripts/verify-muppet-instantiation.sh verify java-micronaut --verbose
   ```

3. **Check verification workspace** manually:
   ```bash
   # Workspace location: platform/verification-workspace/verify-{template}-{timestamp}/
   ls -la platform/verification-workspace/
   ```

4. **Run individual build steps** manually:
   ```bash
   cd platform/verification-workspace/verify-java-micronaut-*/
   ./gradlew clean build --info
   ```

## Extending the System

### Adding New Template Support

To add verification support for a new template type:

1. **Add expected artifacts** to VerificationConfig:
   ```python
   expected_artifacts = {
       'python-fastapi': [
           'dist/*.whl',
           'build/',
           '.pytest_cache/'
       ]
   }
   ```

2. **Implement build verification** method:
   ```python
   def _verify_python_build(self, verification_path: Path, result: VerificationResult) -> None:
       """Verify Python FastAPI build process."""
       # Run pip install, pytest, build commands
       # Update result.build_success and result.build_output
   ```

3. **Update build process dispatcher**:
   ```python
   def _verify_build_process(self, verification_path: Path, template_name: str,
                           test_muppet_name: str, result: VerificationResult) -> None:
       if template_name == 'java-micronaut':
           self._verify_java_build(verification_path, result)
       elif template_name == 'python-fastapi':
           self._verify_python_build(verification_path, result)
   ```

### Custom Verification Steps

Add custom verification steps by extending MuppetVerificationSystem:

```python
class CustomVerificationSystem(MuppetVerificationSystem):
    
    def verify_template(self, template_name: str, 
                       custom_parameters: Optional[Dict[str, Any]] = None) -> VerificationResult:
        # Run standard verification
        result = super().verify_template(template_name, custom_parameters)
        
        # Add custom verification step
        if result.success:
            self._verify_custom_requirements(result.verification_path, result)
        
        return result
    
    def _verify_custom_requirements(self, verification_path: Path, 
                                  result: VerificationResult) -> None:
        # Custom verification logic
        pass
```

## Performance Considerations

### Optimization Strategies

1. **Parallel Template Verification:**
   ```python
   import concurrent.futures
   
   def verify_templates_parallel(template_names):
       with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
           futures = {
               executor.submit(verification_system.verify_template, name): name 
               for name in template_names
           }
           results = {}
           for future in concurrent.futures.as_completed(futures):
               template_name = futures[future]
               results[template_name] = future.result()
       return results
   ```

2. **Build Caching:**
   - Cache Gradle dependencies between runs
   - Reuse Docker build layers
   - Store verification workspaces for incremental testing

3. **Selective Verification:**
   - Only verify templates that have changed
   - Skip build verification for non-code changes
   - Use checksums to detect template modifications

### Resource Usage

- **Disk Space:** Each verification creates ~50-100MB workspace
- **Memory:** Peak usage ~500MB during Java builds
- **CPU:** Gradle builds are CPU-intensive
- **Time:** Java template verification takes ~2-5 minutes

## Security Considerations

### Workspace Isolation

- Each verification runs in isolated temporary directory
- No network access during build (offline mode)
- Limited file system permissions

### Code Execution Safety

- Only executes build tools (Gradle, Maven, etc.)
- No arbitrary code execution from templates
- Sandboxed build environment

### Cleanup Policies

- Automatic cleanup of successful verifications
- Configurable cleanup of failed verifications
- Secure deletion of sensitive test data

## Monitoring and Metrics

### Verification Metrics

Track verification system performance:

```python
# Collect metrics during verification
metrics = {
    'verification_duration': result.duration_seconds,
    'template_generation_time': generation_time,
    'build_time': build_time,
    'success_rate': success_count / total_count,
    'error_types': error_classification
}
```

### Health Checks

Monitor verification system health:

```python
def health_check():
    """Check verification system health."""
    try:
        # Quick template discovery test
        templates = template_manager.discover_templates()
        
        # Java version check
        java_version = verification_system._check_java_version()
        
        # Workspace access check
        workspace_writable = verification_system.verification_root.exists()
        
        return {
            'status': 'healthy',
            'templates_found': len(templates),
            'java_version': java_version,
            'workspace_accessible': workspace_writable
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
```

## Future Enhancements

### Planned Features

1. **Container-based Verification:**
   - Run verifications in Docker containers
   - Isolated build environments
   - Consistent dependency versions

2. **Performance Benchmarking:**
   - Measure build times and resource usage
   - Compare template performance
   - Regression detection

3. **Visual Reporting:**
   - HTML reports with charts and graphs
   - Template comparison views
   - Historical trend analysis

4. **Integration Testing:**
   - Deploy verified muppets to test environments
   - End-to-end functionality testing
   - API endpoint validation

5. **Template Quality Metrics:**
   - Code complexity analysis
   - Security vulnerability scanning
   - Best practice compliance checking

### Extensibility Points

- Plugin system for custom verification steps
- Template-specific verification rules
- Integration with external testing tools
- Custom reporting formats and destinations