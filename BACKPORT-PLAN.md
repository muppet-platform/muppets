# Backport Plan: Template Improvements

## Overview

This plan backports all improvements made during `workflow-validation-test` validation to the platform templates, ensuring all future muppets benefit from the simplified, reliable configuration.

## Changes to Backport

### 1. Simplified Terraform Configuration ✅
**Source**: `workflow-validation-test/terraform/main.tf`
**Target**: `muppets/templates/java-micronaut/terraform/main.tf.template`

**Changes:**
- Replace complex module-based approach with direct AWS resources
- Use default VPC for 80% use case simplification
- Reduce from 600+ lines to ~300 lines (50% reduction)
- Include ARM64 architecture and Java 21 LTS optimizations

### 2. S3 Backend Integration ✅
**Source**: `workflow-validation-test/terraform/backend.tf`
**Target**: `muppets/templates/java-micronaut/terraform/backend.tf.template`

**Changes:**
- Add S3 backend configuration for shared state management
- Use pattern: `muppets/{{muppet_name}}/terraform.tfstate`
- Enable state sharing between local development and CI/CD

### 3. ECR Repository Flow Fix ✅
**Source**: `workflow-validation-test/terraform/main.tf` (data source approach)
**Target**: `muppets/templates/java-micronaut/terraform/main.tf.template`

**Changes:**
- Change from `aws_ecr_repository` resource to `data.aws_ecr_repository` data source
- CD workflow handles ECR creation, terraform references existing
- Prevents "repository already exists" conflicts

### 4. Enhanced CD Workflow ✅
**Source**: `workflow-validation-test/.github/workflows/cd.yml`
**Target**: `muppets/templates/java-micronaut/.github/workflows/cd.yml.template`

**Changes:**
- Add service URL discovery and deployment summary
- Include terraform outputs display
- Add comprehensive deployment information
- ARM64 Docker build support

### 5. Simplified Outputs ✅
**Source**: `workflow-validation-test/terraform/outputs.tf`
**Target**: `muppets/templates/java-micronaut/terraform/outputs.tf.template`

**Changes:**
- Remove module references, use direct resource references
- Add load_balancer_dns for easy copy/paste
- Include deployment_info for CI/CD integration

## Implementation Steps

### Phase 1: Terraform Configuration
1. **Update main.tf.template**
   - Replace complex module approach with simplified direct resources
   - Use `data.aws_ecr_repository` instead of resource
   - Include ARM64 and Java 21 LTS optimizations

2. **Add backend.tf.template**
   - S3 backend configuration with variable substitution
   - Pattern: `muppets/{{muppet_name}}/terraform.tfstate`

3. **Update outputs.tf.template**
   - Simplified outputs matching direct resource approach
   - Add service URL discovery outputs

### Phase 2: GitHub Workflows
1. **Update cd.yml.template**
   - Enhanced deployment summary with URLs
   - Terraform outputs display
   - ARM64 Docker build configuration

2. **Verify ci.yml.template**
   - Ensure Spotless formatting is working
   - Java 21 LTS enforcement

### Phase 3: Template Variables
1. **Update template processing**
   - Ensure all `{{muppet_name}}` variables are properly replaced
   - Test with various muppet naming patterns

2. **Validate template.yaml**
   - Confirm all new files are included in template processing

### Phase 4: Testing and Validation
1. **Create test muppet from updated template**
2. **Verify all improvements work end-to-end**
3. **Test CI/CD pipeline with new configuration**
4. **Validate service URL discovery**

## File Mapping

| Source (workflow-validation-test) | Target (template) | Status |
|-----------------------------------|-------------------|---------|
| `terraform/main.tf` | `terraform/main.tf.template` | 🔄 Pending |
| `terraform/backend.tf` | `terraform/backend.tf.template` | 🔄 Pending |
| `terraform/outputs.tf` | `terraform/outputs.tf.template` | 🔄 Pending |
| `.github/workflows/cd.yml` | `.github/workflows/cd.yml.template` | 🔄 Pending |

## Design Principles Alignment

### ✅ Simple by Default
- Default VPC usage for 80% of use cases
- Direct AWS resources instead of complex modules
- Sensible defaults built-in

### ✅ Extensible by Choice
- Power users can still customize terraform files
- Variables allow configuration overrides
- Module approach available for complex scenarios

### ✅ CI/CD-Only Deployments
- S3 backend enables shared state management
- ECR flow prevents deployment conflicts
- Clear service URL discovery

### ✅ Java 21 LTS Enforcement
- All configurations optimized for Java 21 LTS
- ARM64 architecture for better performance
- Container optimizations included

## Success Criteria

- [ ] New muppets created from template use simplified terraform
- [ ] S3 backend works for state sharing
- [ ] ECR repository conflicts resolved
- [ ] Service URLs clearly displayed in deployment logs
- [ ] All existing template features continue to work
- [ ] Template validation passes with new configuration

## Rollback Plan

If issues arise:
1. Revert template changes
2. Keep `workflow-validation-test` as reference implementation
3. Address issues and re-attempt backport
4. Maintain backward compatibility with existing muppets

## Timeline

- **Phase 1**: 1-2 hours (terraform configuration)
- **Phase 2**: 30 minutes (GitHub workflows)
- **Phase 3**: 30 minutes (template variables)
- **Phase 4**: 1 hour (testing and validation)

**Total Estimated Time**: 3-4 hours

## Next Steps

1. Execute Phase 1: Update terraform templates
2. Test with new muppet creation
3. Validate end-to-end functionality
4. Update platform documentation