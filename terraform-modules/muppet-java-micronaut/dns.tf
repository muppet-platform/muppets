# DNS Record Management for Muppet TLS Endpoints
# Creates Route 53 DNS records for custom muppet domains

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

output "http_endpoint" {
  description = "HTTP endpoint URL (load balancer direct)"
  value       = "http://${module.fargate_service.load_balancer_dns_name}"
}

output "certificate_arn_used" {
  description = "Certificate ARN used for TLS (if enabled)"
  value       = var.enable_https ? var.certificate_arn : null
}