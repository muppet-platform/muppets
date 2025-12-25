# Layered Extensibility Infrastructure Template Architecture

## Overview

The Muppet Platform implements a **Layered Extensibility Architecture** that provides four progressive levels of infrastructure customization while maintaining "Simple by Default, Extensible by Choice" principles.

## Problem Statement

The original platform-centric approach provided limited extensibility:
- ❌ Muppet developers couldn't customize infrastructure for specific needs
- ❌ Power users were constrained to template-provided configurations  
- ❌ Violated "Extensible by Choice" principle for advanced use cases

## Solution: Multi-Layer Extensibility Architecture

### Design Principle
**"Progressive Infrastructure Disclosure with Multiple Extension Points"**

### Four-Layer Extensibility System

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Expert Mode (1% - Full Control)                   │
│ ├── Custom OpenTofu files with platform integration        │
│ ├── Multi-region deployments, complex networking           │
│ └── Organization-specific compliance and security patterns │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Module Extensions (4% - Custom Components)        │
│ ├── Custom modules (Redis, databases, queues)              │
│ ├── Organization-specific infrastructure patterns          │
│ └── Additional AWS resources with platform integration     │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Configuration Overrides (15% - Parameter-based)   │
│ ├── Resource scaling (CPU, memory, auto-scaling limits)    │
│ ├── Custom domains, monitoring settings, log retention     │
│ └── Environment-specific configurations                    │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Simple Path (80% - Zero Configuration)            │
│ ├── Auto-generated infrastructure with platform standards  │
│ ├── TLS, monitoring, security, compliance built-in         │
│ └── Java 21 LTS enforcement and production-ready defaults  │
└─────────────────────────────────────────────────────────────┘
```

## Infrastructure Template Consolidation

### Consolidated Directory Structure

```
platform/infrastructure-templates/
├── base/                           # Layer 1: Base Infrastructure
│   ├── main.tf.template           # Core AWS resources (VPC, ALB, ECS, ECR)
│   ├── variables.tf.template      # Standard variables with validation
│   ├── outputs.tf.template        # Standard outputs
│   └── versions.tf.template       # Provider requirements
├── platform/                      # Layer 2: Platform Standards
│   ├── security.tf.template       # Security baseline (TLS, WAF, headers)
│   ├── monitoring.tf.template     # CloudWatch monitoring and alarms
│   ├── tls.tf.template            # TLS certificate management
│   └── compliance.tf.template     # Compliance and cost optimization
├── templates/                      # Layer 3: Template Extensions
│   ├── java/
│   │   ├── fargate-java.tf.template    # Java-optimized Fargate (Java 21 LTS)
│   │   ├── monitoring-java.tf.template # JVM-specific monitoring
│   │   └── variables-java.tf.template  # Java-specific variables
│   └── python/                     # Future: Python-specific templates
└── extensions/                     # Layer 4: Extension Framework
    ├── hooks/                      # Extension points for custom modules
    ├── validators/                 # Custom validation rules
    └── examples/                   # Extension examples and documentation

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

### Template Processing Flow

1. **Base Infrastructure** (Layer 1): Core AWS resources with sensible defaults
2. **Platform Standards** (Layer 2): Security, TLS, monitoring applied to all muppets
3. **Language Optimization** (Layer 3): Java 21 LTS enforcement, JVM tuning, framework configs
4. **Muppet Extensions** (Layer 4): Custom modules, overrides, and expert-mode customizations

## Extensibility Mechanisms

### Layer 1: Simple Path (80% of developers)
**Zero configuration required** - just use the generated infrastructure as-is.

```yaml
# .muppet/infrastructure.yaml (auto-generated)
mode: simple
template: java-micronaut
auto_generate: true
platform_managed: true
```

### Layer 2: Configuration Overrides (15% of developers)
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
```

### Layer 3: Module Extensions (4% of developers)
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
    
    - name: "postgres_db"
      source: "platform://shared-modules/rds-postgres"
      variables:
        instance_class: "db.t3.medium"
        backup_retention: 7

  environment_variables:
    REDIS_URL: "${module.redis_cache.connection_string}"
    DATABASE_URL: "${module.postgres_db.connection_string}"
```

