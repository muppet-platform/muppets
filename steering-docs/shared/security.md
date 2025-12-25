# Security Guidelines

## Overview

This document defines the security standards and best practices that all muppets must implement to ensure a secure and compliant platform. These guidelines cover authentication, authorization, data protection, and secure coding practices.

## Authentication Standards

### Authentication Methods

**Supported Authentication Types**
- JWT (JSON Web Tokens) - Primary method
- API Keys - For service-to-service communication
- OAuth 2.0 - For third-party integrations
- mTLS - For high-security service communication

**JWT Implementation**
- Use RS256 algorithm (RSA with SHA-256)
- Set appropriate expiration times (15 minutes for access tokens)
- Implement refresh token rotation
- Include minimal claims (user ID, roles, expiration)
- Validate all JWT claims on every request

**Example JWT Claims:**
```json
{
  "sub": "user123",
  "iat": 1642680000,
  "exp": 1642680900,
  "roles": ["user"],
  "iss": "muppet-platform",
  "aud": "muppet-api"
}
```

### Token Management

**Access Tokens**
- Short-lived (15 minutes maximum)
- Store in memory only (never localStorage)
- Include in Authorization header: `Bearer <token>`
- Validate signature and expiration on every request

**Refresh Tokens**
- Longer-lived (7 days maximum)
- Store securely (httpOnly cookies preferred)
- Rotate on every use
- Revoke on logout or suspicious activity

**API Keys**
- Generate cryptographically secure random keys
- Minimum 32 characters length
- Include rate limiting and scope restrictions
- Log all API key usage
- Implement key rotation procedures

## Authorization Standards

### Role-Based Access Control (RBAC)

**Standard Roles**
- `admin`: Full system access
- `user`: Standard user operations
- `service`: Service-to-service operations
- `readonly`: Read-only access

**Permission Structure**
- Use resource:action format (e.g., `users:read`, `orders:create`)
- Implement least privilege principle
- Check permissions at every endpoint
- Log authorization decisions

**Example Authorization Check:**
```python
@require_permission("users:read")
async def get_user(user_id: str, current_user: User):
    # Only execute if user has users:read permission
    return await user_service.get_user(user_id)
```

### Resource-Level Authorization

**Data Ownership**
- Users can only access their own data by default
- Implement ownership checks in data layer
- Use user context in all database queries
- Prevent horizontal privilege escalation

**Multi-Tenant Security**
- Isolate tenant data completely
- Include tenant ID in all queries
- Validate tenant access on every request
- Prevent cross-tenant data leakage

## Input Validation and Sanitization

### Input Validation Rules

**All Input Must Be Validated**
- Validate data type, format, and range
- Use allow-lists rather than deny-lists
- Validate on both client and server side
- Reject invalid input with clear error messages

**Common Validation Patterns**
```python
# Email validation
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Phone number validation
phone_pattern = r'^\+?1?[0-9]{10,15}$'

# Strong password requirements
password_requirements = {
    'min_length': 12,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_numbers': True,
    'require_special_chars': True
}
```

### SQL Injection Prevention

**Use Parameterized Queries**
```python
# GOOD: Parameterized query
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND status = %s",
    (email, status)
)

# BAD: String concatenation
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

**ORM Best Practices**
- Use ORM query builders when possible
- Validate all dynamic query parameters
- Escape special characters in raw queries
- Never trust user input in query construction

### Cross-Site Scripting (XSS) Prevention

**Output Encoding**
- Encode all user-generated content
- Use context-appropriate encoding (HTML, JavaScript, URL)
- Implement Content Security Policy (CSP)
- Sanitize rich text input

**Content Security Policy Example:**
```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'
```

## Data Protection

### Encryption Standards

**Data at Rest**
- Use AES-256 encryption for sensitive data
- Encrypt database columns containing PII
- Use AWS KMS for key management
- Implement key rotation procedures

**Data in Transit**
- Use TLS 1.3 for all communications
- Implement certificate pinning where appropriate
- Use HSTS headers for web applications
- Encrypt internal service communications

**Encryption Implementation Example:**
```python
from cryptography.fernet import Fernet
import os

# Generate or load encryption key
key = os.environ.get('ENCRYPTION_KEY') or Fernet.generate_key()
cipher = Fernet(key)

# Encrypt sensitive data
encrypted_data = cipher.encrypt(sensitive_data.encode())

