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

#### Example Configuration

```hcl
# terraform.tfvars
enable_https = true
domain_name = "muppet-platform.s3u.dev"
parent_zone_id = "/hostedzone/Z01284891NRMNOB6Q86G3"
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
- **ACM Certificate** - Automatic TLS certificate management
- **Route 53 Records** - DNS configuration
- **CloudWatch Logs** - Centralized logging
- **Auto Scaling** - Automatic capacity management

## Files

- `main.tf` - Primary infrastructure resources
- `variables.tf` - Input variables and validation
- `outputs.tf` - Output values for other systems
- `versions.tf` - Provider requirements and versions