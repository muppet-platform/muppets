# Contributing to Muppet Platform

Thank you for your interest in contributing to the Muppet Platform! This document provides guidelines for contributing to this project.

## Getting Started

### Prerequisites

- **Java 21 LTS**: Amazon Corretto 21 (required for template development)
- **Python 3.10+**: For platform service development
- **UV**: Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **OpenTofu 1.6+**: For infrastructure modules (`brew install opentofu`)
- **Docker**: For containerization (optional but recommended)

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/muppet-platform.git
   cd muppet-platform
   ```

2. **Run the setup script**:
   ```bash
   ./scripts/setup.sh
   ```

3. **Verify installation**:
   ```bash
   ./scripts/test-all.sh
   ```

## Project Structure

The Muppet Platform is organized as a monorepo with clear component boundaries:

- **`platform/`** - Core FastAPI service (Python)
- **`templates/`** - Muppet templates (Java Micronaut + future templates)
- **`terraform-modules/`** - Shared infrastructure modules (OpenTofu)
- **`steering-docs/`** - Centralized development guidelines
- **`scripts/`** - Project-level automation scripts
- **`.github/`** - CI/CD workflows and templates

## Development Workflow

### Branch Strategy

- **`main`** - Production-ready code
- **`develop`** - Integration branch for features
- **`feature/*`** - Feature development branches
- **`hotfix/*`** - Critical bug fixes

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the component-specific guidelines below

3. **Test your changes**:
   ```bash
   # Test specific component
   ./scripts/test-platform.sh      # Platform service
   ./scripts/test-templates.sh     # Templates
   ./scripts/test-infrastructure.sh # Infrastructure
   
   # Or test everything
   ./scripts/test-all.sh
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Component-Specific Guidelines

### Platform Service (`platform/`)

**Technology**: Python 3.10+, FastAPI, UV

**Development**:
```bash
cd platform
uv sync                    # Install dependencies
uv run pytest            # Run tests
uv run uvicorn src.main:app --reload  # Start dev server
```

**Code Standards**:
- Use type hints for all functions
- Follow PEP 8 style guidelines
- Write docstrings for all public functions
- Maintain 80%+ test coverage

**Testing**:
- Unit tests with pytest
- Mock all external services (GitHub, AWS)
- Use property-based testing for complex logic

### Templates (`templates/`)

**Technology**: Java 21 LTS (Amazon Corretto), Gradle 8.5+

**Development**:
```bash
cd templates/java-micronaut
./scripts/init.sh         # Initialize template
./scripts/build.sh        # Build template
./scripts/test.sh         # Run tests
```

**Standards**:
- **Java 21 LTS only** - No non-LTS versions
- Use Gradle wrapper (never global Gradle in templates)
- All scripts must be executable and well-documented
- Template variables must use `{{variable}}` syntax

**Testing**:
- Template verification system validates all generated code
- Scripts must pass syntax validation
- Generated muppets must build successfully

### Infrastructure Modules (`terraform-modules/`)

**Technology**: OpenTofu 1.6+

**Development**:
```bash
cd terraform-modules/module-name
tofu init                 # Initialize module
tofu validate            # Validate syntax
tofu fmt                 # Format code
```

**Standards**:
- Use OpenTofu (not Terraform)
- All modules must have: `main.tf`, `variables.tf`, `outputs.tf`, `README.md`
- Follow HashiCorp naming conventions
- Include usage examples in README

**Testing**:
- Syntax validation with `tofu validate`
- Format checking with `tofu fmt -check`
- Integration tests with Terratest (when applicable)

## Code Quality Standards

### General Guidelines

- **Security First**: No hardcoded secrets, follow least privilege
- **Documentation**: Update docs for user-facing changes
- **Testing**: All changes must include appropriate tests
- **Performance**: Consider performance impact of changes

### Commit Message Format

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(platform): add muppet status endpoint
fix(templates): resolve Gradle wrapper corruption
docs(infrastructure): update module usage examples
```

## Testing Requirements

### Minimum Requirements

- **Unit Tests**: All new code must have unit tests
- **Integration Tests**: Cross-component functionality must be tested
- **Documentation Tests**: All examples in documentation must work

### Running Tests

```bash
# Component-specific tests
./scripts/test-platform.sh
./scripts/test-templates.sh
./scripts/test-infrastructure.sh

# All tests
./scripts/test-all.sh

# Specific test suites
cd platform && uv run pytest tests/test_specific.py
```

## Pull Request Process

### Before Submitting

1. **Run all tests**: `./scripts/test-all.sh`
2. **Update documentation**: For user-facing changes
3. **Add tests**: For new functionality
4. **Check formatting**: Follow component style guides

### PR Requirements

- **Description**: Clear description of changes
- **Testing**: Evidence that changes work
- **Documentation**: Updated for user-facing changes
- **Breaking Changes**: Clearly marked and justified

### Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one approving review required
3. **Testing**: Manual testing for significant changes
4. **Documentation**: Review of documentation updates

## Release Process

### Versioning

We use semantic versioning (SemVer):
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

### Release Steps

1. **Create release branch**: `release/v1.2.3`
2. **Update version numbers**: In relevant files
3. **Update CHANGELOG.md**: Document all changes
4. **Test thoroughly**: Full test suite + manual testing
5. **Create release**: Tag and publish

## Getting Help

### Resources

- **Documentation**: Check `docs/` directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions

### Contact

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: Tag relevant maintainers in PRs

## Code of Conduct

### Our Standards

- **Respectful**: Be respectful and inclusive
- **Constructive**: Provide constructive feedback
- **Collaborative**: Work together towards common goals
- **Professional**: Maintain professional communication

### Enforcement

Violations of the code of conduct should be reported to the project maintainers. All reports will be handled confidentially.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to the Muppet Platform! 🎭