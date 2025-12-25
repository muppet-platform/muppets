# HTTP Response Standards

## Overview

This document defines the standard HTTP response patterns, status codes, and error handling formats that all muppets must follow to ensure consistency across the platform.

## HTTP Status Codes

### Success Responses (2xx)

**200 OK**
- Use for successful GET requests that return data
- Use for successful PUT/PATCH requests that update resources
- Include response body with requested data or confirmation

**201 Created**
- Use for successful POST requests that create new resources
- Include `Location` header with URL of created resource
- Include response body with created resource data

**202 Accepted**
- Use for asynchronous operations that have been accepted but not completed
- Include response body with operation status and tracking information

**204 No Content**
- Use for successful DELETE requests
- Use for successful PUT/PATCH requests when no response body is needed
- Must not include response body

### Client Error Responses (4xx)

**400 Bad Request**
- Use for malformed requests, invalid JSON, or missing required fields
- Include detailed error message explaining what was invalid

**401 Unauthorized**
- Use when authentication is required but not provided or invalid
- Include `WWW-Authenticate` header when applicable

**403 Forbidden**
- Use when user is authenticated but lacks permission for the requested resource
- Include clear message about insufficient permissions

**404 Not Found**
- Use when requested resource does not exist
- Include helpful message suggesting valid alternatives when possible

**409 Conflict**
- Use when request conflicts with current resource state
- Common for duplicate creation attempts or version conflicts

**422 Unprocessable Entity**
- Use for requests with valid syntax but semantic errors
- Include detailed validation error messages

**429 Too Many Requests**
- Use when rate limiting is applied
- Include `Retry-After` header with retry timing

### Server Error Responses (5xx)

**500 Internal Server Error**
- Use for unexpected server errors
- Log detailed error information but return generic message to client

**502 Bad Gateway**
- Use when upstream service is unavailable or returns invalid response

**503 Service Unavailable**
- Use during maintenance or when service is temporarily overloaded
- Include `Retry-After` header when possible

## Response Body Format

### Success Response Format

```json
{
  "data": {
    // Actual response data
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "v1",
    "request_id": "req_123456789"
  }
}
```

### Error Response Format

All error responses must follow this standardized format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "email",
        "message": "Email address is required"
      },
      {
        "field": "age",
        "message": "Age must be between 18 and 120"
      }
    ]
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "v1",
    "request_id": "req_123456789"
  }
}
```

### Pagination Response Format

For paginated responses, use this format:

```json
{
  "data": [
    // Array of items
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_items": 100,
    "has_next": true,
    "has_previous": false
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "v1",
    "request_id": "req_123456789"
  }
}
```

## Error Code Standards

### Standard Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_REQUIRED`: Authentication is required
- `AUTHORIZATION_FAILED`: User lacks required permissions
- `RESOURCE_NOT_FOUND`: Requested resource does not exist
- `RESOURCE_CONFLICT`: Request conflicts with existing resource
- `RATE_LIMIT_EXCEEDED`: Too many requests from client
- `INTERNAL_ERROR`: Unexpected server error
- `SERVICE_UNAVAILABLE`: Service is temporarily unavailable
- `UPSTREAM_ERROR`: External service error

### Custom Error Codes

Muppets may define custom error codes following these patterns:
- Use UPPER_SNAKE_CASE format
- Prefix with muppet-specific identifier when needed
- Keep codes descriptive and consistent

Examples:
- `USER_PROFILE_INCOMPLETE`
- `PAYMENT_PROCESSING_FAILED`
- `INVENTORY_INSUFFICIENT`

## Headers

### Required Headers

**All Responses:**
- `Content-Type`: Specify response content type (usually `application/json`)
- `X-Request-ID`: Echo back the request ID for tracing

**Error Responses:**
- `X-Error-Code`: Include the error code for programmatic handling

**Caching:**
- `Cache-Control`: Specify caching behavior
- `ETag`: Include entity tag for conditional requests when appropriate

### Security Headers

Include these security headers in all responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

## Content Negotiation

### Supported Media Types

**Request Accept Headers:**
- `application/json` (primary)
- `application/xml` (if specifically required)
- `text/plain` (for simple responses)

**Response Content-Type:**
- Always specify correct `Content-Type` header
- Default to `application/json; charset=utf-8`

## API Versioning

### Version Header

Include API version in responses:
```
X-API-Version: v1
```

### Version in Response Body

Include version in meta section:
```json
{
  "meta": {
    "version": "v1"
  }
}
```

## Logging Integration

### Request/Response Logging

Log all HTTP requests and responses with:
- Request ID for correlation
- HTTP method and path
- Response status code
- Response time
- User ID (if authenticated)

### Error Logging

For error responses, log:
- Full error details (server-side only)
- Stack trace (for 5xx errors)
- Request context
- User information

## Examples

### Successful Resource Creation

```http
POST /api/v1/users
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com"
}
```

Response:
```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/v1/users/123
X-Request-ID: req_123456789

{
  "data": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "v1",
    "request_id": "req_123456789"
  }
}
```

### Validation Error

```http
POST /api/v1/users
Content-Type: application/json

{
  "name": "",
  "email": "invalid-email"
}
```

Response:
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
X-Request-ID: req_123456789
X-Error-Code: VALIDATION_ERROR

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "name",
        "message": "Name is required and cannot be empty"
      },
      {
        "field": "email",
        "message": "Email address format is invalid"
      }
    ]
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "v1",
    "request_id": "req_123456789"
  }
}
```

### Resource Not Found

```http
GET /api/v1/users/999
```

Response:
```http
HTTP/1.1 404 Not Found
Content-Type: application/json
X-Request-ID: req_123456789
X-Error-Code: RESOURCE_NOT_FOUND

{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID 999 was not found",
    "details": []
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "v1",
    "request_id": "req_123456789"
  }
}
```

## Implementation Guidelines

### Framework-Specific Implementation

**Java Micronaut:**
- Use `@Error` annotation for global exception handling
- Implement custom `ErrorResponseProcessor`
- Use `HttpResponse.status()` for proper status codes

### Testing Requirements

- Test all error scenarios with proper status codes
- Validate response body format matches standards
- Test header presence and values
- Verify logging integration works correctly

## Compliance

All muppets must implement these HTTP response standards. Non-compliance will be flagged during:
- Code reviews
- Automated testing
- Platform health checks
- API documentation generation

## Updates

This document is maintained by the platform team. Updates will be distributed automatically to all muppets through the steering management system.