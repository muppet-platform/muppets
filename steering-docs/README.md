# Muppet Platform Steering Documentation

This repository contains centralized steering documentation that is automatically distributed to all muppets created by the Muppet Platform.

## Overview

The steering documentation system provides:
- **Shared Standards**: Common development guidelines applied to all muppets
- **Automatic Distribution**: Steering docs are automatically included in new muppets
- **Centralized Updates**: Updates to shared docs can be pushed to existing muppets
- **Template-Specific Additions**: Templates can add their own steering documentation

## Repository Structure

```
steering-docs/
├── shared/                    # Centrally managed steering docs
│   ├── http-responses.md      # HTTP status code standards
│   ├── test-coverage.md       # 70% minimum coverage requirement
│   ├── security.md            # Security best practices
│   ├── logging.md             # Logging standards
│   └── performance.md         # Performance guidelines
├── templates/                 # Template-specific steering additions
│   ├── java-micronaut/        # Java Micronaut specific guidelines
│   └── ...                    # Future template-specific docs
└── .github/workflows/         # CI/CD for steering docs
```

## Shared Steering Documents

### Core Standards
- **HTTP Response Standards**: Proper HTTP status codes, error handling patterns, and API response formats
- **Test Coverage Requirements**: Minimum 70% test coverage with guidelines for unit and integration testing
- **Security Guidelines**: Authentication, authorization, input validation, and security best practices
- **Logging Standards**: Structured logging, log levels, and monitoring integration
- **Performance Guidelines**: Response time targets, resource usage, and optimization practices

### Distribution Strategy

**For New Muppets:**
- Shared steering docs are automatically copied to `.kiro/steering/shared/` in new muppets
- Template-specific docs are added to `.kiro/steering/template-specific/`
- Muppet developers can add their own docs to `.kiro/steering/muppet-specific/`

**For Existing Muppets:**
- Platform MCP tools can update shared steering docs across all muppets
- Updates preserve muppet-specific customizations
- Version tracking ensures consistent updates

## Usage

### For Platform Developers
- Update shared steering docs in this repository
- Use MCP tools to distribute updates to existing muppets
- Add template-specific guidelines as needed

### For Muppet Developers
- Shared steering docs are read-only (managed by platform)
- Add muppet-specific guidelines to `.kiro/steering/muppet-specific/`
- Follow shared standards for consistency across the platform

### For Template Maintainers
- Add framework-specific guidelines to `templates/{template-name}/`
- Guidelines are automatically included in muppets created from the template
- Keep template-specific docs focused on framework best practices

## MCP Integration

The platform provides MCP tools for steering management:
- `update_shared_steering()`: Update shared steering docs across all muppets
- `list_steering_docs(muppet_name?)`: List available steering documentation

## Version Management

- Shared steering docs are versioned using Git tags
- Updates include version metadata for tracking
- Muppets track which version of shared docs they have
- Incremental updates preserve local customizations

## Contributing

1. **Update Shared Standards**: Modify files in `shared/` directory
2. **Add Template Guidelines**: Create or update files in `templates/{template-name}/`
3. **Test Changes**: Validate that updates work with existing muppets
4. **Create Pull Request**: Include rationale and impact assessment
5. **Deploy Updates**: Use MCP tools to distribute to existing muppets

## Governance

- **Shared Standards**: Require platform team approval
- **Template Guidelines**: Require template maintainer approval
- **Breaking Changes**: Require impact assessment and migration plan
- **Version Compatibility**: Maintain backward compatibility when possible