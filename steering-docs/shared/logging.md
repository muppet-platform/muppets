# Logging Standards

## Overview

This document defines the logging standards and best practices that all muppets must implement to ensure consistent, secure, and effective logging across the platform. Proper logging is essential for debugging, monitoring, security, and compliance.

## Logging Principles

### Core Logging Principles

**Structured Logging**
- Use JSON format for all log entries
- Include consistent fields across all logs
- Make logs machine-readable and searchable
- Enable automated log analysis and alerting

**Security-First Logging**
- Never log sensitive data (passwords, tokens, PII)
- Mask or hash sensitive information when necessary
- Implement log integrity protection
- Control access to log data

**Performance-Conscious Logging**
- Use appropriate log levels to control verbosity
- Implement asynchronous logging for high-throughput applications
- Consider log volume impact on storage and network
- Use sampling for high-frequency events

**Operational Excellence**
- Include sufficient context for troubleshooting
- Use correlation IDs to trace requests across services
- Implement consistent error logging patterns
- Enable log-based monitoring and alerting

## Log Levels

### Standard Log Levels

**ERROR (40)**
- System errors that require immediate attention
- Unhandled exceptions and critical failures
- Service unavailability or degradation
- Security incidents and authentication failures

**WARN (30)**
- Recoverable errors and degraded functionality
- Configuration issues that don't prevent operation
- Performance issues and resource constraints
- Deprecated feature usage

**INFO (20)**
- Normal application flow and business events
- Service startup and shutdown
- User actions and business transactions
- Configuration changes and deployments

**DEBUG (10)**
- Detailed information for troubleshooting
- Variable values and execution flow
- External service interactions
- Performance timing information

### Log Level Usage Guidelines

**Production Environments**
- Default level: INFO
- Enable DEBUG only for specific troubleshooting
- Monitor log volume and adjust levels as needed
- Use structured configuration for level management

**Development Environments**
- Default level: DEBUG
- Enable verbose logging for all components
- Use console output for immediate feedback
- Test log formatting and content

## Structured Log Format

### Standard Log Entry Structure

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "com.muppetplatform.userservice",
  "message": "User created successfully",
  "request_id": "req_123456789",
  "user_id": "user_456",
  "muppet_name": "user-service",
  "environment": "production",
  "version": "1.2.3",
  "context": {
    "operation": "create_user",
    "duration_ms": 45,
    "status": "success"
  },
  "metadata": {
    "source_file": "UserService.java",
    "line_number": 123,
    "method": "createUser"
  }
}
```

### Required Fields

**Core Fields (Always Present)**
- `timestamp`: ISO 8601 formatted timestamp with milliseconds
- `level`: Log level (ERROR, WARN, INFO, DEBUG)
- `logger`: Logger name (typically class or module name)
- `message`: Human-readable log message
- `muppet_name`: Name of the muppet generating the log
- `environment`: Environment name (production, staging, development)
- `version`: Application version

**Request Context Fields (When Available)**
- `request_id`: Unique identifier for request tracing
- `user_id`: Authenticated user identifier (if applicable)
- `session_id`: Session identifier (if applicable)
- `correlation_id`: Cross-service correlation identifier

**Optional Context Fields**
- `operation`: Name of the operation being performed
- `duration_ms`: Operation duration in milliseconds
- `status`: Operation status (success, failure, partial)
- `error_code`: Application-specific error code
- `stack_trace`: Exception stack trace (for errors only)

## Framework-Specific Implementation

**Java Micronaut Logging**

**Dependencies:**
```gradle
implementation 'ch.qos.logback:logback-classic'
implementation 'net.logstash.logback:logstash-logback-encoder:7.4'
implementation 'io.micronaut:micronaut-tracing'
```

**Logback Configuration (logback.xml):**
```xml
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
            <providers>
                <timestamp/>
                <logLevel/>
                <loggerName/>
                <message/>
                <mdc/>
                <arguments/>
                <stackTrace/>
            </providers>
        </encoder>
    </appender>
    
    <root level="INFO">
        <appender-ref ref="STDOUT"/>
    </root>
