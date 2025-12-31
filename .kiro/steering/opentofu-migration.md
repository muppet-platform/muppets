---
inclusion: always
---

# OpenTofu Migration Guidelines

## Platform Migration: Terraform → OpenTofu

**Note**: For platform developers only. Muppet developers see shared infrastructure docs.

## Why OpenTofu?
- Open source governance with MPL 2.0 license
- 100% Terraform 1.5.x compatibility
- Vendor independence and active development

## Command Migration
```bash
# Old → New
terraform init    → tofu init
terraform plan    → tofu plan
terraform apply   → tofu apply
terraform destroy → tofu destroy
```

## Installation
```bash
# macOS
brew install opentofu

# Linux
curl -fsSL https://get.opentofu.org/install-opentofu.sh | sh

# Verify
tofu version
```

## Platform Integration
- All platform scripts use `tofu` commands
- CI/CD pipelines configured for OpenTofu
- Shared modules developed with OpenTofu
- State files compatible (no migration needed)
```

**Verification:**
```bash
tofu version
# Should show: OpenTofu v1.6.x
```

### CI/CD Integration

**GitHub Actions:**
```yaml
- name: Setup OpenTofu
  uses: opentofu/setup-opentofu@v1
  with:
    tofu_version: 1.6.0

- name: OpenTofu Init
  run: tofu init

- name: OpenTofu Plan
  run: tofu plan

- name: OpenTofu Apply
  run: tofu apply -auto-approve
```

## Command Migration

All `terraform` commands are replaced with `tofu` commands:

```bash
# Old (Terraform)          # New (OpenTofu)
terraform init             tofu init
terraform plan             tofu plan
terraform apply            tofu apply
terraform destroy          tofu destroy
terraform validate         tofu validate
terraform fmt              tofu fmt
terraform show             tofu show
terraform output           tofu output
```

## Module Development Guidelines

### Module Structure

OpenTofu modules follow the same structure as Terraform modules:

```
terraform-modules/{module-name}/
├── main.tf                 # Primary resource definitions
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── versions.tf             # Provider requirements
├── README.md               # Module documentation
└── examples/               # Usage examples
    └── basic/
        ├── main.tf
        └── variables.tf
```

### Provider Configuration

**versions.tf:**
```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### Module Versioning

- Use semantic versioning (e.g., v1.2.3)
- Tag releases in Git for version tracking
- Update module references in muppet templates when versions change

## Platform Integration

### Infrastructure Manager Updates

The platform's Infrastructure Manager component has been updated to use OpenTofu:

```python
# Execute OpenTofu commands
async def run_opentofu(self, command: str, workspace_path: str) -> dict:
    """Execute OpenTofu command in specified workspace"""
    cmd = f"tofu {command}"
    # ... implementation
```

### Template Generation

Muppet templates now generate OpenTofu configurations:

```hcl
# Generated main.tf for muppets
module "fargate_service" {
  source = "git::https://github.com/muppet-platform/terraform-modules.git//fargate-service?ref=v1.0.0"
  
  service_name = var.muppet_name
  # ... other variables
}
```

## Testing Strategy

### Module Testing

**Validation Tests:**
```bash
# In each module directory
tofu init
tofu validate
tofu fmt -check
```

**Integration Tests with Terratest:**
```go
func TestFargateServiceModule(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../examples/basic",
        TerraformBinary: "tofu",  // Use OpenTofu instead of Terraform
    }
    
    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)
    
    // Test outputs and resources
}
```

### Platform Testing

Property-based tests validate OpenTofu module integration:

```python
@given(muppet_name=muppet_names(), template_type=template_types())
def test_opentofu_module_versioning(muppet_name: str, template_type: str):
    """Test that OpenTofu modules maintain version consistency"""
    # Test implementation
```

## Migration Checklist

### For New Development

- ✅ Use `tofu` commands in all scripts
- ✅ Reference OpenTofu in documentation
- ✅ Configure CI/CD with OpenTofu actions
- ✅ Update module references to use OpenTofu

### For Existing Code

- ✅ Update command references from `terraform` to `tofu`
- ✅ Update documentation and comments
- ✅ Test all modules with OpenTofu
- ✅ Update CI/CD pipelines

## Troubleshooting

### Common Issues

**1. Command Not Found:**
```bash
# Error: tofu: command not found
# Solution: Install OpenTofu using package manager
brew install opentofu
```

**2. State File Compatibility:**
```bash
# OpenTofu can read existing Terraform state files
# No migration needed for state files
tofu plan  # Works with existing .tfstate files
```

**3. Provider Compatibility:**
```bash
# All Terraform providers work with OpenTofu
# No changes needed to provider configurations
```

### Getting Help

- **OpenTofu Documentation**: https://opentofu.org/docs/
- **GitHub Issues**: https://github.com/opentofu/opentofu/issues
- **Community Forum**: https://discuss.opentofu.org/

## Best Practices

### Development Workflow

1. **Local Development:**
   ```bash
   tofu init
   tofu plan
   tofu apply
   ```

2. **Code Review:**
   - Always run `tofu fmt` before committing
   - Include `tofu plan` output in pull requests
   - Validate modules with `tofu validate`

3. **Testing:**
   - Test modules in isolation
   - Use Terratest for integration testing
   - Validate against multiple AWS regions

### Security Considerations

- Store state files in encrypted S3 buckets
- Use IAM roles with minimal required permissions
- Enable state file locking with DynamoDB
- Never commit sensitive values to Git

### Performance Optimization

- Use remote state for team collaboration
- Enable parallel execution where safe
- Cache provider plugins in CI/CD
- Use workspaces for environment separation

## Future Considerations

### OpenTofu Roadmap

- **Registry Support**: OpenTofu registry for module sharing
- **Enhanced Features**: New features beyond Terraform compatibility
- **Performance Improvements**: Faster execution and better resource handling

### Platform Evolution

- **Module Registry**: Consider hosting private OpenTofu module registry
- **Advanced Features**: Leverage OpenTofu-specific features as they become available
- **Community Contributions**: Contribute improvements back to OpenTofu project

## Resources

- **OpenTofu Official Site**: https://opentofu.org/
- **Migration Guide**: https://opentofu.org/docs/intro/migration/
- **Provider Registry**: https://registry.opentofu.org/
- **Community Resources**: https://github.com/opentofu/opentofu