# TLS-by-Default Implementation Plan

## Overview

This document provides a detailed implementation plan for enabling TLS-by-default for all muppet endpoints using the `s3u.dev` domain, ensuring zero code/configuration changes for current or new muppet developers.

## Implementation Phases

### Phase 1: DNS Infrastructure Setup (Week 1)
**Owner**: Platform Team  
**Risk**: Low  
**Dependencies**: None  

#### 1.1 Create s3u.dev Route 53 Hosted Zone
```bash
# Task: Set up DNS infrastructure
# Estimated Time: 2 hours
# Prerequisites: AWS Route 53 access

# Create hosted zone
aws route53 create-hosted-zone \
  --name s3u.dev \
  --caller-reference "muppet-platform-$(date +%s)" \
  --hosted-zone-config Comment="Muppet Platform TLS endpoints"

# Update domain registrar with Route 53 name servers
# (Manual step - update s3u.dev NS records with registrar)
```

**Deliverables:**
- [x] s3u.dev hosted zone created in Route 53
- [ ] Domain registrar updated with Route 53 name servers
- [ ] DNS propagation verified (dig s3u.dev NS)
- [ ] Zone ID documented for terraform variables

#### 1.2 Request Wildcard SSL Certificate
```hcl
# Task: Add wildcard certificate to platform terraform
# Estimated Time: 4 hours
# File: platform/terraform/certificates.tf (new file)

resource "aws_acm_certificate" "muppet_wildcard" {
  domain_name       = "*.s3u.dev"
  validation_method = "DNS"
  
  subject_alternative_names = [
    "s3u.dev"  # Include apex domain
  ]
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = merge(local.common_tags, {
    Name = "muppet-wildcard-certificate"
    Purpose = "muppet-tls-endpoints"
    Domain = "*.s3u.dev"
  })
}

# Validation records
resource "aws_route53_record" "muppet_wildcard_validation" {
  for_each = {
    for dvo in aws_acm_certificate.muppet_wildcard.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.s3u_dev.zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "muppet_wildcard" {
  certificate_arn         = aws_acm_certificate.muppet_wildcard.arn
  validation_record_fqdns = [for record in aws_route53_record.muppet_wildcard_validation : record.fqdn]
  
  timeouts {
    create = "10m"
  }
}

# Data source for existing zone
data "aws_route53_zone" "s3u_dev" {
  name = "s3u.dev"
}
```

**Deliverables:**
- [ ] Wildcard certificate requested and validated
- [ ] Certificate ARN available for muppet modules
- [ ] Certificate monitoring alarms configured
- [ ] Terraform state updated with certificate resources

#### 1.3 Update Platform Terraform Variables
```hcl
# Task: Add TLS variables to platform
# Estimated Time: 1 hour
# File: platform/terraform/variables.tf

# Add new variables for muppet TLS support
variable "s3u_dev_zone_id" {
  description = "Route 53 hosted zone ID for s3u.dev domain"
  type        = string
  default     = ""  # Will be populated after zone creation
}

variable "muppet_wildcard_certificate_arn" {
  description = "ARN of the wildcard certificate for muppet endpoints"
  type        = string
  default     = ""  # Will be populated after certificate creation
}

variable "enable_muppet_tls_by_default" {
  description = "Enable TLS by default for all new muppets"
  type        = bool
  default     = true
}
```

**Deliverables:**
- [ ] Platform variables updated
- [ ] Terraform plan validates successfully
- [ ] Variables documented in README

### Phase 2: Platform Service Enhancement (Week 2)
**Owner**: Platform Team  
**Risk**: Medium  
**Dependencies**: Phase 1 complete  

