# Muppet Platform Deployment Principles

## Core Principle: CI/CD-Only Deployments

**All production deployments MUST go through CI/CD pipelines. No direct deployments from developer machines.**

### Rationale

1. **Security**: Prevents unauthorized deployments and ensures proper access controls
2. **Auditability**: All deployments are logged and traceable through CI/CD systems
3. **Consistency**: Ensures identical deployment process across all environments
4. **Quality Gates**: Enforces testing, security scanning, and approval workflows
5. **Rollback Capability**: CI/CD systems provide standardized rollback mechanisms

### Implementation

- **GitHub Actions**: Primary CI/CD system for all muppet deployments
- **Environment Protection**: Production deployments require approval
- **Secrets Management**: All credentials managed through GitHub Secrets
- **Infrastructure as Code**: OpenTofu configurations deployed through pipelines

### Development and Testing

- **Local Development**: Use `make run` for local testing with Docker/LocalStack
- **Infrastructure Testing**: Temporary deployment scripts allowed ONLY for:
  - Platform development and testing
  - Infrastructure module validation
  - Emergency debugging (with proper approval)

### Cleanup Tasks

- [ ] Remove `scripts/deploy.sh` from templates after infrastructure validation
- [ ] Remove deployment targets from Makefile templates
- [ ] Ensure all deployment logic is in GitHub Actions workflows
- [ ] Document emergency deployment procedures for platform team

### Enforcement

- Template validation should reject direct deployment scripts in production templates
- Code reviews must flag any direct deployment mechanisms
- Platform documentation should emphasize CI/CD-only approach
- Training materials should cover proper deployment workflows

---

**Status**: Currently allowing deployment scripts for platform development and testing.
**Target**: Remove all direct deployment capabilities from production templates.