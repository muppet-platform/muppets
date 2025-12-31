---
inclusion: always
---

# Python Development Standards

## Requirements
- **Python 3.11+** for platform development
- **UV** for dependency management and virtual environments
- **pyproject.toml** for project configuration

## Setup
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
uv init my-project && cd my-project
uv add fastapi uvicorn pydantic
uv add --dev pytest black isort mypy
```

## Code Quality
- **Black**: Code formatting (88 char line length)
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing with moto for AWS mocking

## Platform Standards
- Use Pydantic v2 for validation
- Implement async/await patterns
- Use structured logging (python-json-logger)
- Pin exact versions in production