#### 2.1 Implement TLS Auto-Generator
```python
# Task: Create TLS configuration auto-generator
# Estimated Time: 8 hours
# File: platform/src/services/tls_auto_generator.py (new file)

import boto3
from typing import Dict, Any, Optional
from ..config import settings

class TLSAutoGenerator:
    """Automatically configures TLS for all muppets."""
    
    def __init__(self):
        self.route53_client = boto3.client('route53', region_name=settings.aws_region)
        self.acm_client = boto3.client('acm', region_name=settings.aws_region)
        self._s3u_dev_zone_id = None
        self._wildcard_cert_arn = None
    
    @property
    def s3u_dev_zone_id(self) -> str:
        """Get the s3u.dev hosted zone ID (cached)."""
        if self._s3u_dev_zone_id is None:
            self._s3u_dev_zone_id = self._discover_s3u_dev_zone_id()
        return self._s3u_dev_zone_id
    
    @property
    def wildcard_cert_arn(self) -> str:
        """Get the wildcard certificate ARN (cached)."""
        if self._wildcard_cert_arn is None:
            self._wildcard_cert_arn = self._discover_wildcard_certificate_arn()
        return self._wildcard_cert_arn
    
    def generate_muppet_tls_config(self, muppet_name: str) -> Dict[str, Any]:
        """Generate complete TLS configuration for a muppet."""
        return {
            "enable_https": True,
            "certificate_arn": self.wildcard_cert_arn,
            "domain_name": f"{muppet_name}.s3u.dev",
            "zone_id": self.s3u_dev_zone_id,
            "redirect_http_to_https": True,
            "ssl_policy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
            "create_dns_record": True
        }
    
    def _discover_s3u_dev_zone_id(self) -> str:
        """Discover the s3u.dev hosted zone ID."""
        try:
            response = self.route53_client.list_hosted_zones_by_name(DNSName="s3u.dev")
            for zone in response.get("HostedZones", []):
                if zone["Name"] == "s3u.dev.":
                    return zone["Id"].split("/")[-1]
            raise ValueError("s3u.dev hosted zone not found")
        except Exception as e:
            raise RuntimeError(f"Failed to discover s3u.dev zone ID: {e}")
    
    def _discover_wildcard_certificate_arn(self) -> str:
        """Discover the wildcard certificate ARN."""
        try:
            response = self.acm_client.list_certificates(
                CertificateStatuses=['ISSUED']
            )
            for cert in response.get("CertificateSummaryList", []):
                if cert["DomainName"] == "*.s3u.dev":
                    return cert["CertificateArn"]
            raise ValueError("*.s3u.dev certificate not found or not issued")
        except Exception as e:
            raise RuntimeError(f"Failed to discover wildcard certificate ARN: {e}")
    
    async def validate_tls_endpoint(self, muppet_name: str) -> bool:
        """Validate that a muppet's HTTPS endpoint is working."""
        import httpx
        endpoint = f"https://{muppet_name}.s3u.dev/health"
        try:
            async with httpx.AsyncClient(verify=True, timeout=10) as client:
                response = await client.get(endpoint)
                return response.status_code == 200
        except Exception:
            return False
```

**Deliverables:**
- [ ] TLSAutoGenerator class implemented
- [ ] Unit tests for TLS configuration generation
- [ ] Integration tests for AWS service discovery
- [ ] Error handling and logging implemented

#### 2.2 Enhance Muppet Lifecycle Service
```python
# Task: Update muppet creation to include TLS by default
# Estimated Time: 6 hours
# File: platform/src/services/muppet_lifecycle_service.py

from .tls_auto_generator import TLSAutoGenerator

class MuppetLifecycleService:
    """Enhanced with TLS-by-default support."""
    
    def __init__(self, tls_generator: TLSAutoGenerator = None):
        self.tls_generator = tls_generator or TLSAutoGenerator()
        # ... existing initialization
    
    async def create_muppet(
        self, 
        muppet_name: str, 
        template: str = "java-micronaut",
        enable_tls: bool = True  # New parameter, defaults to True
    ) -> Dict[str, Any]:
        """Create muppet with TLS enabled by default."""
        
        try:
            # Generate base infrastructure configuration
            base_config = await self._generate_base_infrastructure_config(muppet_name, template)
            
            # Add TLS configuration if enabled
            if enable_tls:
                tls_config = self.tls_generator.generate_muppet_tls_config(muppet_name)
                infrastructure_config = {**base_config, **tls_config}
            else:
                infrastructure_config = base_config
            
            # Create muppet infrastructure
            result = await self._create_muppet_infrastructure(muppet_name, infrastructure_config)
            
            if not result["success"]:
                return result
            
            # Prepare response with TLS information
            response = {
                "success": True,
                "muppet_name": muppet_name,
                "template": template,
                "infrastructure": result["infrastructure"],
                "endpoints": {
                    "load_balancer": f"http://{result['load_balancer_dns']}"
                }
            }
            
            # Add HTTPS endpoint if TLS is enabled
            if enable_tls:
                response["endpoints"]["https"] = f"https://{muppet_name}.s3u.dev"
                response["tls"] = {
                    "enabled": True,
                    "certificate_arn": tls_config["certificate_arn"],
                    "domain_name": tls_config["domain_name"],
                    "ssl_policy": tls_config["ssl_policy"]
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to create muppet {muppet_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "muppet_name": muppet_name
            }
    
    async def migrate_existing_muppet_to_tls(self, muppet_name: str) -> Dict[str, Any]:
        """Migrate an existing muppet to use TLS."""
        try:
            # Generate TLS configuration
            tls_config = self.tls_generator.generate_muppet_tls_config(muppet_name)
            
            # Update muppet's terraform variables
            await self._update_muppet_terraform_vars(muppet_name, tls_config)
            
            # Trigger CD pipeline to apply changes
            await self._trigger_muppet_cd_pipeline(muppet_name)
            
            return {
                "success": True,
                "muppet_name": muppet_name,
                "message": "TLS migration initiated. Re-run CD pipeline to complete.",
                "https_endpoint": f"https://{muppet_name}.s3u.dev",
                "tls_config": tls_config
            }
            
        except Exception as e:
            logger.error(f"Failed to migrate muppet {muppet_name} to TLS: {e}")
            return {
                "success": False,
                "error": str(e),
                "muppet_name": muppet_name
            }
```