</configuration>
```

**Java Logging Example:**
```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

@Singleton
public class UserService {
    private static final Logger logger = LoggerFactory.getLogger(UserService.class);
    
    public User createUser(CreateUserRequest request) {
        // Add context to MDC
        MDC.put("operation", "create_user");
        MDC.put("request_id", request.getRequestId());
        
        try {
            long startTime = System.currentTimeMillis();
            
            logger.info("Creating user with email: {}", maskEmail(request.getEmail()));
            
            User user = userRepository.save(new User(request));
            
            long duration = System.currentTimeMillis() - startTime;
            MDC.put("duration_ms", String.valueOf(duration));
            MDC.put("user_id", user.getId());
            
            logger.info("User created successfully");
            
            return user;
            
        } catch (Exception e) {
            logger.error("Failed to create user", e);
            throw e;
        } finally {
            MDC.clear();
        }
    }
    
    private String maskEmail(String email) {
        // Mask email for logging: john@example.com -> j***@e***.com
        String[] parts = email.split("@");
        String maskedLocal = parts[0].charAt(0) + "***";
        String maskedDomain = parts[1].charAt(0) + "***." + parts[1].split("\\.")[1];
        return maskedLocal + "@" + maskedDomain;
    }
}
```

## Security and Privacy

### Sensitive Data Handling

**Never Log These Items**
- Passwords or password hashes
- Authentication tokens (JWT, API keys, session tokens)
- Credit card numbers or payment information
- Social Security Numbers or national IDs
- Personal health information
- Encryption keys or certificates

**Data Masking Techniques**
```python
# Email masking
"john.doe@example.com" → "j***.d**@e***.com"

# Phone number masking
"+1-555-123-4567" → "+1-***-***-4567"

# Credit card masking
"4111-1111-1111-1111" → "****-****-****-1111"

# Generic PII masking
"John Doe" → "J*** D**"
```

### Log Access Control

**Access Restrictions**
- Implement role-based access to log data
- Use separate credentials for log access
- Audit log access and modifications
- Implement log data retention policies

**Log Integrity**
- Use tamper-evident logging mechanisms
- Implement log signing or hashing
- Store logs in append-only systems
- Monitor for log tampering attempts

## Performance Considerations

### Asynchronous Logging

**High-Throughput Applications**
- Use asynchronous logging to avoid blocking
- Implement log buffering and batching
- Monitor log queue sizes and performance
- Handle log overflow gracefully

**Example Async Logging (Java):**
```xml
<configuration>
    <appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
        <queueSize>1000</queueSize>
        <discardingThreshold>0</discardingThreshold>
        <includeCallerData>false</includeCallerData>
        <appender-ref ref="STDOUT"/>
    </appender>
    
    <root level="INFO">
        <appender-ref ref="ASYNC"/>
    </root>
</configuration>
```

### Log Sampling

**High-Frequency Events**
- Implement sampling for very frequent events
- Use rate limiting for repetitive log messages
- Aggregate similar events when appropriate
- Maintain statistical accuracy in samples

**Sampling Example:**
```python
import random
from functools import wraps

