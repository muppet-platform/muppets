---
inclusion: always
---

# Testing with Mocks and Dependency Injection

## Core Principle
**Tests must never depend on external services.** Mock all network calls, databases, and third-party APIs for fast, reliable, deterministic tests.

## Mandatory Patterns

### 1. Dependency Injection
```python
# ✅ Testable
class ServiceClass:
    def __init__(self, github_client=None, aws_client=None):
        self.github_client = github_client or GitHubClient()
        self.aws_client = aws_client or AWSClient()

# ❌ Untestable
class ServiceClass:
    def __init__(self):
        self.github_client = GitHubClient()  # Hard-coded
```

### 2. Mock External Services
Always mock: GitHub API, AWS services, databases, HTTP requests, file system operations

### 3. Complete Mock Data
```python
@pytest.fixture
def mock_service():
    mock = AsyncMock()
    mock.method.return_value = {
        "success": True,
        "data": {...},
        "timestamp": "2025-01-01T00:00:00Z"
    }
    return mock
```

### 4. Property-Based Tests
```python
@given(test_data())
def test_property(data):
    mock_service = AsyncMock()  # Must mock dependencies
    tool = ServiceClass(external_service=mock_service)
    # Test logic
```

## Enforcement
- All services MUST accept dependencies as constructor parameters
- All tests MUST mock external service calls
- Mock responses MUST match real implementation structure exactly
- Tests making real network calls will be rejected
    return mock
```

### 4. Property-Based Tests Require Extra Care

Property-based tests generate many test cases. Unmocked dependencies cause exponential failures:

```python
@given(test_data())
def test_property(data):
    async def async_test():
        # MUST mock all dependencies
        mock_service = AsyncMock()
        tool = ServiceClass(external_service=mock_service)
        # ... test logic
```

## Response Format Validation

### Mock Data Must Match Implementation

```python
# If implementation returns:
{
    "muppet": {
        "name": "test",
        "metrics": {"cpu": 0.5}
    }
}

# Mock must return identical structure:
mock.method.return_value = {
    "muppet": {
        "name": "test", 
        "metrics": {"cpu": 0.5}  # Don't forget any fields
    }
}
```

### Timestamp Format Consistency

```python
# Use consistent timestamp formats
"created_at": "2025-01-01T00:00:00Z"  # For JSON serialization
"created_at": "2025-01-01T00:00:00"   # For datetime.fromisoformat()
```

## Test Architecture Patterns

### Service Layer Testing

```python
class TestServiceClass:
    @pytest.fixture
    def mock_dependencies(self):
        return {
            'github_client': AsyncMock(),
            'aws_client': AsyncMock(),
            'state_manager': AsyncMock()
        }
    
    @pytest.fixture
    def service(self, mock_dependencies):
        return ServiceClass(**mock_dependencies)
    
    async def test_method(self, service, mock_dependencies):
        # Configure mocks
        mock_dependencies['github_client'].create_repo.return_value = {...}
        
        # Test
        result = await service.create_something()
        
        # Assert
        assert result["success"] is True
```

### Integration Testing with Mocks

Even integration tests should mock external services:

```python
def test_api_endpoint(client, mock_lifecycle_service):
    # Mock the service layer
    mock_lifecycle_service.list_all.return_value = {...}
    
    # Test the endpoint
    response = client.get("/api/v1/items")
    assert response.status_code == 200
```

## Common Anti-Patterns to Avoid

### ❌ Real API Calls in Tests
```python
def test_create_repo():
    client = GitHubClient()  # Will make real API calls
    result = client.create_repository("test-repo")  # Fails with 403
```

### ❌ Hard-Coded Service Instantiation
```python
class ToolRegistry:
    def __init__(self):
        self.service = ExternalService()  # Can't be mocked
```

### ❌ Incomplete Mock Data
```python
# Test expects 'metrics' field but mock doesn't provide it
mock.get_status.return_value = {"name": "test"}  # Missing fields
```

### ❌ Inconsistent Timestamp Formats
```python
# Mock returns 'Z' suffix but code expects without
mock_data = {"created_at": "2025-01-01T00:00:00Z"}
datetime.fromisoformat(data["created_at"])  # Fails
```

## Enforcement Rules

1. **All new services MUST accept dependencies as constructor parameters**
2. **All tests MUST mock external service calls**
3. **Property-based tests MUST use dependency injection**
4. **Mock responses MUST match real implementation structure exactly**
5. **Tests that make real network calls will be rejected in code review**

## Benefits of Proper Mocking

- **Fast**: Tests complete in seconds, not minutes
- **Reliable**: No flaky failures due to network issues
- **Deterministic**: Same results every time
- **Isolated**: Tests don't affect each other
- **Debuggable**: Failures indicate actual code issues

## Validation

Before merging code, verify:
- [ ] All external services are mocked
- [ ] Tests run without network access
- [ ] Mock responses match real service responses
- [ ] Property-based tests use dependency injection
- [ ] Integration tests mock external dependencies

**Remember: If you can't easily write a fast, reliable test for your code, your code architecture needs improvement.**