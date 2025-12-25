# GitHub Repository Setup Plan

## Repository Creation Strategy

### 1. Main Repository Setup

**Repository Name**: `muppet-platform`
**Visibility**: Private (initially), Public (when ready)
**Organization**: Create under your GitHub organization

### 2. Branch Strategy

```
main                    # Production-ready code
├── develop            # Integration branch for features
├── feature/*          # Feature development branches
├── hotfix/*           # Critical bug fixes
└── release/*          # Release preparation branches
```

### 3. Initial Repository Structure

```bash
# Create main repository
gh repo create your-org/muppet-platform --private --description "Internal developer platform for creating and managing backend applications"

# Set up branch protection
gh api repos/your-org/muppet-platform/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/platform","ci/templates","ci/infrastructure"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### 4. GitHub Actions Workflows

#### Platform Service CI (`platform-ci.yml`)
```yaml
name: Platform Service CI

on:
  push:
    paths: ['platform/**']
  pull_request:
    paths: ['platform/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: cd platform && uv sync
      - name: Run tests
        run: cd platform && uv run pytest
      - name: Build Docker image
        run: cd platform && docker build -t muppet-platform:${{ github.sha }} .
```

#### Template Validation CI (`templates-ci.yml`)
```yaml
name: Template Validation CI

on:
  push:
    paths: ['templates/**']
  pull_request:
    paths: ['templates/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Java 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'
      - name: Validate Java Micronaut Template
        run: |
          cd templates/java-micronaut
          ./scripts/init.sh
          ./scripts/build.sh
          ./scripts/test.sh
```

#### Infrastructure CI (`infrastructure-ci.yml`)
```yaml
name: Infrastructure CI

on:
  push:
    paths: ['terraform-modules/**']
  pull_request:
    paths: ['terraform-modules/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup OpenTofu
        uses: opentofu/setup-opentofu@v1
        with:
          tofu_version: 1.6.0
      - name: Validate modules
        run: |
          for module in terraform-modules/*/; do
            cd "$module"
            tofu init
            tofu validate
            tofu fmt -check
            cd - > /dev/null
          done
```

### 5. Repository Settings

#### Branch Protection Rules
- **Require pull request reviews**: 1 approving review
- **Dismiss stale reviews**: When new commits are pushed
- **Require status checks**: All CI workflows must pass
- **Require branches to be up to date**: Before merging
- **Restrict pushes**: Only allow through pull requests

#### Security Settings
- **Dependency alerts**: Enable Dependabot alerts
- **Security advisories**: Enable private vulnerability reporting
- **Secret scanning**: Enable for all branches
- **Code scanning**: Enable CodeQL analysis

### 6. Issue and PR Templates

#### Issue Template (`.github/ISSUE_TEMPLATE/bug_report.md`)
```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**Component**
- [ ] Platform Service
- [ ] Java Micronaut Template
- [ ] Infrastructure Modules
- [ ] Documentation

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Environment**
- OS: [e.g. macOS, Ubuntu]
- Java Version: [e.g. Amazon Corretto 21]
- Platform Version: [e.g. v1.0.0]

**Additional context**
Add any other context about the problem here.
```

#### Feature Request Template (`.github/ISSUE_TEMPLATE/feature_request.md`)
```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Component Impact**
Which components would be affected by this feature?
- [ ] Platform Service
- [ ] Templates
- [ ] Infrastructure
- [ ] Documentation

**Additional context**
Add any other context or screenshots about the feature request here.
```

#### Pull Request Template (`.github/pull_request_template.md`)
```markdown
## Description
Brief description of the changes in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Component Changes
- [ ] Platform Service
- [ ] Templates
- [ ] Infrastructure Modules
- [ ] Documentation

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] New tests added for new functionality

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published
```

### 7. Repository Labels

```bash
# Create standard labels
gh label create "component:platform" --color "0052cc" --description "Platform service related"
gh label create "component:templates" --color "5319e7" --description "Template related"
gh label create "component:infrastructure" --color "d4c5f9" --description "Infrastructure related"
gh label create "component:docs" --color "0e8a16" --description "Documentation related"

gh label create "priority:high" --color "d93f0b" --description "High priority"
gh label create "priority:medium" --color "fbca04" --description "Medium priority"
gh label create "priority:low" --color "0e8a16" --description "Low priority"

gh label create "type:bug" --color "d73a4a" --description "Something isn't working"
gh label create "type:feature" --color "a2eeef" --description "New feature or request"
gh label create "type:improvement" --color "7057ff" --description "Enhancement to existing feature"
gh label create "type:maintenance" --color "fef2c0" --description "Maintenance and refactoring"
```

### 8. Project Boards

Create GitHub Projects for:
- **Development Roadmap**: High-level feature planning
- **Sprint Planning**: Current sprint work
- **Bug Tracking**: Issue triage and resolution
- **Release Planning**: Release milestone tracking

### 9. Security Configuration

#### Dependabot Configuration (`.github/dependabot.yml`)
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/platform"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "gradle"
    directory: "/templates/java-micronaut"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "terraform"
    directory: "/terraform-modules"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

### 10. Documentation Setup

#### Main README Structure
```markdown
# Muppet Platform

> Internal developer platform for creating and managing backend applications

## Quick Start
[Getting started guide]

## Architecture
[High-level architecture overview]

## Components
- [Platform Service](platform/README.md)
- [Templates](templates/README.md)
- [Infrastructure](terraform-modules/README.md)
- [Documentation](docs/README.md)

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
[License information]
```

### 11. Release Strategy

#### Semantic Versioning
- Use GitHub Releases with semantic versioning
- Automated changelog generation
- Release notes with component-specific changes

#### Release Workflow
```yaml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create Release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
```

This GitHub setup plan provides a comprehensive foundation for managing the Muppet Platform as a modular monorepo with proper CI/CD, security, and collaboration features.