**Deliverables:**
- [ ] Enhanced muppet creation with TLS defaults
- [ ] Migration function for existing muppets
- [ ] Comprehensive error handling
- [ ] Unit and integration tests

#### 2.3 Add TLS Management API Endpoints
```python
# Task: Add API endpoints for TLS management
# Estimated Time: 4 hours
# File: platform/src/routers/tls_router.py (new file)

from fastapi import APIRouter, HTTPException, Depends
from ..services.tls_auto_generator import TLSAutoGenerator
from ..services.muppet_lifecycle_service import MuppetLifecycleService

router = APIRouter(prefix="/api/v1/tls", tags=["TLS Management"])

@router.get("/certificate/status")
async def get_certificate_status():
    """Get wildcard certificate status."""
    try:
        tls_generator = TLSAutoGenerator()
        cert_arn = tls_generator.wildcard_cert_arn
        # Get certificate details from ACM
        # Return certificate status, expiry, etc.
        return {
            "certificate_arn": cert_arn,
            "status": "ISSUED",
            "domain": "*.s3u.dev"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/muppet/{muppet_name}/migrate")
async def migrate_muppet_to_tls(muppet_name: str):
    """Migrate an existing muppet to use TLS."""
    try:
        lifecycle_service = MuppetLifecycleService()
        result = await lifecycle_service.migrate_existing_muppet_to_tls(muppet_name)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/muppet/{muppet_name}/validate")
async def validate_muppet_tls(muppet_name: str):
    """Validate a muppet's TLS endpoint."""
    try:
        tls_generator = TLSAutoGenerator()
        is_valid = await tls_generator.validate_tls_endpoint(muppet_name)
        
        return {
            "muppet_name": muppet_name,
            "https_endpoint": f"https://{muppet_name}.s3u.dev",
            "tls_valid": is_valid,
            "validated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/muppets/status")
async def get_all_muppets_tls_status():
    """Get TLS status for all muppets."""
    try:
        # Discover all muppets from GitHub organization
        # Validate TLS for each muppet
        # Return comprehensive status report
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Deliverables:**
- [ ] TLS management API endpoints
- [ ] API documentation updated
- [ ] Integration tests for API endpoints
- [ ] Error handling and validation

### Phase 3: Terraform Module Updates (Week 3)
**Owner**: Platform Team  
**Risk**: Medium  
**Dependencies**: Phase 2 complete  

#### 3.1 Update Muppet Module Variables
```hcl
# Task: Update muppet module to support TLS by default
# Estimated Time: 4 hours
# File: terraform-modules/muppet-java-micronaut/variables.tf

# Update existing variables
variable "enable_https" {
  description = "Enable HTTPS listener on the load balancer"
  type        = bool
  default     = true  # Changed from false to true
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener"
  type        = string
  default     = ""  # Will be auto-populated by platform
}

# Add new variables for TLS support
variable "domain_name" {
  description = "Custom domain name for the muppet (e.g., muppet-name.s3u.dev)"
  type        = string
  default     = ""
  
  validation {
    condition = var.domain_name == "" || can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]\\.[a-z0-9][a-z0-9-]*[a-z0-9]$", var.domain_name))
    error_message = "Domain name must be a valid FQDN (e.g., muppet-name.s3u.dev)."
  }
}

variable "zone_id" {
  description = "Route 53 hosted zone ID for DNS record creation"
  type        = string
  default     = ""
}

variable "redirect_http_to_https" {
  description = "Redirect HTTP traffic to HTTPS"
  type        = bool
  default     = true
}

variable "ssl_policy" {
  description = "SSL policy for HTTPS listener"
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  
  validation {
    condition = contains([
      "ELBSecurityPolicy-TLS13-1-2-2021-06",
      "ELBSecurityPolicy-TLS-1-2-2017-01",
      "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"
    ], var.ssl_policy)
    error_message = "SSL policy must be a valid ELB security policy."
  }
}