def sample_logs(sample_rate=0.1):
    """Decorator to sample log messages"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if random.random() < sample_rate:
                return func(*args, **kwargs)
        return wrapper
    return decorator

@sample_logs(sample_rate=0.01)  # Log 1% of calls
def log_frequent_event(event_data):
    logger.debug("Frequent event occurred", extra=event_data)
```

## Monitoring and Alerting

### Log-Based Monitoring

**Key Metrics to Monitor**
- Error rate by service and endpoint
- Response time percentiles
- Authentication failure rates
- Resource utilization patterns
- Business metric trends

**Alert Conditions**
- Error rate exceeds threshold (>1% for 5 minutes)
- Critical errors occur (any ERROR level log)
- Authentication failures spike (>10 failures/minute)
- Service unavailability detected
- Unusual access patterns identified

### Log Analysis

**Automated Analysis**
- Implement log parsing and indexing
- Create dashboards for key metrics
- Set up automated anomaly detection
- Generate regular log analysis reports

**Tools Integration**
- AWS CloudWatch Logs for log aggregation
- ElasticSearch for log search and analysis
- Grafana for log-based dashboards
- Custom alerting systems for business metrics

## Compliance and Retention

### Log Retention Policies

**Retention Periods by Log Type**
- Security logs: 7 years
- Audit logs: 7 years
- Application logs: 90 days
- Debug logs: 30 days
- Performance logs: 30 days

**Retention Implementation**
- Implement automated log rotation
- Use lifecycle policies for log storage
- Compress older logs to reduce costs
- Securely delete logs after retention period

### Compliance Requirements

**Regulatory Compliance**
- SOX: Financial transaction logging
- GDPR: Personal data processing logs
- HIPAA: Healthcare data access logs
- PCI DSS: Payment processing logs

**Audit Trail Requirements**
- Log all data access and modifications
- Include user identification in all logs
- Maintain log integrity and non-repudiation
- Provide log search and export capabilities

## Testing and Validation

### Log Testing

**Unit Testing**
- Test log message content and format
- Verify log levels are appropriate
- Test log context and metadata
- Validate sensitive data masking

**Integration Testing**
- Test log aggregation and forwarding
- Verify log correlation across services
- Test log-based monitoring and alerting
- Validate log retention and rotation

**Example Log Testing (Python):**
```python
import pytest
import logging
from unittest.mock import patch
import json

def test_user_creation_logging(caplog):
    """Test that user creation logs appropriate information"""
    with caplog.at_level(logging.INFO):
        user_service.create_user({"email": "test@example.com", "name": "Test User"})
    
    # Verify log message exists
    assert "User created successfully" in caplog.text
    
    # Parse and verify log structure
    log_record = caplog.records[0]
    assert log_record.levelname == "INFO"
    assert "operation" in log_record.__dict__
    assert log_record.operation == "create_user"
    
    # Verify sensitive data is masked
    assert "test@example.com" not in caplog.text
    assert "t***@e***.com" in caplog.text
```

## Troubleshooting Guide

### Common Logging Issues

**Missing Context Information**
- Ensure request IDs are propagated across all services
- Include user context in all relevant logs
- Add operation names to all business logic logs
- Include timing information for performance analysis

**Log Volume Issues**
- Adjust log levels in production environments
- Implement log sampling for high-frequency events
- Use asynchronous logging for high-throughput applications
- Monitor log storage costs and optimize retention

**Log Format Inconsistencies**
- Use centralized logging configuration
- Implement logging standards validation
- Create shared logging utilities
- Regular audit of log formats across services

### Performance Troubleshooting

**High Logging Overhead**
- Profile logging performance impact
- Use asynchronous logging appenders
- Optimize log message formatting
- Consider log level filtering at source

**Log Processing Delays**
- Monitor log ingestion pipelines
- Implement log buffering and batching
- Scale log processing infrastructure
- Optimize log parsing and indexing

## Resources and Tools

### Logging Libraries

**Java**
- SLF4J + Logback: Standard Java logging
- Log4j2: High-performance logging framework
- Logstash Logback Encoder: JSON formatting

### Log Management Tools

**Cloud Services**
- AWS CloudWatch Logs
- Google Cloud Logging
- Azure Monitor Logs

**Self-Hosted Solutions**
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Fluentd for log collection
- Grafana Loki for log aggregation

## Updates and Maintenance

This document is maintained by the platform team and updated based on:
- New compliance requirements
- Performance optimization discoveries
- Security best practices evolution
- Framework-specific improvements
- Operational lessons learned

Updates are automatically distributed to all muppets through the steering management system.