### Layer 4: Expert Mode (1% of developers)
**Complete OpenTofu customization** with platform integration.

```yaml
# .muppet/infrastructure.yaml
mode: expert
template: java-micronaut
auto_generate: false
platform_integration: true

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

```hcl
# terraform-extensions/custom-main.tf
# Expert mode: Multi-region deployment with platform integration

# Use platform security module
module "platform_security" {
  source = "platform://security"
  service_name = var.muppet_name
}

# Custom multi-region setup
module "primary_region" {
  source = "./custom-modules/multi-region-fargate"
  region = "us-west-2"
  service_name = var.muppet_name
  security_group_id = module.platform_security.security_group_id
}

module "secondary_region" {
  source = "./custom-modules/multi-region-fargate"
  region = "us-east-1"
  service_name = var.muppet_name
  security_group_id = module.platform_security.security_group_id
}

# Global load balancing with platform TLS
module "global_load_balancer" {
  source = "./custom-modules/global-alb"
  primary_endpoint = module.primary_region.endpoint
  secondary_endpoint = module.secondary_region.endpoint
  certificate_arn = module.platform_security.certificate_arn
}
```

## Platform Standards Enforcement

### Validation Framework

```python
class PlatformStandardsValidator:
    def validate_extension(self, extension: Extension) -> ValidationResult:
        """Ensure extensions don't violate platform standards."""
        
        violations = []
        
        # Security requirements (cannot be disabled)
        if not extension.has_tls_enabled():
            violations.append("TLS termination must be enabled")
        
        if not extension.has_monitoring():
            violations.append("CloudWatch monitoring must be configured")
        
        # Java 21 LTS enforcement
        if extension.java_version and extension.java_version != "21":
            violations.append("Java 21 LTS is required, non-LTS versions not allowed")
        
        # Cost optimization
        if extension.exceeds_cost_limits():
            violations.append("Extension exceeds platform cost limits")
        
        # Compliance requirements
        if not extension.meets_compliance_standards():
            violations.append("Extension doesn't meet compliance standards")
        
        return ValidationResult(violations)
```

### Java 21 LTS Enforcement

All layers enforce Java 21 LTS compliance:
- **Layer 1**: Auto-generated infrastructure uses Java 21 LTS by default
- **Layer 2**: Configuration overrides cannot change Java version
- **Layer 3**: Custom modules validated for Java 21 LTS compatibility
- **Layer 4**: Expert mode validated to ensure Java 21 LTS enforcement

## Benefits of Layered Architecture

### For 80% of Developers (Simple Path)
- ✅ Zero configuration required
- ✅ Production-ready infrastructure automatically
- ✅ Platform standards enforced
- ✅ Java 21 LTS compliance guaranteed

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

## Implementation Architecture

### Extension Processing System

```python
class LayeredExtensibilityManager:
    def process_muppet_infrastructure(self, muppet_config: MuppetConfig) -> InfrastructureConfig:
        """Process muppet infrastructure based on extensibility layer."""
        
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

### Template Consolidation Benefits

**For Platform Team:**
- Single source of truth for infrastructure standards
- Consistent security and compliance across all muppets
- Easier to evolve infrastructure patterns
- Better control over cost optimization

**For Template Developers:**
- Focus on application concerns rather than infrastructure complexity
- Automatic compliance with platform standards
- Language-specific optimizations without infrastructure expertise
- Reduced maintenance burden

**For Muppet Developers:**
- Consistent infrastructure experience across all templates
- Production-ready defaults with security and monitoring built-in
- Progressive extensibility from zero-config to full control
- Predictable resource allocation and cost patterns

This architecture provides true "Simple by Default, Extensible by Choice" where:
- **Simple**: 80% get zero-config experience with Java 21 LTS enforcement
- **Extensible**: 20% can customize at appropriate complexity levels
- **Safe**: Platform standards enforced at all levels
- **Maintainable**: Clear separation of concerns across layers