variable "create_dns_record" {
  description = "Create Route 53 DNS record for custom domain"
  type        = bool
  default     = false  # Only create if domain_name and zone_id are provided
}
```

**Deliverables:**
- [ ] Updated variable definitions
- [ ] Variable validation rules
- [ ] Backward compatibility maintained
- [ ] Documentation updated

#### 3.2 Add DNS Record Management
```hcl
# Task: Add DNS record creation to muppet module
# Estimated Time: 3 hours
# File: terraform-modules/muppet-java-micronaut/dns.tf (new file)

# DNS record for custom domain (conditional)
resource "aws_route53_record" "muppet_domain" {
  count = var.create_dns_record && var.domain_name != "" && var.zone_id != "" ? 1 : 0
  
  zone_id = var.zone_id
  name    = var.domain_name
  type    = "A"
  
  alias {
    name                   = module.fargate_service.load_balancer_dns_name
    zone_id                = module.fargate_service.load_balancer_zone_id
    evaluate_target_health = true
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.muppet_name}-dns-record"
    Domain = var.domain_name
    MuppetName = var.muppet_name
  })
}

# Output the DNS record information
output "dns_record_name" {
  description = "DNS record name (if created)"
  value       = var.create_dns_record && var.domain_name != "" ? var.domain_name : null
}

output "dns_record_fqdn" {
  description = "Fully qualified domain name (if DNS record created)"
  value       = var.create_dns_record && var.domain_name != "" ? aws_route53_record.muppet_domain[0].fqdn : null
}

output "https_endpoint" {
  description = "HTTPS endpoint URL (if TLS enabled)"
  value       = var.enable_https && var.domain_name != "" ? "https://${var.domain_name}" : null
}
```

**Deliverables:**
- [ ] DNS record creation logic
- [ ] Conditional resource creation
- [ ] Output values for endpoints
- [ ] Integration with fargate-service module

#### 3.3 Update Fargate Service Module for TLS
```hcl
# Task: Enhance fargate-service module for TLS support
# Estimated Time: 6 hours
# File: terraform-modules/fargate-service/load_balancer.tf

# Enhanced HTTPS listener with better configuration
resource "aws_lb_listener" "https" {
  count = var.enable_https && var.certificate_arn != "" ? 1 : 0
  
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn
  
  default_action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.main.arn
        weight = 100
      }
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.service_name}-https-listener"
    Protocol = "HTTPS"
    Port = "443"
  })
}

# HTTP listener with conditional behavior
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  # Conditional action: redirect to HTTPS if TLS enabled, otherwise forward
  default_action {
    type = var.enable_https && var.redirect_http_to_https ? "redirect" : "forward"
    
    # Forward action when HTTPS is disabled
    dynamic "forward" {
      for_each = var.enable_https && var.redirect_http_to_https ? [] : [1]
      content {
        target_group {
          arn    = aws_lb_target_group.main.arn
          weight = 100
        }
      }
    }
    
    # Redirect action when HTTPS is enabled
    dynamic "redirect" {
      for_each = var.enable_https && var.redirect_http_to_https ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }
  
  tags = merge(var.tags, {
    Name = "${var.service_name}-http-listener"
    Protocol = "HTTP"
    Port = "80"
    RedirectToHTTPS = var.enable_https && var.redirect_http_to_https ? "true" : "false"
  })
}

# Add TLS-related variables to fargate-service module
variable "ssl_policy" {
  description = "SSL policy for HTTPS listener"
  type        = string
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}

variable "redirect_http_to_https" {
  description = "Redirect HTTP traffic to HTTPS"
  type        = bool
  default     = true
}

# Add TLS-related outputs
output "https_listener_arn" {
  description = "ARN of the HTTPS listener (if created)"
  value       = var.enable_https && var.certificate_arn != "" ? aws_lb_listener.https[0].arn : null
}

output "ssl_policy" {
  description = "SSL policy used for HTTPS listener"
  value       = var.enable_https ? var.ssl_policy : null
}
```

**Deliverables:**
- [ ] Enhanced HTTPS listener configuration
- [ ] Conditional HTTP→HTTPS redirect
- [ ] TLS-related outputs
- [ ] Backward compatibility maintained

### Phase 4: Testing and Validation (Week 4)
**Owner**: Platform Team  
**Risk**: Low  
**Dependencies**: Phase 3 complete  

#### 4.1 Create Test Muppet with TLS
```bash
# Task: Create and validate a test muppet with TLS
# Estimated Time: 4 hours

# Create test muppet using platform API
curl -X POST "https://muppet-platform.s3u.dev/api/v1/muppets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "tls-test-muppet",
    "template": "java-micronaut",
    "enable_tls": true
  }'

