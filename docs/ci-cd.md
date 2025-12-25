# CI/CD Pipeline Documentation

The Muppet Platform uses GitHub Actions for comprehensive CI/CD automation, including testing, security scanning, building, and deployment.

## Pipeline Overview

### Workflows

1. **[CI Pipeline](.github/workflows/ci.yml)** - Continuous Integration
2. **[CD Pipeline](.github/workflows/cd.yml)** - Continuous Deployment  
3. **[Security Scan](.github/workflows/security.yml)** - Security Analysis
4. **[Release](.github/workflows/release.yml)** - Release Management
5. **[Maintenance](.github/workflows/maintenance.yml)** - Automated Maintenance

## CI Pipeline (`ci.yml`)

**Triggers**: Push to `main`/`develop`, Pull Requests

### Jobs

#### 1. Platform Tests
- **Runtime**: Ubuntu Latest
- **Python**: 3.11 with UV package manager
- **Actions**: 
  - Install dependencies with `uv`
  - Run platform test suite (`./scripts/test-platform.sh`)
  - Upload test results as artifacts

#### 2. Template Tests  
- **Runtime**: Ubuntu Latest
- **Java**: Amazon Corretto 21 LTS (enforced)
- **Actions**:
  - Validate Java 21 LTS version
  - Run template tests (`./scripts/test-templates.sh`)
  - Upload template test results

#### 3. Infrastructure Tests
- **Runtime**: Ubuntu Latest  
- **OpenTofu**: 1.6.0
- **Actions**:
  - Install OpenTofu
  - Run infrastructure validation (`./scripts/test-infrastructure.sh`)
  - Upload infrastructure test results

#### 4. Integration Tests
- **Dependencies**: Platform + Template tests must pass
- **Runtime**: Ubuntu Latest with Python 3.11 + Java 21 LTS
- **Actions**:
  - Run comprehensive integration tests (`./scripts/test-all.sh`)
  - Upload integration test results

#### 5. Code Quality
- **Runtime**: Ubuntu Latest
- **Tools**: Black, isort, flake8, mypy
- **Actions**:
  - Code formatting validation
  - Import sorting validation  
  - Linting checks
  - Type checking

#### 6. Security Scan
- **Runtime**: Ubuntu Latest
- **Tools**: Bandit security scanner
- **Actions**:
  - Run security analysis on Python code
  - Upload security reports

#### 7. Build Artifacts
- **Dependencies**: All test jobs must pass
- **Runtime**: Ubuntu Latest with full toolchain
- **Actions**:
  - Build all components (`./scripts/build-all.sh`)
  - Upload build artifacts

## CD Pipeline (`cd.yml`)

**Triggers**: Push to `main`, Tags `v*`, Manual dispatch

### Jobs

#### 1. Build Docker Image
- **Registry**: GitHub Container Registry (ghcr.io)
- **Platforms**: linux/amd64, linux/arm64
- **Caching**: GitHub Actions cache
- **Tags**: Branch, PR, semver, SHA-based

#### 2. Deploy to Staging
- **Trigger**: Push to `main` or manual dispatch
- **Environment**: `staging` (with protection rules)
- **Actions**:
  - Deploy infrastructure with OpenTofu
  - Run smoke tests
  - Verify deployment health

#### 3. Deploy to Production  
- **Trigger**: Tags `v*` or manual dispatch
- **Dependencies**: Staging deployment must succeed
- **Environment**: `production` (with protection rules)
- **Actions**:
  - Deploy production infrastructure
  - Run comprehensive smoke tests
  - Create GitHub release for tags

#### 4. Cleanup
- **Actions**: Remove old container images (keep 10 most recent)

## Security Pipeline (`security.yml`)

**Triggers**: Daily at 2 AM UTC, Push to `main`, PRs, Manual dispatch

### Jobs

#### 1. Dependency Vulnerability Scan
- **Tools**: Safety (Python vulnerability database)
- **Actions**: Scan for known vulnerabilities in dependencies

#### 2. Code Security Analysis
- **Tools**: Bandit (Python security linter)
- **Actions**: Static analysis for security issues

#### 3. Container Security Scan
- **Tools**: Trivy (container vulnerability scanner)
- **Actions**: 
  - Build Docker image
  - Scan for OS and library vulnerabilities
  - Upload results to GitHub Security tab

#### 4. Infrastructure Security Scan
- **Tools**: tfsec, Checkov (Infrastructure as Code security)
- **Actions**: Scan OpenTofu modules for security misconfigurations

#### 5. Secrets Scan
- **Tools**: TruffleHog, GitLeaks
- **Actions**: Scan for accidentally committed secrets

#### 6. Security Summary
- **Actions**: Generate comprehensive security report

## Release Pipeline (`release.yml`)

**Triggers**: Tags `v*`, Manual dispatch

### Jobs

#### 1. Validate Release
- **Actions**: 
  - Validate version format (semver)
  - Determine if pre-release

#### 2. Full Test Suite
- **Actions**: Run complete test suite before release

#### 3. Build Release Artifacts
- **Actions**:
  - Build platform, templates, and terraform modules
  - Create compressed archives
  - Upload as release artifacts

#### 4. Generate Release Notes
- **Actions**:
  - Generate changelog from git history
  - Create comprehensive release documentation

#### 5. Create GitHub Release
- **Actions**:
  - Create GitHub release with artifacts
  - Upload platform, templates, and terraform archives

#### 6. Update Documentation
- **Actions**:
  - Update CHANGELOG.md
  - Commit documentation updates

## Maintenance Pipeline (`maintenance.yml`)

**Triggers**: Weekly (Sundays 3 AM UTC), Manual dispatch

### Jobs

