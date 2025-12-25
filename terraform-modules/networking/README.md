# Networking Module

This Terraform module creates a complete VPC networking infrastructure for the Muppet Platform, including public and private subnets, NAT gateways, and VPC endpoints for cost optimization.

## Features

- **VPC**: Configurable CIDR block with DNS support
- **Multi-AZ Subnets**: Public and private subnets across multiple availability zones
- **NAT Gateways**: Internet access for private subnets with cost optimization options
- **VPC Endpoints**: Direct access to AWS services without internet routing
- **Security Groups**: Properly configured default security group restrictions
- **Network ACLs**: Optional additional network-level security
- **Cost Optimization**: Single NAT gateway option and VPC endpoints

## Usage

```hcl
module "networking" {
  source = "../terraform-modules/networking"

  name_prefix = "muppet-platform"
  vpc_cidr    = "10.0.0.0/16"
  
  # Subnet configuration
  public_subnet_count  = 2
  private_subnet_count = 2
  
  # NAT Gateway configuration
  enable_nat_gateway   = true
  single_nat_gateway   = false  # Set to true for cost optimization
  
  # VPC Endpoints for cost optimization
  enable_vpc_endpoints = true
  
  # Optional Network ACLs
  enable_network_acls = false
  
  tags = {
    Environment = "production"
    Project     = "muppet-platform"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | ~> 5.0 |

## Providers

| Name | Version |
|------|---------|
| aws | ~> 5.0 |

## Resources

| Name | Type |
|------|------|
| aws_vpc.main | resource |
| aws_internet_gateway.main | resource |
| aws_subnet.public | resource |
| aws_subnet.private | resource |
| aws_nat_gateway.main | resource |
| aws_eip.nat | resource |
| aws_route_table.public | resource |
| aws_route_table.private | resource |
| aws_vpc_endpoint.s3 | resource |
| aws_vpc_endpoint.ecr_dkr | resource |
| aws_vpc_endpoint.ecr_api | resource |
| aws_vpc_endpoint.logs | resource |
| aws_security_group.vpc_endpoints | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name_prefix | Prefix for resource names | `string` | `"muppet-platform"` | no |
| vpc_cidr | CIDR block for VPC | `string` | `"10.0.0.0/16"` | no |
| public_subnet_count | Number of public subnets to create | `number` | `2` | no |
| private_subnet_count | Number of private subnets to create | `number` | `2` | no |
| enable_nat_gateway | Enable NAT Gateway for private subnets | `bool` | `true` | no |
| single_nat_gateway | Use single NAT Gateway for cost optimization | `bool` | `false` | no |
| enable_vpc_endpoints | Enable VPC endpoints for AWS services | `bool` | `true` | no |
| enable_network_acls | Enable custom Network ACLs | `bool` | `false` | no |
| tags | Tags to apply to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | ID of the VPC |
| vpc_cidr_block | CIDR block of the VPC |
| public_subnet_ids | List of IDs of the public subnets |
| private_subnet_ids | List of IDs of the private subnets |
| nat_gateway_ids | List of IDs of the NAT Gateways |
| nat_gateway_public_ips | List of public IPs of the NAT Gateways |
| availability_zones | List of availability zones used |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           VPC (10.0.0.0/16)                    │
│                                                                 │
│  ┌─────────────────┐                    ┌─────────────────┐    │
│  │  Public Subnet  │                    │  Public Subnet  │    │
│  │   10.0.0.0/24   │                    │   10.0.1.0/24   │    │
│  │      AZ-a       │                    │      AZ-b       │    │
│  │                 │                    │                 │    │
│  │  ┌───────────┐  │                    │  ┌───────────┐  │    │
│  │  │    ALB    │  │                    │  │    ALB    │  │    │
│  │  └───────────┘  │                    │  └───────────┘  │    │
│  │  ┌───────────┐  │                    │  ┌───────────┐  │    │
│  │  │NAT Gateway│  │                    │  │NAT Gateway│  │    │
│  │  └───────────┘  │                    │  └───────────┘  │    │
│  └─────────────────┘                    └─────────────────┘    │
│           │                                       │             │
│           │              Internet Gateway         │             │
│           └─────────────────┬─────────────────────┘             │
│                             │                                   │
│  ┌─────────────────┐                    ┌─────────────────┐    │
│  │ Private Subnet  │                    │ Private Subnet  │    │
│  │  10.0.2.0/24    │                    │  10.0.3.0/24    │    │
│  │      AZ-a       │                    │      AZ-b       │    │
│  │                 │                    │                 │    │
│  │  ┌───────────┐  │                    │  ┌───────────┐  │    │
│  │  │ECS Tasks  │  │                    │  │ECS Tasks  │  │    │
│  │  └───────────┘  │                    │  └───────────┘  │    │
│  │  ┌───────────┐  │                    │  ┌───────────┐  │    │
│  │  │VPC Endpoints│ │                    │  │VPC Endpoints│ │    │
│  │  └───────────┘  │                    │  └───────────┘  │    │
│  └─────────────────┘                    └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Subnet Allocation

The module automatically calculates subnet CIDR blocks:

- **Public Subnets**: `10.0.0.0/24`, `10.0.1.0/24`, etc.
- **Private Subnets**: `10.0.2.0/24`, `10.0.3.0/24`, etc.

Each subnet is placed in a different availability zone for high availability.

## Cost Optimization Features

### Single NAT Gateway

Set `single_nat_gateway = true` to use one NAT Gateway for all private subnets:

```hcl
module "networking" {
  source = "../terraform-modules/networking"
  
