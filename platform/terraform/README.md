# Muppet Platform Terraform Configuration

This directory contains the Terraform/OpenTofu infrastructure configuration for the Muppet Platform.

## Configuration

### HTTPS and Domain Configuration

The platform supports automatic HTTPS configuration using AWS Certificate Manager (ACM) and Route 53.

#### Route 53 Configuration

**s3u.dev Domain Zone ID**: `/hostedzone/Z01284891NRMNOB6Q86G3`

This zone ID is required for the `parent_zone_id` variable when enabling HTTPS.

#### Variables

Key variables for HTTPS configuration:

- `enable_https` (bool, default: true) - Enable HTTPS with ACM certificate
- `domain_name` (string, default: "muppet-platform.s3u.dev") - Platform domain name
- `parent_zone_id` (string, required when HTTPS enabled) - Route 53 hosted zone ID for s3u.dev

**TLS-by-Default for Muppets:**

- `enable_muppet_tls_by_default` (bool, default: true) - Enable TLS by default for all new muppets
- `s3u_dev_zone_name` (string, default: "s3u.dev") - Route 53 hosted zone name for s3u.dev domain
- `s3u_dev_zone_id` (string, default: "") - Route 53 hosted zone ID for s3u.dev domain (auto-populated)
- `muppet_wildcard_certificate_arn` (string, default: "") - ARN of wildcard certificate for muppet endpoints (auto-populated)

#### Example Configuration

```hcl
# terraform.tfvars
enable_https = true
domain_name = "muppet-platform.s3u.dev"
parent_zone_id = "/hostedzone/Z01284891NRMNOB6Q86G3"

# TLS-by-Default for Muppets
enable_muppet_tls_by_default = true
s3u_dev_zone_name = "s3u.dev"
```

#### Deployment

To deploy with HTTPS enabled:

```bash
# Set the zone ID environment variable
export TF_VAR_parent_zone_id="/hostedzone/Z01284891NRMNOB6Q86G3"

# Initialize and apply
tofu init
tofu plan
tofu apply
```

## Infrastructure Components

- **ECS Fargate Service** - Platform service container
- **Application Load Balancer** - HTTP/HTTPS traffic routing
- **ACM Certificate** - Automatic TLS certificate management (platform + wildcard for muppets)
- **Route 53 Records** - DNS configuration and certificate validation
- **CloudWatch Logs** - Centralized logging
- **CloudWatch Alarms** - Certificate expiry monitoring
- **Auto Scaling** - Automatic capacity management

## TLS-by-Default Architecture

The platform now includes TLS-by-default infrastructure for all muppets:

- **Wildcard Certificate** - `*.s3u.dev` certificate covers all muppet subdomains
- **Automatic DNS Validation** - Certificate validation handled automatically
- **Certificate Monitoring** - CloudWatch alarms for certificate expiry (30-day warning)
- **Muppet Integration** - Certificate ARN and zone ID available for muppet modules

## Files

- `main.tf` - Primary infrastructure resources
- `variables.tf` - Input variables and validation
- `outputs.tf` - Output values for other systems
- `certificates.tf` - TLS certificates and validation (platform + muppet wildcard)
- `versions.tf` - Provider requirements and versions