# Decrypt when needed
decrypted_data = cipher.decrypt(encrypted_data).decode()
```

### Personal Identifiable Information (PII)

**PII Classification**
- **Highly Sensitive**: SSN, credit card numbers, passwords
- **Sensitive**: Email addresses, phone numbers, addresses
- **Internal**: User IDs, session tokens, internal references

**PII Handling Rules**
- Encrypt all PII at rest
- Log PII access and modifications
- Implement data retention policies
- Provide data deletion capabilities
- Mask PII in logs and error messages

**Data Masking Example:**
```python
def mask_email(email: str) -> str:
    """Mask email for logging: john@example.com -> j***@e***.com"""
    local, domain = email.split('@')
    masked_local = local[0] + '*' * (len(local) - 1)
    masked_domain = domain[0] + '*' * (len(domain.split('.')[0]) - 1) + '.' + domain.split('.')[1]
    return f"{masked_local}@{masked_domain}"
```

## Secure Coding Practices

### Error Handling

**Secure Error Messages**
- Never expose internal system details
- Use generic error messages for authentication failures
- Log detailed errors server-side only
- Implement proper error codes for client handling

**Example Error Handling:**
```python
try:
    user = authenticate_user(username, password)
except AuthenticationError as e:
    # Log detailed error server-side
    logger.error(f"Authentication failed for {username}: {e}")
    
    # Return generic error to client
    raise HTTPException(
        status_code=401,
        detail="Invalid credentials"
    )
```

### Logging and Monitoring

**Security Event Logging**
- Log all authentication attempts
- Log authorization failures
- Log data access and modifications
- Log configuration changes
- Monitor for suspicious patterns

**Log Security Requirements**
- Never log passwords or tokens
- Mask PII in log messages
- Use structured logging format
- Implement log integrity protection
- Set appropriate log retention periods

**Secure Logging Example:**
```python
import logging
from datetime import datetime

security_logger = logging.getLogger('security')

def log_authentication_attempt(username: str, success: bool, ip_address: str):
    security_logger.info({
        'event': 'authentication_attempt',
        'username': username,
        'success': success,
        'ip_address': ip_address,
        'timestamp': datetime.utcnow().isoformat(),
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    })
```

## API Security

### Rate Limiting

**Rate Limiting Rules**
- Implement per-user and per-IP rate limiting
- Use sliding window or token bucket algorithms
- Different limits for different endpoint types
- Return appropriate HTTP 429 responses

**Rate Limiting Configuration:**
```python
RATE_LIMITS = {
    'authentication': '5/minute',
    'api_general': '100/minute',
    'api_intensive': '10/minute',
    'password_reset': '3/hour'
}
```

### CORS Configuration

**CORS Best Practices**
- Specify exact allowed origins (avoid wildcards)
- Limit allowed methods to necessary ones
- Set appropriate preflight cache times
- Validate Origin header on server side

**CORS Configuration Example:**
```python
CORS_CONFIG = {
    'allow_origins': ['https://app.muppetplatform.com'],
    'allow_methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'allow_headers': ['Authorization', 'Content-Type'],
    'max_age': 86400  # 24 hours
}
```

### Request Validation

**Request Size Limits**
- Limit request body size (default: 1MB)
- Limit file upload sizes
- Implement timeout limits
- Validate Content-Type headers

**Security Headers**
```python
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

## Dependency Security

### Dependency Management

**Dependency Security Rules**
- Keep all dependencies up to date
- Use dependency scanning tools
- Pin dependency versions in production
- Review security advisories regularly
- Remove unused dependencies

**Vulnerability Scanning**
- Scan dependencies on every build
- Fail builds for high-severity vulnerabilities
- Implement automated dependency updates
- Monitor for new vulnerabilities

**Example Dependency Scanning (Python):**
```bash
# Install security scanning tools
pip install safety bandit

# Scan for known vulnerabilities
safety check

# Scan code for security issues
bandit -r src/
```

### Supply Chain Security

**Package Verification**
- Verify package signatures when available
- Use official package repositories only
- Review package maintainers and history
- Implement package integrity checks

## Infrastructure Security

### Container Security

**Container Best Practices**
- Use minimal base images (Alpine Linux)
- Run containers as non-root users
- Scan images for vulnerabilities
- Keep base images updated
- Use multi-stage builds to reduce attack surface