  single_nat_gateway = true  # Reduces NAT Gateway costs
  
  # ... other configuration
}
```

**Trade-offs:**
- **Cost**: ~$45/month savings per NAT Gateway
- **Availability**: Single point of failure for internet access
- **Recommendation**: Use for development/staging environments

### VPC Endpoints

VPC endpoints eliminate NAT Gateway data transfer costs for AWS services:

```hcl
module "networking" {
  source = "../terraform-modules/networking"
  
  enable_vpc_endpoints = true  # Reduces data transfer costs
  
  # ... other configuration
}
```

**Included Endpoints:**
- **S3**: Gateway endpoint (no cost)
- **ECR**: Interface endpoints for Docker image pulls
- **CloudWatch Logs**: Interface endpoint for log shipping

**Cost Savings:**
- Eliminates NAT Gateway data transfer charges for AWS services
- Interface endpoints: ~$7.20/month per endpoint
- Typically breaks even with moderate AWS service usage

## Security Features

### Default Security Group

The module restricts the default security group to prevent accidental usage:

```hcl
# Default security group blocks all traffic
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id
  # No ingress or egress rules
}
```

### Network ACLs (Optional)

Enable additional network-level security:

```hcl
module "networking" {
  source = "../terraform-modules/networking"
  
  enable_network_acls = true
  
  # ... other configuration
}
```

**Public Subnet NACLs:**
- Allow HTTP (80) and HTTPS (443) inbound
- Allow ephemeral ports (1024-65535) for return traffic
- Allow all outbound traffic

**Private Subnet NACLs:**
- Allow all traffic from VPC CIDR
- Allow ephemeral ports for return traffic
- Allow all outbound traffic

## Examples

### Development Environment (Cost Optimized)

```hcl
module "dev_networking" {
  source = "../terraform-modules/networking"

  name_prefix = "muppet-dev"
  vpc_cidr    = "10.1.0.0/16"
  
  # Minimal subnets for development
  public_subnet_count  = 1
  private_subnet_count = 1
  
  # Cost optimization
  single_nat_gateway   = true
  enable_vpc_endpoints = false  # Skip VPC endpoints for dev
  
  tags = {
    Environment = "development"
    Project     = "muppet-platform"
  }
}
```

### Production Environment (High Availability)

```hcl
module "prod_networking" {
  source = "../terraform-modules/networking"

  name_prefix = "muppet-prod"
  vpc_cidr    = "10.0.0.0/16"
  
  # Multi-AZ for high availability
  public_subnet_count  = 3
  private_subnet_count = 3
  
  # High availability configuration
  enable_nat_gateway   = true
  single_nat_gateway   = false  # NAT Gateway per AZ
  
  # Cost optimization with VPC endpoints
  enable_vpc_endpoints = true
  
  # Additional security
  enable_network_acls = true
  
  tags = {
    Environment = "production"
    Project     = "muppet-platform"
    Team        = "platform"
  }
}
```

### Integration with Other Modules

```hcl
module "networking" {
  source = "../terraform-modules/networking"
  # ... networking configuration
}

module "muppet_service" {
  source = "../terraform-modules/fargate-service"

  service_name = "my-muppet"
  
  # Use networking module outputs
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids
  
  # ... other configuration
}
```

## Best Practices

1. **Subnet Planning**: Ensure sufficient IP addresses for future growth
2. **Availability Zones**: Use at least 2 AZs for high availability
3. **Cost Optimization**: Use single NAT Gateway for non-production environments
4. **VPC Endpoints**: Enable for production to reduce data transfer costs
5. **Security**: Never use the default security group for applications
6. **Tagging**: Consistent tagging for cost allocation and management