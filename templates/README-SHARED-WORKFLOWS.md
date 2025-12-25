# Shared Workflow Infrastructure - Java Micronaut

This document describes the centralized pipeline management system for Java Micronaut templates in the Muppet Platform, which allows template maintainers to manage CI/CD workflows for all Java Micronaut muppets.

## Overview

The shared workflow infrastructure enables:

- **Centralized Pipeline Logic**: Template maintainers can update CI/CD logic for all Java Micronaut muppets
- **Java-Specific Optimizations**: Workflows optimized for Java 21 LTS, Gradle, and Micronaut framework
- **Versioned Updates**: Workflows are versioned and can be pinned to specific versions for stability
- **Controlled Rollouts**: Platform provides MCP tools to update muppets to new workflow versions

## Architecture

```
templates/
├── java-micronaut/.github/workflows/
│   ├── shared-test.yml           # Java-optimized testing workflow
│   ├── shared-build.yml          # Java build and Docker image creation
│   ├── shared-deploy.yml         # OpenTofu deployment workflow
│   ├── shared-security.yml       # Java security scanning (OWASP, SpotBugs, PMD)
│   ├── workflow-versions.yml     # Version management workflow
│   └── WORKFLOW_MANIFEST.json   # Workflow metadata and versioning
└── scripts/
    ├── update-muppet-workflows.py    # Script to update muppet workflows
    └── validate-shared-workflows.py  # Workflow validation script
```

## Shared Workflows for Java Micronaut

### Java Micronaut (`templates/java-micronaut/.github/workflows/`)

**shared-test.yml**
- Java 21 LTS enforcement with Amazon Corretto
- Gradle caching and optimization
- JaCoCo test coverage reporting (70% minimum)
- JUnit test execution with parallel support
- Coverage reporting on pull requests

**shared-build.yml**
- Java 21 LTS validation
- Gradle Shadow JAR creation
- Docker image building with multi-stage builds
- ECR push with vulnerability scanning
- Build artifact validation

**shared-deploy.yml**
- OpenTofu-based deployment to AWS Fargate
- Environment-specific configuration (staging/production)
- Health check validation
- ECS service stability waiting
- Deployment rollback support

**shared-security.yml**
- OWASP Dependency Check for vulnerability scanning
- SpotBugs static analysis for bug detection
- PMD code quality analysis
- Checkstyle code style validation
- TruffleHog secrets scanning

## Workflow Versioning

### Version Tags

Workflows are versioned using semantic versioning with template-specific prefixes:
- Java Micronaut: `java-micronaut-v1.2.3`

### Workflow Manifest

Each template includes a `WORKFLOW_MANIFEST.json` file that describes:

```json
{
  "template_type": "java-micronaut",
  "version": "1.2.3",
  "version_tag": "java-micronaut-v1.2.3",
  "created_at": "2024-12-22T00:00:00Z",
  "workflows": {
    "shared-test": {
      "file": "shared-test.yml",
      "description": "Shared Java test workflow with coverage reporting",
      "inputs": ["java_version", "java_distribution", "coverage_threshold"],
      "outputs": ["test_results_artifact", "coverage_artifact"]
    }
  },
  "requirements": {
    "java_version": "21",
    "java_distribution": "corretto",
    "gradle_version": "8.5+"
  }
}
```

### Version Management Workflow

The `workflow-versions.yml` workflow automatically:
1. Validates all shared workflow files
2. Generates updated workflow manifest
3. Creates version tags
4. Publishes GitHub releases
5. Enables controlled rollout to muppets

## Muppet Workflow Generation

### Generated Workflow Structure

When a muppet is created, minimal workflow files are generated that reference shared workflows:

```yaml
# .github/workflows/ci.yml in muppet repository
name: CI - my-muppet
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    uses: muppet-platform/templates/.github/workflows/shared-test.yml@java-micronaut-v1.2.3
    with:
      java_version: "21"
      coverage_threshold: 70
    secrets: inherit
```

### Workflow Types Generated

1. **CI Workflow** (`ci.yml`): Combines test and build workflows
2. **Deploy Workflow** (`deploy.yml`): Handles staging and production deployments
3. **Security Workflow** (`security.yml`): Weekly security scans

## Java Micronaut Optimizations

### Java Micronaut Optimizations

