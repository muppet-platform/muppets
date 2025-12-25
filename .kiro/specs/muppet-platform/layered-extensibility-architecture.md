# Layered Extensibility Architecture for Infrastructure Templates

## Problem with Current Recommendation

The platform-centric approach provides limited extensibility:
- ❌ Muppet developers can't customize infrastructure for their specific needs
- ❌ Power users are constrained to template-provided configurations
- ❌ Violates "Extensible by Choice" principle

## Enhanced Architecture: **Multi-Layer Extensibility**

### Design Principle
**"Progressive Infrastructure Disclosure with Multiple Extension Points"**

### Extensibility Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Muppet-Specific Overrides (Power Users)           │
│ ├── Custom modules, resources, configurations              │
│ ├── Organization-specific infrastructure patterns          │
│ └── Advanced networking, security, compliance requirements │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Template Extensions (Template Developers)         │
│ ├── Language-specific optimizations                        │
│ ├── Framework-specific configurations                      │
│ └── Runtime-specific resource allocation                   │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Platform Standards (Platform Team)                │
│ ├── Security baseline, TLS, monitoring                     │
│ ├── Networking patterns, compliance requirements           │
│ └── Cost optimization, operational excellence              │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Base Infrastructure (Auto-Generated)              │
│ ├── Core AWS resources (VPC, ALB, ECS, ECR)               │
│ ├── Standard variables, outputs, provider configuration    │
│ └── Basic resource allocation and naming conventions       │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
platform/infrastructure-templates/
├── base/                           # Layer 1: Base Infrastructure
│   ├── main.tf.template
│   ├── variables.tf.template
│   ├── outputs.tf.template
│   └── versions.tf.template
├── platform/                      # Layer 2: Platform Standards
│   ├── security.tf.template
│   ├── monitoring.tf.template
│   ├── tls.tf.template
│   └── compliance.tf.template
├── templates/                      # Layer 3: Template Extensions
│   ├── java/
│   │   ├── fargate-java.tf.template
│   │   ├── monitoring-java.tf.template
│   │   └── variables-java.tf.template
│   └── python/
│       ├── fargate-python.tf.template
│       └── monitoring-python.tf.template
└── extensions/                     # Layer 4: Extension Framework
    ├── hooks/                      # Extension points
    ├── validators/                 # Custom validation rules
    └── examples/                   # Extension examples

# Generated muppet structure
my-awesome-muppet/
├── src/                           # Application code
├── terraform/                     # Generated base infrastructure
│   ├── main.tf                   # Layers 1-3 combined
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── terraform-extensions/          # Layer 4: Muppet-specific extensions
│   ├── custom-modules/            # Custom OpenTofu modules
│   ├── overrides/                 # Variable and configuration overrides
│   ├── additional-resources/      # Additional AWS resources
│   └── organization-modules/      # Organization-specific modules
└── .muppet/                       # Muppet configuration
    ├── infrastructure.yaml        # Infrastructure customization settings
    ├── extensions.yaml            # Enabled extensions and overrides
    └── validation-rules.yaml      # Custom validation rules
```

## Extensibility Mechanisms

### 1. Simple Path (80% of developers)
**Zero configuration required** - just use the generated infrastructure as-is.

```yaml
# .muppet/infrastructure.yaml (auto-generated)
mode: simple
template: java-micronaut
auto_generate: true
platform_managed: true
```

### 2. Configuration Overrides (15% of developers)
**Parameter-based customization** without touching OpenTofu code.

```yaml
# .muppet/infrastructure.yaml
mode: configured
template: java-micronaut
auto_generate: true

overrides:
  # Resource allocation
  cpu: 2048
  memory: 4096
  min_capacity: 2
  max_capacity: 20
  
  # Environment-specific settings
  environment: production
  enable_detailed_monitoring: true
  log_retention_days: 30
  
  # Security settings
  allowed_cidr_blocks: ["10.0.0.0/8"]
  enable_waf: true
  
  # Custom domain
  custom_domain: "api.mycompany.com"
  hosted_zone_id: "Z123456789"
  
  # Database integration
  enable_rds: true
  db_instance_class: "db.t3.medium"
```

### 3. Module Extensions (4% of developers)
**Add custom modules** while preserving platform standards.

```yaml
# .muppet/infrastructure.yaml
mode: extended
template: java-micronaut
auto_generate: true

