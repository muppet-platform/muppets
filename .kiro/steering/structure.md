---
inclusion: always
---

# Project Structure & Organization

## Repository Layout
```
muppet-platform/
├── platform/                  # Core platform service (FastAPI)
├── templates/                  # Muppet template development
├── terraform-modules/         # Shared infrastructure modules
├── steering-docs/             # Centralized steering documentation
└── docs/                      # Project documentation
```

## Platform Service Structure
```
platform/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Pydantic settings
│   ├── models.py               # Data models
│   ├── integrations/           # AWS, GitHub clients
│   └── routers/               # API endpoints
├── tests/                     # Unit and integration tests
├── mcp/                       # MCP server implementation
└── terraform/                 # Platform infrastructure
```

## Code Organization
- **FastAPI**: Routers for endpoints, Pydantic models, dependency injection
- **Configuration**: Environment variables with Pydantic validation
- **Error Handling**: Custom exceptions with structured responses
- **Logging**: JSON format with request context

## Naming Conventions
- **Python**: snake_case files
- **Config**: kebab-case YAML
- **Docs**: kebab-case Markdown
- **Tests**: `test_<module>.py` pattern with moto for AWS mocking