#### 1. Update Dependencies
- **Actions**:
  - Update Python dependencies with `uv`
  - Run tests to verify compatibility
  - Create PR with dependency updates

#### 2. Security Maintenance
- **Actions**:
  - Run comprehensive security scans
  - Generate security reports
  - Create issues for high-severity vulnerabilities

#### 3. Cleanup Artifacts
- **Actions**:
  - Remove old workflow runs (>30 days)
  - Clean up old artifacts

#### 4. Documentation Maintenance
- **Actions**:
  - Update documentation links and versions
  - Generate API documentation
  - Check for broken links

#### 5. Health Summary
- **Actions**: Generate weekly maintenance report

## Environment Configuration

### Required Secrets

```yaml
# AWS Deployment
AWS_ACCESS_KEY_ID: AWS access key for deployment
AWS_SECRET_ACCESS_KEY: AWS secret key for deployment

# GitHub
GITHUB_TOKEN: Automatically provided by GitHub Actions

# Optional
GITLEAKS_LICENSE: GitLeaks license key (if using pro features)
```

### Required Variables

```yaml
# AWS Configuration  
AWS_REGION: AWS region for deployment (default: us-east-1)

# Environment URLs (set per environment)
STAGING_URL: Staging environment URL
PRODUCTION_URL: Production environment URL
```

### Environment Protection Rules

#### Staging Environment
- **Required reviewers**: 1 team member
- **Wait timer**: 0 minutes
- **Restrict to branches**: `main`

#### Production Environment  
- **Required reviewers**: 2 team members (including team lead)
- **Wait timer**: 5 minutes
- **Restrict to branches**: `main`
- **Restrict to tags**: `v*`

## Artifact Management

### Build Artifacts
- **Retention**: 30 days
- **Contents**: Platform service, templates, terraform modules
- **Format**: Compressed tar.gz archives

### Test Results
- **Retention**: 7 days (30 days for releases)
- **Contents**: JUnit XML, coverage reports, logs
- **Format**: Structured test output

### Security Reports
- **Retention**: 30 days (90 days for maintenance reports)
- **Contents**: Vulnerability scans, security analysis
- **Format**: JSON and SARIF formats

### Container Images
- **Registry**: GitHub Container Registry
- **Retention**: 10 most recent versions
- **Cleanup**: Automated via CD pipeline

## Monitoring and Notifications

### Workflow Status
- **Success**: Green checkmarks on commits/PRs
- **Failure**: Red X with detailed logs
- **In Progress**: Yellow dot during execution

### Notifications
- **PR Status**: Automatic status checks on pull requests
- **Release**: GitHub release notifications
- **Security**: Issues created for high-severity vulnerabilities
- **Maintenance**: Weekly summary reports

## Troubleshooting

### Common Issues

#### Java Version Errors
```bash
# Error: Unsupported Java version
# Solution: Ensure Amazon Corretto 21 LTS is used
- name: Set up Java (Amazon Corretto 21 LTS)
  uses: actions/setup-java@v4
  with:
    java-version: '21'
    distribution: 'corretto'
```

#### UV Installation Issues
```bash
# Error: uv command not found
# Solution: Install UV and add to PATH
- name: Install uv
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "$HOME/.cargo/bin" >> $GITHUB_PATH
```

#### OpenTofu State Issues
```bash
# Error: State file conflicts
# Solution: Use proper workspace management
- name: Deploy infrastructure
  run: |
    cd platform/terraform
    tofu init
    tofu workspace select staging || tofu workspace new staging
    tofu apply -auto-approve
```

#### Docker Build Failures
```bash
# Error: Docker build context too large
# Solution: Use .dockerignore to exclude unnecessary files
# Add to .dockerignore:
.git
.pytest_cache
__pycache__
*.pyc
.venv
```

### Debug Workflows

#### Enable Debug Logging
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

#### Access Artifacts
1. Go to workflow run page
2. Scroll to "Artifacts" section
3. Download relevant artifacts for debugging

#### Re-run Failed Jobs
1. Go to failed workflow run
2. Click "Re-run failed jobs"
3. Monitor logs for detailed error information

## Best Practices

### Workflow Design
- **Fail Fast**: Run quick tests first
- **Parallel Execution**: Run independent jobs in parallel
- **Conditional Execution**: Use `if` conditions to skip unnecessary jobs
- **Artifact Sharing**: Use artifacts to share data between jobs

### Security
- **Least Privilege**: Use minimal required permissions
- **Secret Management**: Store sensitive data in GitHub Secrets
- **Dependency Scanning**: Regular security scans
- **Container Security**: Scan images before deployment

### Performance
- **Caching**: Use GitHub Actions cache for dependencies
- **Matrix Builds**: Test multiple configurations efficiently
- **Resource Limits**: Set appropriate timeouts and resource limits

### Maintenance
- **Regular Updates**: Keep actions and tools updated
- **Monitoring**: Monitor workflow performance and success rates
- **Documentation**: Keep CI/CD documentation current
- **Testing**: Test workflow changes in feature branches

## Migration and Updates

### Updating Workflows
1. Create feature branch
2. Update workflow files
3. Test in feature branch
4. Review changes carefully
5. Merge to main after approval

### Adding New Jobs
1. Follow existing patterns
2. Add appropriate dependencies
3. Include error handling
4. Update documentation
5. Test thoroughly

### Changing Environments
1. Update environment variables
2. Modify protection rules
3. Test deployment process
4. Update documentation
5. Communicate changes to team

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [OpenTofu GitHub Actions](https://github.com/opentofu/setup-opentofu)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Security Actions](https://github.com/marketplace?type=actions&query=security)
- [AWS Actions](https://github.com/aws-actions)