# Infrastructure Design Principles

## Overview

This document outlines the core infrastructure design principles that all muppets and platform components must follow. These principles ensure consistency, maintainability, and vendor independence across the entire platform.

**Note**: This document is for **muppet developers** building applications using the platform. For **platform developers** working on the platform migration and internal processes, see the [OpenTofu Migration Guidelines](../../../.kiro/steering/opentofu-migration.md) in the workspace steering docs.

## Core Principles

### 1. OpenTofu Over Terraform

**MANDATORY**: All infrastructure-as-code MUST use OpenTofu instead of Terraform.

**Why OpenTofu?**
- **Open Source Governance**: Community-driven development with transparent governance
- **License Stability**: MPL 2.0 license provides long-term stability without vendor lock-in
- **Terraform Compatibility**: 100% compatible with Terraform 1.5.x syntax and modules
- **Active Development**: Regular releases with bug fixes and new features
- **Vendor Independence**: Not controlled by a single commercial entity

**Implementation Requirements:**
- Use `tofu` commands instead of `terraform` commands in all scripts
- Reference OpenTofu in all documentation and comments
- Configure CI/CD pipelines with OpenTofu actions
- Use OpenTofu binary for all infrastructure operations

**Examples:**
```bash
# ✅ Correct - Use OpenTofu
tofu init
tofu plan
tofu apply

# ❌ Incorrect - Don't use Terraform
terraform init
terraform plan
terraform apply
```

**CI/CD Configuration:**
```yaml
# ✅ Correct - Use OpenTofu in GitHub Actions
- name: Setup OpenTofu
  uses: opentofu/setup-opentofu@v1
  with:
    tofu_version: 1.6.0

- name: OpenTofu Plan
  run: tofu plan
```

### 2. Infrastructure as Code

**MANDATORY**: All infrastructure MUST be defined as code using OpenTofu.

- No manual resource creation through AWS console
- All infrastructure changes must go through version control
- Use shared modules for consistency
- Maintain state files in encrypted S3 buckets

### 3. Shared Module Architecture

**MANDATORY**: Use centralized, versioned OpenTofu modules for common infrastructure patterns.

- Reference shared modules from `terraform-modules/` repository
- Version modules using Git tags (e.g., `v1.2.3`)
- Avoid duplicating infrastructure code across muppets
- Contribute improvements back to shared modules

**Example:**
```hcl
module "fargate_service" {
  source = "git::https://github.com/muppet-platform/terraform-modules.git//fargate-service?ref=v1.0.0"
  
  service_name = var.muppet_name
  # ... other variables
}
```

### 4. Security by Default

**MANDATORY**: All infrastructure must implement security best practices by default.

- TLS termination at load balancer level
- Encrypted data at rest and in transit
- Least privilege IAM policies
- Security groups with minimal required access
- Regular security scanning and updates

### 5. Cost Optimization

**MANDATORY**: All infrastructure must be optimized for cost efficiency.

- Use ARM64 architecture for better cost/performance ratio
- Implement appropriate log retention policies (7 days default)
- Use auto-scaling to match demand
- Monitor and alert on cost anomalies
- Choose appropriate instance sizes and storage types

### 6. Monitoring and Observability

**MANDATORY**: All infrastructure must include comprehensive monitoring.

- CloudWatch logging with structured log format
- Health checks and alarms for all services
- Performance metrics and dashboards
- Distributed tracing where appropriate
- Cost monitoring and budgets

### 7. High Availability and Resilience

**MANDATORY**: All production infrastructure must be highly available.

- Multi-AZ deployments for critical services
- Auto-scaling and self-healing capabilities
- Circuit breaker patterns for external dependencies
- Graceful degradation under load
- Disaster recovery procedures

### 8. CI/CD-Only Deployments

**MANDATORY**: All production deployments MUST go through CI/CD pipelines. No direct deployments from developer machines.

**Rationale:**
- **Security**: Prevents unauthorized deployments and ensures proper access controls
- **Auditability**: All deployments are logged and traceable through CI/CD systems
- **Consistency**: Ensures identical deployment process across all environments
- **Quality Gates**: Enforces testing, security scanning, and approval workflows
- **Rollback Capability**: CI/CD systems provide standardized rollback mechanisms

**Implementation Requirements:**
- **GitHub Actions**: Primary CI/CD system for all muppet deployments
- **Environment Protection**: Production deployments require approval
- **Secrets Management**: All credentials managed through GitHub Secrets
- **Infrastructure as Code**: OpenTofu configurations deployed through pipelines

**Development vs Production:**
- **Local Development**: Use `make run` for local testing with Docker/LocalStack
- **Infrastructure Testing**: Temporary deployment scripts allowed ONLY for:
  - Platform development and testing
  - Infrastructure module validation
  - Emergency debugging (with proper approval)

**Enforcement:**
- Template validation should reject direct deployment scripts in production templates
- Code reviews must flag any direct deployment mechanisms
- Platform documentation should emphasize CI/CD-only approach
- Training materials should cover proper deployment workflows

## Validation and Enforcement

### Code Review Requirements

All infrastructure changes must be reviewed for:
- ✅ Uses OpenTofu instead of Terraform
- ✅ References appropriate shared modules
- ✅ Implements security best practices
- ✅ Includes monitoring and alerting
- ✅ Follows cost optimization guidelines
- ✅ Uses CI/CD-only deployment approach

### Automated Validation

CI/CD pipelines automatically validate:
- OpenTofu syntax and formatting (`tofu validate`, `tofu fmt`)
- Security scanning of infrastructure code
- Cost impact analysis
- Compliance with platform standards

### Documentation Requirements

All infrastructure code must include:
- Clear variable descriptions and validation
- Output descriptions for important values
- README with usage examples
- Architecture diagrams for complex setups

## Migration from Terraform

### For New Development
- ✅ Use OpenTofu from the start
- ✅ Reference this document in code reviews
- ✅ Configure CI/CD with OpenTofu actions

### For Existing Code
- 🔄 Update command references from `terraform` to `tofu`
- 🔄 Update documentation and comments
- 🔄 Test all modules with OpenTofu
- 🔄 Update CI/CD pipelines

### State File Compatibility
- ✅ OpenTofu can read existing Terraform state files
- ✅ No migration needed for state files
- ✅ Gradual migration is supported

## Resources and Support

### Official Resources
- **OpenTofu Documentation**: https://opentofu.org/docs/
- **Migration Guide**: https://opentofu.org/docs/intro/migration/
- **Provider Registry**: https://registry.opentofu.org/

### Internal Resources
- **Platform Team**: Contact for OpenTofu questions and support
- **Shared Modules**: https://github.com/muppet-platform/terraform-modules
- **Training Materials**: Internal OpenTofu training and best practices

### Getting Help
- **GitHub Issues**: https://github.com/opentofu/opentofu/issues
- **Community Forum**: https://discuss.opentofu.org/
- **Platform Team Slack**: #platform-engineering

## Compliance

This document is part of the platform's mandatory steering documentation. All muppets and platform components must comply with these principles. Non-compliance will be flagged during code review and must be addressed before deployment.

**Last Updated**: December 2024  
**Next Review**: March 2025  
**Owner**: Platform Engineering Team