extensions:
  custom_modules:
    - name: "redis_cache"
      source: "git::https://github.com/myorg/terraform-modules.git//redis?ref=v2.0.0"
      variables:
        cluster_size: 3
        node_type: "cache.t3.micro"
    
    - name: "custom_monitoring"
      source: "./terraform-extensions/custom-modules/advanced-monitoring"
      variables:
        enable_custom_dashboards: true
        alert_email: "team@mycompany.com"

  additional_resources:
    - "terraform-extensions/additional-resources/s3-buckets.tf"
    - "terraform-extensions/additional-resources/lambda-functions.tf"
```

### 4. Full Control (1% of developers)
**Complete OpenTofu customization** with platform integration.

```yaml
# .muppet/infrastructure.yaml
mode: expert
template: java-micronaut
auto_generate: false  # Disable auto-generation
platform_integration: true  # Still use platform modules

expert_mode:
  custom_main_tf: "terraform-extensions/custom-main.tf"
  merge_platform_standards: true
  validation_required: true
  
  platform_modules:
    - security
    - monitoring
    - tls
  
  custom_modules:
    - all_files_in: "terraform-extensions/custom-modules/"
```

## Implementation Details

### Extension Point System

```python
class InfrastructureExtensionManager:
    def process_muppet_extensions(self, muppet_config: MuppetConfig) -> InfrastructureConfig:
        """Process muppet-specific infrastructure extensions."""
        
        if muppet_config.mode == "simple":
            return self.generate_simple_infrastructure(muppet_config)
        
        elif muppet_config.mode == "configured":
            base_config = self.generate_simple_infrastructure(muppet_config)
            return self.apply_configuration_overrides(base_config, muppet_config.overrides)
        
        elif muppet_config.mode == "extended":
            base_config = self.generate_simple_infrastructure(muppet_config)
            extended_config = self.add_custom_modules(base_config, muppet_config.extensions)
            return self.validate_extensions(extended_config)
        
        elif muppet_config.mode == "expert":
            return self.process_expert_mode(muppet_config)
```

### Configuration Override System

```python
class ConfigurationOverrideProcessor:
    def apply_overrides(self, base_template: str, overrides: Dict[str, Any]) -> str:
        """Apply configuration overrides to base template."""
        
        # Validate overrides don't violate platform standards
        self.validate_platform_compliance(overrides)
        
        # Apply resource allocation overrides
        template = self.apply_resource_overrides(base_template, overrides)
        
        # Apply security overrides (within allowed bounds)
        template = self.apply_security_overrides(template, overrides)
        
        # Apply monitoring and logging overrides
        template = self.apply_monitoring_overrides(template, overrides)
        
        return template
```

### Custom Module Integration

```python
class CustomModuleIntegrator:
    def integrate_custom_modules(self, base_config: InfrastructureConfig, 
                                custom_modules: List[CustomModule]) -> InfrastructureConfig:
        """Integrate custom modules with platform standards."""
        
        for module in custom_modules:
            # Validate module doesn't conflict with platform standards
            self.validate_module_compatibility(module)
            
            # Add module to infrastructure
            base_config.add_module(module)
            
            # Wire module outputs to platform inputs if needed
            self.wire_module_integration(base_config, module)
        
        return base_config
```

## Extension Examples

### Example 1: Simple Configuration Override

```yaml
# .muppet/infrastructure.yaml
mode: configured
overrides:
  # Scale up for high-traffic service
  cpu: 2048
  memory: 4096
  min_capacity: 3
  max_capacity: 50
  
  # Production monitoring
  log_retention_days: 90
  enable_detailed_monitoring: true
  
  # Custom domain
  custom_domain: "payments.mycompany.com"
```

**Generated Result**: Same infrastructure with different resource allocation and monitoring settings.

### Example 2: Redis Cache Extension

```yaml
# .muppet/infrastructure.yaml
mode: extended
extensions:
  custom_modules:
    - name: "redis_cache"
      source: "git::https://github.com/myorg/terraform-modules.git//redis?ref=v2.0.0"
      variables:
        cluster_size: 3
        node_type: "cache.t3.small"
        
  environment_variables:
    REDIS_URL: "${module.redis_cache.connection_string}"