**Dockerfile Security Example:**
```dockerfile
FROM amazoncorretto:21-alpine

# Create non-root user
RUN addgroup -g 1001 -S muppet && \
    adduser -u 1001 -S muppet -G muppet

# Copy application
COPY --chown=muppet:muppet app.jar /app/app.jar

# Switch to non-root user
USER muppet

# Run application
CMD ["java", "-jar", "/app/app.jar"]
```

### Network Security

**Network Isolation**
- Use VPC with private subnets
- Implement security groups with minimal access
- Use NAT gateways for outbound internet access
- Enable VPC Flow Logs for monitoring

**Service Communication**
- Use TLS for all service-to-service communication
- Implement service mesh for complex architectures
- Use mutual TLS (mTLS) for high-security communications
- Validate service certificates

## Incident Response

### Security Incident Handling

**Incident Classification**
- **Critical**: Data breach, system compromise
- **High**: Authentication bypass, privilege escalation
- **Medium**: Denial of service, information disclosure
- **Low**: Configuration issues, minor vulnerabilities

**Response Procedures**
1. **Immediate Response** (0-1 hour)
   - Contain the incident
   - Assess impact and scope
   - Notify security team
   - Begin evidence collection

2. **Investigation** (1-24 hours)
   - Analyze logs and evidence
   - Determine root cause
   - Assess data impact
   - Document findings

3. **Recovery** (24-72 hours)
   - Implement fixes
   - Restore services
   - Verify security controls
   - Monitor for recurrence

4. **Post-Incident** (1-2 weeks)
   - Conduct lessons learned
   - Update security controls
   - Improve monitoring
   - Update documentation

### Breach Notification

**Notification Requirements**
- Internal notification within 1 hour
- Customer notification within 24 hours (if applicable)
- Regulatory notification as required
- Public disclosure if legally required

## Compliance and Auditing

### Security Auditing

**Regular Security Reviews**
- Quarterly security assessments
- Annual penetration testing
- Code security reviews
- Infrastructure security audits

**Audit Logging**
- Log all security-relevant events
- Implement tamper-evident logging
- Retain logs for compliance periods
- Provide audit trail capabilities

### Compliance Standards

**Applicable Standards**
- SOC 2 Type II compliance
- GDPR data protection requirements
- Industry-specific regulations
- Internal security policies

## Framework-Specific Security

**Java Micronaut Security**

**Security Dependencies:**
```gradle
implementation 'io.micronaut.security:micronaut-security-jwt'
implementation 'io.micronaut.security:micronaut-security-oauth2'
```

**Security Configuration:**
```java
@Singleton
public class SecurityConfig {
    
    @Bean
    public JwtAuthenticationProvider jwtAuthenticationProvider() {
        return new JwtAuthenticationProvider();
    }
    
    @Bean
    public SecurityFilter securityFilter() {
        return SecurityFilter.create()
            .requireAuthentication("/api/**")
            .permitAll("/health", "/metrics");
    }
}
```

## Security Testing

### Security Test Requirements

**Automated Security Testing**
- Static Application Security Testing (SAST)
- Dynamic Application Security Testing (DAST)
- Dependency vulnerability scanning
- Container image scanning

**Manual Security Testing**
- Penetration testing
- Code security reviews
- Architecture security reviews
- Threat modeling exercises

### Security Test Integration

**CI/CD Security Gates**
- Fail builds for critical vulnerabilities
- Require security review for sensitive changes
- Implement security regression testing
- Monitor security metrics over time

## Resources and Training

### Security Resources

**Internal Resources**
- Security team contact information
- Incident response procedures
- Security policy documentation
- Compliance requirements

**External Resources**
- OWASP Top 10 Web Application Security Risks
- NIST Cybersecurity Framework
- Cloud Security Alliance guidelines
- Framework-specific security guides

### Security Training

**Required Training**
- Secure coding practices
- Common vulnerability patterns
- Incident response procedures
- Compliance requirements

**Ongoing Education**
- Security newsletter subscriptions
- Conference attendance
- Security certification programs
- Regular security updates

## Updates and Maintenance

This document is maintained by the platform security team and updated based on:
- Emerging security threats
- New compliance requirements
- Framework security updates
- Incident lessons learned
- Industry best practices evolution

Updates are automatically distributed to all muppets through the steering management system.