# Validate HTTPS endpoint
curl -v https://tls-test-muppet.s3u.dev/health

# Validate HTTP→HTTPS redirect
curl -v http://tls-test-muppet.s3u.dev/health

# Validate certificate
openssl s_client -connect tls-test-muppet.s3u.dev:443 -servername tls-test-muppet.s3u.dev
```

**Deliverables:**
- [ ] Test muppet created successfully
- [ ] HTTPS endpoint accessible
- [ ] HTTP redirect working
- [ ] Certificate validation passed
- [ ] DNS resolution working

#### 4.2 Automated Testing Suite
```python
# Task: Create comprehensive test suite for TLS functionality
# Estimated Time: 8 hours
# File: platform/tests/test_tls_integration.py

import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, patch

class TestTLSIntegration:
    """Integration tests for TLS-by-default functionality."""
    
    @pytest.mark.asyncio
    async def test_create_muppet_with_tls_default(self):
        """Test that new muppets get TLS by default."""
        # Test muppet creation with TLS enabled
        # Verify infrastructure configuration
        # Validate HTTPS endpoint
        pass
    
    @pytest.mark.asyncio
    async def test_tls_certificate_discovery(self):
        """Test TLS certificate discovery logic."""
        # Mock AWS ACM responses
        # Test certificate ARN discovery
        # Verify error handling
        pass
    
    @pytest.mark.asyncio
    async def test_dns_record_creation(self):
        """Test DNS record creation for muppets."""
        # Mock Route 53 responses
        # Test DNS record creation
        # Verify record configuration
        pass
    
    @pytest.mark.asyncio
    async def test_https_endpoint_validation(self):
        """Test HTTPS endpoint validation."""
        # Test valid HTTPS endpoints
        # Test invalid endpoints
        # Test timeout handling
        pass
    
    @pytest.mark.asyncio
    async def test_existing_muppet_migration(self):
        """Test migration of existing muppets to TLS."""
        # Test migration API endpoint
        # Verify configuration updates
        # Test rollback scenarios
        pass

# Load testing for TLS endpoints
class TestTLSPerformance:
    """Performance tests for TLS endpoints."""
    
    @pytest.mark.asyncio
    async def test_https_response_time(self):
        """Test HTTPS endpoint response times."""
        # Measure HTTPS vs HTTP response times
        # Verify acceptable performance overhead
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_tls_requests(self):
        """Test concurrent HTTPS requests."""
        # Test multiple concurrent HTTPS requests
        # Verify no performance degradation
        pass
```

**Deliverables:**
- [ ] Comprehensive test suite
- [ ] Integration tests for all TLS components
- [ ] Performance tests for HTTPS endpoints
- [ ] Error handling tests
- [ ] Mock tests for AWS services

#### 4.3 Security Validation
```bash
# Task: Validate TLS security configuration
# Estimated Time: 4 hours

# SSL Labs test (if publicly accessible)
curl -s "https://api.ssllabs.com/api/v3/analyze?host=tls-test-muppet.s3u.dev"

# Test TLS configuration with testssl.sh
./testssl.sh https://tls-test-muppet.s3u.dev

# Validate certificate chain
openssl s_client -connect tls-test-muppet.s3u.dev:443 -showcerts

# Test for common vulnerabilities
nmap --script ssl-enum-ciphers -p 443 tls-test-muppet.s3u.dev
```

**Deliverables:**
- [ ] SSL Labs A+ rating (if applicable)
- [ ] TLS 1.3 support verified
- [ ] No weak ciphers or protocols
- [ ] Certificate chain validation
- [ ] Security scan results documented

### Phase 5: Existing Muppet Migration (Week 5)
**Owner**: Platform Team  
**Risk**: Medium  
**Dependencies**: Phase 4 complete  

#### 5.1 Discover Existing Muppets
```python
# Task: Create script to discover and catalog existing muppets
# Estimated Time: 4 hours
# File: scripts/discover-existing-muppets.py

import asyncio
import json
from platform.src.integrations.github_client import GitHubClient

async def discover_existing_muppets():
    """Discover all existing muppets in the organization."""
    github_client = GitHubClient()
    
    # Get all repositories in muppet-platform organization
    repos = await github_client.list_organization_repositories("muppet-platform")
    
    muppets = []
    for repo in repos:
        # Skip platform repositories
        if repo["name"] in ["muppets", "terraform-modules"]:
            continue
        
        # Check if repository is a muppet (has muppet.yaml)
        try:
            muppet_config = await github_client.get_file_content(
                repo["name"], "muppet.yaml"
            )
            if muppet_config:
                muppets.append({
                    "name": repo["name"],
                    "repository": repo["html_url"],
                    "created_at": repo["created_at"],
                    "has_tls": False,  # Will be determined later
                    "migration_status": "pending"
                })
        except Exception:
            # Not a muppet repository
            continue
    
    # Save discovery results
    with open("existing-muppets.json", "w") as f:
        json.dump(muppets, f, indent=2)
    
    print(f"Discovered {len(muppets)} existing muppets")
    return muppets

