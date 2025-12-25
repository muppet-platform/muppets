# Project Structure & Organization

## Repository Layout

```
muppet-platform/
├── platform/                  # Core platform service
├── templates/                  # Muppet template development
├── terraform-modules/         # Shared infrastructure modules
├── steering-docs/             # Centralized steering documentation
└── docs/                      # Project documentation
```

## Component Isolation

Each major component is organized as a separate directory with its own:
- `README.md` - Component-specific documentation
- `config.yaml` - Component configuration
- `.github/workflows/` - Component-specific CI/CD
- `tests/` - Component test suites

## Platform Service Structure

```
platform/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Pydantic settings
│   ├── exceptions.py           # Custom exception classes
│   ├── logging_config.py       # Structured logging setup
│   ├── models.py               # Pydantic data models
│   ├── state_manager.py        # Muppet state management
│   ├── integrations/           # External service integrations
│   │   ├── aws.py             # AWS service clients
│   │   └── github.py          # GitHub API client
│   └── routers/               # FastAPI route handlers
│       ├── health.py          # Health check endpoints
│       └── muppets.py         # Muppet management endpoints
├── tests/                     # Unit and integration tests
├── mcp/                       # MCP server implementation
├── terraform/                 # Platform infrastructure
├── docker/                    # Platform containerization
└── requirements.txt           # Python dependencies
```

## Code Organization Patterns

### FastAPI Structure
- **Routers**: Separate files for logical endpoint groupings
- **Models**: Pydantic models for request/response validation
- **Dependencies**: Shared dependencies and dependency injection
- **Middleware**: CORS and error handling middleware

### Configuration Pattern
- **Hierarchical Settings**: Component configs inherit from global settings
- **Environment Variables**: All config via env vars with defaults
- **Validation**: Pydantic validators for configuration validation

### Error Handling
- **Custom Exceptions**: PlatformException base class with error types
- **Global Handlers**: Centralized exception handling in main.py
- **Structured Responses**: Consistent error response format

### Logging Pattern
- **Structured Logging**: JSON format for all log output
- **Logger Factory**: get_logger() function for consistent logger creation
- **Context**: Include request context in all log messages

## File Naming Conventions

- **Python Files**: snake_case (e.g., `state_manager.py`)
- **Config Files**: kebab-case YAML (e.g., `muppet-platform.yaml`)
- **Documentation**: kebab-case Markdown (e.g., `aws-setup.md`)
- **Directories**: kebab-case for multi-word names

## Import Organization

Follow isort configuration:
1. Standard library imports
2. Third-party imports
3. Local application imports (relative imports with `.`)

## Testing Structure

- **Unit Tests**: `test_<module>.py` pattern
- **Integration Tests**: Separate directory or `integration_` prefix
- **Fixtures**: Shared fixtures in `conftest.py`
- **Mocking**: Use moto for AWS service mocking