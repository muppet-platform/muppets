# TLS Certificates for Muppet Platform
# Creates wildcard certificate for *.s3u.dev to enable TLS-by-default for all muppets

# Data source for existing s3u.dev hosted zone
data "aws_route53_zone" "s3u_dev" {
  name = "s3u.dev"
}

# Wildcard ACM Certificate for all muppet endpoints
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
    Domain = "wildcard.s3u.dev"
  })
}

# DNS validation records for the wildcard certificate
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

# Certificate validation with timeout
resource "aws_acm_certificate_validation" "muppet_wildcard" {
  certificate_arn         = aws_acm_certificate.muppet_wildcard.arn
  validation_record_fqdns = [for record in aws_route53_record.muppet_wildcard_validation : record.fqdn]
  
  timeouts {
    create = "10m"
  }
}

# CloudWatch alarm for certificate expiry monitoring
resource "aws_cloudwatch_metric_alarm" "muppet_certificate_expiry" {
  alarm_name          = "muppet-wildcard-certificate-expiry"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DaysToExpiry"
  namespace           = "AWS/CertificateManager"
  period              = "86400"  # 24 hours
  statistic           = "Average"
  threshold           = "30"     # Alert when less than 30 days to expiry
  alarm_description   = "Muppet wildcard certificate expires in less than 30 days"
  treat_missing_data  = "breaching"

  dimensions = {
    CertificateArn = aws_acm_certificate.muppet_wildcard.arn
  }

  tags = merge(local.common_tags, {
    Name = "muppet-certificate-expiry-alarm"
    Purpose = "certificate-monitoring"
  })
}

# Outputs for the wildcard certificate
output "muppet_wildcard_certificate_arn" {
  description = "ARN of the wildcard certificate for muppet endpoints"
  value       = aws_acm_certificate_validation.muppet_wildcard.certificate_arn
}

output "muppet_wildcard_certificate_status" {
  description = "Status of the muppet wildcard certificate"
  value       = aws_acm_certificate.muppet_wildcard.status
}

output "muppet_wildcard_certificate_domain" {
  description = "Domain covered by the muppet wildcard certificate"
  value       = aws_acm_certificate.muppet_wildcard.domain_name
}

output "s3u_dev_zone_id" {
  description = "Route 53 hosted zone ID for s3u.dev domain"
  value       = data.aws_route53_zone.s3u_dev.zone_id
}

output "s3u_dev_zone_name" {
  description = "Route 53 hosted zone name for s3u.dev domain"
  value       = data.aws_route53_zone.s3u_dev.name
}