if __name__ == "__main__":
    asyncio.run(discover_existing_muppets())
```

**Deliverables:**
- [ ] Complete inventory of existing muppets
- [ ] Migration status tracking
- [ ] Muppet categorization (active/inactive)
- [ ] Current TLS status assessment

#### 5.2 Batch Migration Script
```python
# Task: Create batch migration script for existing muppets
# Estimated Time: 6 hours
# File: scripts/migrate-muppets-to-tls.py

import asyncio
import json
from typing import List, Dict
from platform.src.services.muppet_lifecycle_service import MuppetLifecycleService

class MuppetTLSMigrator:
    """Batch migrate existing muppets to TLS."""
    
    def __init__(self):
        self.lifecycle_service = MuppetLifecycleService()
        self.migration_results = []
    
    async def migrate_all_muppets(self, muppets: List[Dict], batch_size: int = 5):
        """Migrate all muppets to TLS in batches."""
        
        for i in range(0, len(muppets), batch_size):
            batch = muppets[i:i + batch_size]
            print(f"Migrating batch {i//batch_size + 1}: {[m['name'] for m in batch]}")
            
            # Process batch concurrently
            tasks = [self.migrate_single_muppet(muppet) for muppet in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for muppet, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    self.migration_results.append({
                        "muppet_name": muppet["name"],
                        "success": False,
                        "error": str(result)
                    })
                else:
                    self.migration_results.append(result)
            
            # Wait between batches to avoid overwhelming AWS APIs
            await asyncio.sleep(30)
        
        return self.migration_results
    
    async def migrate_single_muppet(self, muppet: Dict) -> Dict:
        """Migrate a single muppet to TLS."""
        muppet_name = muppet["name"]
        
        try:
            # Check if muppet already has TLS
            if await self._muppet_has_tls(muppet_name):
                return {
                    "muppet_name": muppet_name,
                    "success": True,
                    "message": "Already has TLS enabled",
                    "action": "skipped"
                }
            
            # Migrate to TLS
            result = await self.lifecycle_service.migrate_existing_muppet_to_tls(muppet_name)
            
            if result["success"]:
                # Wait for DNS propagation
                await asyncio.sleep(60)
                
                # Validate HTTPS endpoint
                tls_valid = await self.lifecycle_service.tls_generator.validate_tls_endpoint(muppet_name)
                
                return {
                    "muppet_name": muppet_name,
                    "success": True,
                    "https_endpoint": f"https://{muppet_name}.s3u.dev",
                    "tls_valid": tls_valid,
                    "action": "migrated"
                }
            else:
                return {
                    "muppet_name": muppet_name,
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "action": "failed"
                }
                
        except Exception as e:
            return {
                "muppet_name": muppet_name,
                "success": False,
                "error": str(e),
                "action": "failed"
            }
    
    async def _muppet_has_tls(self, muppet_name: str) -> bool:
        """Check if muppet already has TLS enabled."""
        try:
            return await self.lifecycle_service.tls_generator.validate_tls_endpoint(muppet_name)
        except Exception:
            return False

async def main():
    """Main migration function."""
    # Load existing muppets
    with open("existing-muppets.json", "r") as f:
        muppets = json.load(f)
    
    # Filter active muppets only
    active_muppets = [m for m in muppets if m.get("status") != "inactive"]
    
    print(f"Migrating {len(active_muppets)} active muppets to TLS")
    
    # Migrate in batches
    migrator = MuppetTLSMigrator()
    results = await migrator.migrate_all_muppets(active_muppets, batch_size=3)
    
    # Save results
    with open("migration-results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    successful = len([r for r in results if r["success"]])
    failed = len([r for r in results if not r["success"]])
    
    print(f"\nMigration Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Deliverables:**
- [ ] Batch migration script
- [ ] Migration progress tracking
- [ ] Error handling and retry logic
- [ ] Migration results reporting
- [ ] Rollback capability

#### 5.3 Communication and Coordination
```markdown
# Task: Communicate migration plan to muppet teams
# Estimated Time: 2 hours

## Email Template for Muppet Teams

Subject: Action Required: TLS-by-Default Migration for Your Muppet

Dear Muppet Development Team,

The Platform Team is rolling out TLS-by-default for all muppet endpoints to enhance security. Your muppet will soon have an HTTPS endpoint at:

https://your-muppet-name.s3u.dev

## What You Need to Do

1. **Re-run your CD pipeline** after receiving this notification
2. **Update any hardcoded HTTP URLs** in your application (if any)
3. **Test your HTTPS endpoint** to ensure everything works correctly

## What We've Done for You

- ✅ Created SSL certificate for your muppet
- ✅ Set up DNS record (your-muppet-name.s3u.dev)
- ✅ Updated your infrastructure configuration
- ✅ Configured automatic HTTP→HTTPS redirect

## Timeline

- **Migration Date**: [DATE]
- **Action Required By**: [DATE + 7 days]
- **Support Available**: Platform team Slack channel

## No Code Changes Required

This migration requires NO changes to your application code. Your existing HTTP endpoint will continue to work and automatically redirect to HTTPS.

## Questions?

Contact the Platform Team in #platform-support or email platform-team@company.com

Best regards,
Platform Team
```

**Deliverables:**
- [ ] Communication plan created
- [ ] Email templates prepared
- [ ] Slack notifications scheduled
- [ ] Documentation updated
- [ ] Support process defined

### Phase 6: Monitoring and Validation (Week 6)
**Owner**: Platform Team  
**Risk**: Low  
**Dependencies**: Phase 5 complete  

#### 6.1 TLS Monitoring Dashboard
```python
# Task: Create monitoring dashboard for TLS endpoints
# Estimated Time: 6 hours
# File: platform/src/monitoring/tls_dashboard.py

import boto3
from typing import Dict, List
from ..services.tls_auto_generator import TLSAutoGenerator

class TLSMonitoringDashboard:
    """Monitoring dashboard for TLS endpoints."""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.tls_generator = TLSAutoGenerator()
    
    async def create_tls_dashboard(self):
        """Create CloudWatch dashboard for TLS monitoring."""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/CertificateManager", "DaysToExpiry", "CertificateArn", self.tls_generator.wildcard_cert_arn]
                        ],
                        "period": 86400,
                        "stat": "Average",
                        "region": "us-west-2",
                        "title": "Wildcard Certificate Days to Expiry"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "muppet-*", {"stat": "Average"}],
                            [".", "HTTPCode_Target_2XX_Count", ".", ".", {"stat": "Sum"}],
                            [".", "HTTPCode_Target_4XX_Count", ".", ".", {"stat": "Sum"}],
                            [".", "HTTPCode_Target_5XX_Count", ".", ".", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-west-2",
                        "title": "Muppet HTTPS Endpoints Health"
                    }
                }
            ]
        }
        
        self.cloudwatch.put_dashboard(
            DashboardName="MuppetTLSMonitoring",
            DashboardBody=json.dumps(dashboard_body)
        )
    
    async def create_certificate_expiry_alarm(self):
        """Create alarm for certificate expiry."""
        
        self.cloudwatch.put_metric_alarm(
            AlarmName="MuppetWildcardCertificateExpiry",
            ComparisonOperator="LessThanThreshold",
            EvaluationPeriods=1,
            MetricName="DaysToExpiry",
            Namespace="AWS/CertificateManager",
            Period=86400,
            Statistic="Average",
            Threshold=30.0,
            ActionsEnabled=True,
            AlarmActions=[
                # Add SNS topic ARN for notifications
            ],
            AlarmDescription="Muppet wildcard certificate expires in less than 30 days",
            Dimensions=[
                {
                    "Name": "CertificateArn",
                    "Value": self.tls_generator.wildcard_cert_arn
                }
            ]
        )
```

**Deliverables:**
- [ ] TLS monitoring dashboard
- [ ] Certificate expiry alarms
- [ ] HTTPS endpoint health checks
- [ ] Performance monitoring
- [ ] Alert notifications configured

#### 6.2 Automated TLS Validation
```python
# Task: Create automated TLS validation service
# Estimated Time: 4 hours
# File: platform/src/services/tls_validator.py

import asyncio
import httpx
from typing import Dict, List
from datetime import datetime, timedelta

class TLSValidator:
    """Automated TLS validation for all muppets."""
    
    async def validate_all_muppets(self) -> Dict[str, Dict]:
        """Validate TLS for all muppets."""
        # Discover all muppets
        muppets = await self._discover_all_muppets()
        
        # Validate each muppet
        results = {}
        for muppet_name in muppets:
            results[muppet_name] = await self._validate_muppet_tls(muppet_name)
        
        return results
    
    async def _validate_muppet_tls(self, muppet_name: str) -> Dict:
        """Validate TLS for a single muppet."""
        endpoint = f"https://{muppet_name}.s3u.dev"
        
        try:
            async with httpx.AsyncClient(verify=True, timeout=10) as client:
                # Test HTTPS endpoint
                response = await client.get(f"{endpoint}/health")
                https_status = response.status_code == 200
                
                # Test HTTP redirect
                http_response = await client.get(f"http://{muppet_name}.s3u.dev/health", follow_redirects=False)
                redirect_status = http_response.status_code in [301, 302, 307, 308]
                
                return {
                    "https_working": https_status,
                    "http_redirect_working": redirect_status,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "certificate_valid": True,  # If we got here, cert is valid
                    "last_checked": datetime.utcnow().isoformat(),
                    "status": "healthy" if https_status and redirect_status else "unhealthy"
                }
                
        except Exception as e:
            return {
                "https_working": False,
                "http_redirect_working": False,
                "response_time_ms": None,
                "certificate_valid": False,
                "last_checked": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "error"
            }

# Scheduled validation job
async def scheduled_tls_validation():
    """Run TLS validation every hour."""
    validator = TLSValidator()
    
    while True:
        try:
            results = await validator.validate_all_muppets()
            
            # Log results
            healthy_count = len([r for r in results.values() if r["status"] == "healthy"])
            total_count = len(results)
            
            print(f"TLS Validation: {healthy_count}/{total_count} muppets healthy")
            
            # Store results in database or send to monitoring system
            # await store_validation_results(results)
            
        except Exception as e:
            print(f"TLS validation failed: {e}")
        
        # Wait 1 hour
        await asyncio.sleep(3600)
```

**Deliverables:**
- [ ] Automated TLS validation service
- [ ] Scheduled validation jobs
- [ ] Health status reporting
- [ ] Error detection and alerting
- [ ] Performance metrics collection

## Risk Management

### High-Risk Items
1. **DNS Propagation Delays**: DNS changes may take time to propagate
   - **Mitigation**: Use short TTL values, validate before proceeding
   
2. **Certificate Validation Failures**: ACM certificate validation may fail
   - **Mitigation**: Automated retry logic, manual validation fallback
   
3. **Existing Muppet Compatibility**: Some muppets may have hardcoded HTTP URLs
   - **Mitigation**: Maintain HTTP endpoints during transition period

### Medium-Risk Items
1. **Performance Impact**: HTTPS may add latency
   - **Mitigation**: Use modern TLS policies, monitor performance
   
2. **Migration Coordination**: Coordinating with multiple muppet teams
   - **Mitigation**: Clear communication, phased rollout

### Low-Risk Items
1. **Certificate Renewal**: ACM handles automatic renewal
   - **Mitigation**: Monitoring and alerting for renewal issues

## Success Criteria

### Technical Success
- [ ] 100% of new muppets get HTTPS endpoints automatically
- [ ] 100% of existing muppets migrated successfully
- [ ] All HTTPS endpoints return valid certificates
- [ ] HTTP→HTTPS redirects work for all muppets
- [ ] DNS resolution works for all muppet subdomains

### Developer Experience Success
- [ ] Zero code changes required for muppet developers
- [ ] Migration requires only CD pipeline re-run
- [ ] No increase in support tickets related to TLS
- [ ] Documentation updated and clear

### Security Success
- [ ] All muppet traffic encrypted in transit
- [ ] TLS 1.3 support enabled
- [ ] No weak ciphers or protocols
- [ ] Certificate monitoring and alerting active

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | Week 1 | DNS infrastructure, wildcard certificate |
| Phase 2 | Week 2 | Platform service enhancements |
| Phase 3 | Week 3 | Terraform module updates |
| Phase 4 | Week 4 | Testing and validation |
| Phase 5 | Week 5 | Existing muppet migration |
| Phase 6 | Week 6 | Monitoring and validation |

**Total Duration**: 6 weeks  
**Team Size**: 2-3 platform engineers  
**Estimated Effort**: 120-150 hours  

## Post-Implementation

### Maintenance Tasks
- [ ] Monitor certificate expiry and renewal
- [ ] Regular TLS endpoint validation
- [ ] Performance monitoring and optimization
- [ ] Security policy updates as needed

### Future Enhancements
- [ ] Custom domain support for enterprise customers
- [ ] Advanced TLS policies (HSTS, certificate pinning)
- [ ] TLS 1.3 optimization
- [ ] Certificate transparency monitoring

This implementation plan ensures a smooth, risk-managed rollout of TLS-by-default while maintaining the platform's core principle of "Simple by Default, Extensible by Choice."