```

**Generated Result**: Base infrastructure + Redis cluster with automatic environment variable injection.

### Example 3: Organization-Specific Security

```yaml
# .muppet/infrastructure.yaml
mode: extended
extensions:
  additional_resources:
    - "terraform-extensions/additional-resources/org-security.tf"
    
  overrides:
    # Restrict to internal network only
    allowed_cidr_blocks: ["10.0.0.0/8", "172.16.0.0/12"]
    
    # Enable organization-specific monitoring
    enable_org_monitoring: true
    org_monitoring_endpoint: "https://monitoring.myorg.internal"
```

### Example 4: Expert Mode with Custom Infrastructure

```hcl
# terraform-extensions/custom-main.tf
# Expert mode: full control with platform integration

# Use platform security module
module "platform_security" {
  source = "platform://security"
  service_name = var.muppet_name
}

# Custom multi-region setup
module "primary_region" {
  source = "./custom-modules/multi-region-fargate"
  region = "us-west-2"
  # ... custom configuration
}

module "secondary_region" {
  source = "./custom-modules/multi-region-fargate"
  region = "us-east-1"
  # ... custom configuration
}

# Custom load balancing between regions
module "global_load_balancer" {
  source = "./custom-modules/global-alb"
  primary_endpoint = module.primary_region.endpoint
  secondary_endpoint = module.secondary_region.endpoint
}
```

## Validation and Safety

### Platform Standards Enforcement

```python
class PlatformStandardsValidator:
    def validate_extension(self, extension: Extension) -> ValidationResult:
        """Ensure extensions don't violate platform standards."""
        
        violations = []
        
        # Security requirements
        if not extension.has_tls_enabled():
            violations.append("TLS must be enabled")
        
        # Monitoring requirements
        if not extension.has_monitoring():
            violations.append("Monitoring must be configured")
        
        # Cost optimization
        if extension.exceeds_cost_limits():
            violations.append("Extension exceeds cost limits")
        
        # Compliance requirements
        if not extension.meets_compliance_standards():
            violations.append("Extension doesn't meet compliance standards")
        
        return ValidationResult(violations)
```

### Extension Testing Framework

```python
class ExtensionTestFramework:
    def test_extension(self, muppet_path: Path) -> TestResult:
        """Test muppet with extensions."""
        
        # Generate infrastructure with extensions
        infrastructure = self.generate_infrastructure(muppet_path)
        
        # Validate OpenTofu syntax
        self.validate_terraform_syntax(infrastructure)
        
        # Test platform standards compliance
        self.test_platform_compliance(infrastructure)
        
        # Test extension functionality
        self.test_extension_functionality(infrastructure)
        
        # Performance and cost testing
        self.test_performance_impact(infrastructure)
        
        return TestResult(passed=True, details=test_details)
```

## Benefits of Layered Extensibility

### For 80% of Developers (Simple Path)
- ✅ Zero configuration required
- ✅ Production-ready infrastructure automatically
- ✅ Platform standards enforced
- ✅ No infrastructure knowledge needed

### For 15% of Developers (Configuration Overrides)
- ✅ Easy parameter-based customization
- ✅ No OpenTofu knowledge required
- ✅ Platform standards still enforced
- ✅ Common use cases covered (scaling, monitoring, domains)

### For 4% of Developers (Module Extensions)
- ✅ Add custom infrastructure components
- ✅ Integrate with existing organizational modules
- ✅ Platform standards automatically integrated
- ✅ Validation ensures compatibility

### For 1% of Developers (Expert Mode)
- ✅ Full OpenTofu control when needed
- ✅ Can still leverage platform modules
- ✅ Complete flexibility for complex requirements
- ✅ Advanced validation and testing support

## Migration Path

### Phase 1: Implement Configuration Overrides
- Add override system to existing Auto-Generator
- Support common customization scenarios
- Maintain backward compatibility

### Phase 2: Add Module Extension Framework
- Create extension point system
- Add custom module integration
- Build validation framework

### Phase 3: Enable Expert Mode
- Support custom OpenTofu files
- Add platform module integration
- Create advanced testing tools

This layered approach provides true "Simple by Default, Extensible by Choice" architecture where:
- **Simple**: 80% get zero-config experience
- **Extensible**: 20% can customize at appropriate levels
- **Safe**: Platform standards enforced at all levels
- **Maintainable**: Clear separation of concerns across layers