- **Gradle Daemon**: Disabled in CI for consistent builds
- **Parallel Testing**: Enabled for faster test execution
- **Shadow JAR**: Fat JAR creation for containerization
- **JaCoCo Integration**: Built-in coverage reporting
- **Java 21 LTS Enforcement**: Automatic validation and rejection of non-LTS versions

## Usage

### For Template Maintainers

1. **Update Shared Workflows**: Modify workflows in your template's `.github/workflows/` directory
2. **Version Release**: Push changes to trigger automatic versioning
3. **Validate Changes**: Use validation scripts to ensure consistency
4. **Release Notes**: Document breaking changes and new features

### For Platform Operators

1. **Update Muppet Workflows**: Use MCP tools to update muppets to new workflow versions
2. **Rollback Support**: Revert muppets to previous workflow versions if needed
3. **Monitoring**: Track workflow adoption across muppets

### For Muppet Developers

1. **Automatic Updates**: Workflows are updated centrally by platform operators
2. **Custom Configuration**: Override workflow inputs in muppet configuration
3. **Local Testing**: Use provided scripts to test workflow changes locally

## Scripts and Tools

### update-muppet-workflows.py

Updates muppet workflows to reference specific shared workflow versions:

```bash
python3 templates/scripts/update-muppet-workflows.py \
  --template-type java-micronaut \
  --workflow-version 1.2.3 \
  --workflow-type shared-test \
  --muppet-name my-muppet \
  --output-file .github/workflows/test.yml
```

### validate-shared-workflows.py

Validates shared workflow files for consistency and correctness:

```bash
python3 templates/scripts/validate-shared-workflows.py \
  --template-type java-micronaut \
  --strict
```

## MCP Integration

The platform provides MCP tools for workflow management:

- `update_muppet_pipelines(muppet_name, workflow_version)`: Update muppet to specific workflow version
- `list_workflow_versions(template_type)`: Show available workflow versions
- `rollback_muppet_pipelines(muppet_name, workflow_version)`: Rollback to previous version

## Best Practices

### For Template Maintainers

1. **Semantic Versioning**: Use proper semantic versioning for workflow releases
2. **Breaking Changes**: Clearly document breaking changes in major versions
3. **Testing**: Validate workflows with multiple muppets before release
4. **Documentation**: Update workflow descriptions and input/output documentation

### For Workflow Development

1. **Input Validation**: Validate all workflow inputs with appropriate defaults
2. **Error Handling**: Provide clear error messages and recovery instructions
3. **Security**: Pin action versions and avoid script injection vulnerabilities
4. **Performance**: Use caching and parallel execution where appropriate

### For Muppet Integration

1. **Version Pinning**: Pin workflows to specific versions for stability
2. **Configuration**: Use muppet-specific configuration for customization
3. **Testing**: Test workflow changes in staging before production
4. **Monitoring**: Monitor workflow execution and performance

## Troubleshooting

### Common Issues

1. **Workflow Not Found**: Ensure the workflow version tag exists and is accessible
2. **Input Validation Errors**: Check that all required inputs are provided
3. **Permission Errors**: Verify that secrets and permissions are properly configured
4. **Version Conflicts**: Use the validation script to check for inconsistencies

### Debugging

1. **Workflow Logs**: Check GitHub Actions logs for detailed error information
2. **Validation Script**: Run validation script to identify configuration issues
3. **Manifest Check**: Verify workflow manifest matches actual workflow files
4. **Version History**: Check version tags and release notes for changes

## Migration Guide

### Updating Existing Muppets

1. **Identify Current Version**: Check current workflow references in muppet
2. **Review Changes**: Check release notes for breaking changes
3. **Update Configuration**: Modify muppet configuration if needed
4. **Test in Staging**: Deploy to staging environment first
5. **Production Rollout**: Update production workflows after validation

### Template Migration

1. **Create Shared Workflows**: Move existing workflow logic to shared workflows
2. **Generate Manifest**: Create workflow manifest with version information
3. **Update Muppets**: Use update scripts to migrate existing muppets
4. **Validate Migration**: Ensure all muppets are using shared workflows correctly

This shared workflow infrastructure provides a robust foundation for centralized pipeline management while maintaining the flexibility needed for different template types and muppet-specific requirements.